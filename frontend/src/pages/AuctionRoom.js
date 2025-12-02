import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import io from "socket.io-client";
import { useAuctionClock } from "../hooks/useAuctionClock";
import PlayerCard from "../components/PlayerCard";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || "http://localhost:8001";

let socket = null;

export default function AuctionRoom() {
  const { auctionId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [auction, setAuction] = useState(null);
  const [players, setPlayers] = useState([]);
  const [currentPlayer, setCurrentPlayer] = useState(null);
  const [bids, setBids] = useState([]);
  const [bidAmount, setBidAmount] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedPlayerForLot, setSelectedPlayerForLot] = useState(null);
  const [competition, setCompetition] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [currentLotId, setCurrentLotId] = useState(null);

  // Use the new auction clock hook
  const { remainingMs } = useAuctionClock(socket, currentLotId);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      alert("Please sign in first");
      navigate("/");
      return;
    }

    loadAuction();
    // loadPlayers(); // TODO: Implement players endpoint
    const cleanupSocket = initializeSocket();

    return () => {
      if (socket) {
        // Leave the auction room
        socket.emit("leave_auction", { auctionId });
        
        // Clean up all listeners
        if (cleanupSocket) {
          cleanupSocket();
        }
        
        // Disconnect socket
        socket.disconnect();
        socket = null;
      }
    };
  }, [auctionId]);

  const initializeSocket = () => {
    // Disconnect any existing socket first
    if (socket) {
      console.log("Disconnecting existing socket");
      socket.disconnect();
      socket = null;
    }
    
    const socketURL = "http://localhost:8001";
    console.log("Initializing socket with URL:", socketURL);
    socket = io(socketURL, {
      path: "/socket.io",
      transports: ["polling", "websocket"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });
    console.log("Socket object created:", socket);
    
    // Define handlers as named functions for proper cleanup
    const handleConnectError = (error) => {
      console.error("Socket.IO connection error:", error);
    };

    const handleConnect = () => {
      console.log("Socket connected, joining auction:", auctionId);
      socket.emit("join_auction", { auctionId, userId: user?.id });
      console.log("Emitted join_auction event");
    };

    const handleJoined = (data) => {
      console.log("Joined auction:", data);
    };

    const handleAuctionState = (data) => {
      console.log("Received auction state:", data);
      // Update state with current auction data
      if (data.currentPlayer) {
        setCurrentPlayer(data.currentPlayer);
      }
      if (data.auction) {
        setAuction(data.auction);
        if (data.auction.currentLotId) {
          setCurrentLotId(data.auction.currentLotId);
        }
      }
    };

    const handleSyncState = (data) => {
      console.log("Received sync state:", data);
      // Update state with current auction data (timer handled by useAuctionClock)
      if (data.currentPlayer) {
        setCurrentPlayer(data.currentPlayer);
      }
      if (data.currentBids) {
        setBids(data.currentBids);
      }
      if (data.participants) {
        setParticipants(data.participants);
      }
      // Extract lot ID from auction data for the clock hook
      if (data.auction && data.auction.currentLotId) {
        setCurrentLotId(data.auction.currentLotId);
      }
    };

    const handleBidPlaced = (data) => {
      console.log("Bid placed event received:", data);
      console.log("Current bids before update:", bids);
      console.log("Current player:", currentPlayer);
      setBids((prev) => {
        const newBids = [data.bid, ...prev];
        console.log("New bids after update:", newBids);
        return newBids;
      });
      loadAuction();
      loadPlayers(); // Reload players to update status
    };

    const handleLotStarted = (data) => {
      console.log("Lot started:", data);
      
      if (data.isUnsoldRetry) {
        alert(`🔄 Re-offering unsold player: ${data.player.name}!`);
      }
      
      setCurrentPlayer(data.player);
      if (data.timer && data.timer.lotId) {
        setCurrentLotId(data.timer.lotId);
      }
    };

    const handleSold = (data) => {
      console.log("Lot sold:", data);
      
      if (data.unsold) {
        alert(`❌ Player went unsold! "${data.playerId}" will be offered again later.`);
      } else {
        const winnerName = data.winningBid ? data.winningBid.userName : "Unknown";
        const amount = data.winningBid ? `£${data.winningBid.amount.toLocaleString()}` : "";
        alert(`✅ Player sold to ${winnerName} for ${amount}!`);
      }
      
      setCurrentPlayer(null);
      setBidAmount("");
      if (data.participants) {
        setParticipants(data.participants);
      }
      loadAuction();
      loadPlayers(); // Reload players to update status
    };

    const handleAntiSnipe = (data) => {
      console.log("Anti-snipe triggered:", data);
      alert(`🔥 Anti-snipe! Timer extended!`);
    };

    const handleAuctionComplete = (data) => {
      console.log("Auction complete:", data);
      alert(data.message || "Auction complete! All players have been auctioned.");
    };

    const handleAuctionPaused = (data) => {
      console.log("Auction paused:", data);
      alert(`⏸️ ${data.message}`);
      loadAuction(); // Reload to show paused state
    };

    const handleAuctionResumed = (data) => {
      console.log("Auction resumed:", data);
      alert(`▶️ ${data.message}`);
      loadAuction(); // Reload to show resumed state
    };

    const handleAuctionWaiting = (data) => {
      console.log("Auction waiting:", data);
      loadAuction(); // Reload to show waiting state
    };

    const handleBiddingStarted = (data) => {
      console.log("Bidding started:", data);
      alert(`🚀 ${data.message}`);
      loadAuction(); // Reload to show active state
    };

    const handleDisconnect = () => {
      console.log("Socket disconnected");
    };

    // Remove existing listeners before adding new ones (prevent duplicates)
    socket.off("connect_error", handleConnectError);
    socket.off("connect", handleConnect);
    socket.off("joined", handleJoined);
    socket.off("auction_state", handleAuctionState);
    socket.off("sync_state", handleSyncState);
    socket.off("new_bid", handleBidPlaced);
    socket.off("lot_started", handleLotStarted);
    socket.off("sold", handleSold);
    socket.off("anti_snipe", handleAntiSnipe);
    socket.off("auction_complete", handleAuctionComplete);
    socket.off("auction_paused", handleAuctionPaused);
    socket.off("auction_resumed", handleAuctionResumed);
    socket.off("auction_waiting", handleAuctionWaiting);
    socket.off("bidding_started", handleBiddingStarted);
    socket.off("disconnect", handleDisconnect);

    // Add listeners
    socket.on("connect_error", handleConnectError);
    socket.on("connect", handleConnect);
    socket.on("joined", handleJoined);
    socket.on("auction_state", handleAuctionState);
    socket.on("sync_state", handleSyncState);
    socket.on("new_bid", handleBidPlaced);
    socket.on("lot_started", handleLotStarted);
    socket.on("sold", handleSold);
    socket.on("anti_snipe", handleAntiSnipe);
    socket.on("auction_complete", handleAuctionComplete);
    socket.on("auction_paused", handleAuctionPaused);
    socket.on("auction_resumed", handleAuctionResumed);
    socket.on("auction_waiting", handleAuctionWaiting);
    socket.on("bidding_started", handleBiddingStarted);
    socket.on("disconnect", handleDisconnect);

    // Store cleanup function
    return () => {
      socket.off("connect_error", handleConnectError);
      socket.off("connect", handleConnect);
      socket.off("joined", handleJoined);
      socket.off("sync_state", handleSyncState);
      socket.off("bid_placed", handleBidPlaced);
      socket.off("lot_started", handleLotStarted);
      socket.off("sold", handleSold);
      socket.off("anti_snipe", handleAntiSnipe);
      socket.off("auction_complete", handleAuctionComplete);
      socket.off("auction_paused", handleAuctionPaused);
      socket.off("auction_resumed", handleAuctionResumed);
      socket.off("auction_waiting", handleAuctionWaiting);
      socket.off("bidding_started", handleBiddingStarted);
      socket.off("disconnect", handleDisconnect);
    };
  };

  const loadAuction = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/auctions/${auctionId}`);
      console.log("Auction data loaded:", response.data);
      
      // Backend returns auction object directly
      const auctionData = response.data;
      setAuction(auctionData);
      
      // Set lot ID for timer hook
      if (auctionData.currentLotId) {
        setCurrentLotId(auctionData.currentLotId);
      }
      
      // Load current player if there is one
      if (auctionData.currentPlayerId) {
        const playerResponse = await axios.get(`${BACKEND_URL}/darts/players/${auctionData.currentPlayerId}`);
        setCurrentPlayer(playerResponse.data);
      }

      // Load competition
      const competitionResponse = await axios.get(`${BACKEND_URL}/darts/competitions/${auctionData.competitionId}`);
      setCompetition(competitionResponse.data);
      setParticipants(competitionResponse.data.participants || []);
      
      // Load bids for current player
      if (auctionData.currentPlayerId) {
        // Bids would need a separate endpoint - for now just use empty array
        setBids([]);
      }
    } catch (e) {
      console.error("Error loading auction:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadPlayers = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/auctions/${auctionId}/players`);
      setPlayers(response.data.players);
      console.log("Loaded players:", response.data);
    } catch (error) {
      console.error("Error loading players:", error);
    }
  };

  const loadParticipants = async () => {
    try {
      if (!auction) return;
      const competitionId = auction.competitionId;
      const response = await axios.get(`${BACKEND_URL}/darts/competitions/${competitionId}/participants`);
      setParticipants(response.data);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const placeBid = async () => {
    if (!user || !currentPlayer || !bidAmount) {
      alert("Please enter a bid amount");
      return;
    }

    const amount = parseFloat(bidAmount);
    if (isNaN(amount) || amount <= 0) {
      alert("Please enter a valid bid amount");
      return;
    }

    // Check user's budget
    const userParticipant = participants.find((p) => p.userId === user.id);
    if (userParticipant && amount > userParticipant.budgetRemaining) {
      alert(`Insufficient budget. You have £${userParticipant.budgetRemaining.toLocaleString()} remaining`);
      return;
    }

    // Check if higher than current highest bid
    const currentBids = bids.filter((b) => b.playerId === currentPlayer.id);
    if (currentBids.length > 0) {
      const highestBid = Math.max(...currentBids.map((b) => b.amount));
      if (amount <= highestBid) {
        alert(`Bid must be higher than current highest bid: £${highestBid.toLocaleString()}`);
        return;
      }
    }

    try {
      await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/bid`, {
        userId: user.id,
        playerId: currentPlayer.id,
        amount,
      });
      setBidAmount("");
    } catch (e) {
      console.error("Error placing bid:", e);
      const errorMessage = e.response?.data?.detail || e.message || "Error placing bid";
      alert(errorMessage);
    }
  };

  const startLot = async (playerId) => {
    try {
      await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/start-lot/${playerId}`);
      setSelectedPlayerForLot(null);
    } catch (e) {
      console.error("Error starting lot:", e);
      alert("Error starting lot");
    }
  };

  const completeLot = async () => {
    try {
      await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/complete-lot`);
    } catch (e) {
      console.error("Error completing lot:", e);
    }
  };

  const pauseAuction = async () => {
    try {
      const result = await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/pause`);
      console.log("Auction paused:", result.data);
    } catch (e) {
      console.error("Error pausing auction:", e);
      alert("Error pausing auction: " + (e.response?.data?.detail || e.message));
    }
  };

  const resumeAuction = async () => {
    try {
      const result = await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/resume`);
      console.log("Auction resumed:", result.data);
    } catch (e) {
      console.error("Error resuming auction:", e);
      alert("Error resuming auction: " + (e.response?.data?.detail || e.message));
    }
  };

  const deleteAuction = async () => {
    if (!window.confirm(
      `Are you sure you want to delete this auction? This will:\n` +
      `• Remove all auction data and bids\n` +
      `• Reset all participant budgets\n` +
      `• Return the competition to ready state\n\n` +
      `This action cannot be undone.`
    )) {
      return;
    }

    try {
      const result = await axios.delete(`${BACKEND_URL}/darts/auctions/${auctionId}`);
      console.log("Auction deleted:", result.data);
      alert("Auction deleted successfully!");
      navigate("/"); // Go back to homepage
    } catch (e) {
      console.error("Error deleting auction:", e);
      alert("Error deleting auction: " + (e.response?.data?.detail || e.message));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-darts-bg-900 via-darts-bg-800 to-darts-dark-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading auction...</div>
      </div>
    );
  }

  const isCommissioner = competition && user && competition.commissionerId === user.id;
  const currentPlayerBids = currentPlayer ? bids.filter((b) => b.playerId === currentPlayer.id) : [];
  
  // Debug logging for bid display
  if (currentPlayer) {
    console.log("Current player ID:", currentPlayer.id);
    console.log("All bids:", bids);
    console.log("Current player bids:", currentPlayerBids);
  }
  const highestBid = currentPlayerBids.length > 0 ? Math.max(...currentPlayerBids.map((b) => b.amount)) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-darts-bg-900 via-darts-bg-800 to-darts-dark-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => navigate("/")}
            className="text-white hover:text-darts-gold-500 transition-colors mb-4 flex items-center gap-2 font-semibold"
          >
            ← Back to Home
          </button>

          {/* Auction Header */}
          <div className="bg-gradient-to-r from-darts-dark-800 to-darts-dark-900 rounded-xl shadow-2xl p-6 mb-6 border-2 border-darts-dark-700">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-4xl font-bold text-white uppercase tracking-tight">
                  {competition ? competition.name : "Auction Room"}
                </h1>
                <p className="text-gray-300 font-semibold mt-2">
                  Lot #{auction?.currentLot || 0} • Status: <span className="text-darts-gold-500">{auction?.status || "Unknown"}</span>
                  {auction?.status === "paused" && (
                    <span className="ml-2 px-3 py-1 bg-darts-gold-500 text-darts-dark-900 text-sm rounded-full font-bold">PAUSED</span>
                  )}
                  {auction?.status === "waiting" && (
                    <span className="ml-2 px-3 py-1 bg-darts-green-500 text-white text-sm rounded-full font-bold">WAITING</span>
                  )}
                  {auction?.status === "active" && (
                    <span className="ml-2 px-3 py-1 bg-darts-red-500 text-white text-sm rounded-full font-bold animate-pulse">LIVE</span>
                  )}
                </p>
              </div>
              
              {/* Commissioner Controls */}
              {isCommissioner && (
                <div className="flex gap-2">
                  {auction?.status === "active" && (
                    <button
                      onClick={pauseAuction}
                      className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                      title="Pause Auction"
                    >
                      ⏸️ Pause
                    </button>
                  )}
                  
                  {auction?.status === "paused" && (
                    <button
                      onClick={resumeAuction}
                      className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                      title="Resume Auction"
                    >
                      ▶️ Resume
                    </button>
                  )}
                  
                  <button
                    onClick={completeLot}
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    title="Complete Current Lot"
                  >
                    Complete Lot
                  </button>
                  
                  <button
                    onClick={deleteAuction}
                    className="px-4 py-2 bg-red-700 text-white rounded hover:bg-red-800"
                    title="Delete Entire Auction"
                  >
                    🗑️ Delete Auction
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Participant Budgets */}
          <div className="bg-gradient-to-r from-darts-dark-800 to-darts-dark-900 rounded-xl shadow-2xl p-6 mb-6 border-2 border-darts-dark-700">
            <h2 className="text-2xl font-bold mb-4 text-white uppercase tracking-wide">Manager Budgets</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {participants.map((p) => {
                const isCurrentUser = user && p.userId === user.id;
                const budgetPercent = (p.budgetRemaining / 100000) * 100;
                
                return (
                  <div
                    key={p.userId}
                    className={`p-5 rounded-xl border-2 transform transition-all duration-200 ${
                      isCurrentUser
                        ? "bg-gradient-to-br from-darts-gold-600 to-darts-gold-700 border-darts-gold-500 shadow-xl scale-105"
                        : "bg-darts-bg-800 border-darts-dark-700 hover:border-darts-dark-600"
                    }`}
                  >
                    <div className={`font-bold text-sm mb-2 ${isCurrentUser ? 'text-white' : 'text-gray-300'}`}>
                      {p.userName} {isCurrentUser && "⭐"}
                    </div>
                    <div className={`text-3xl font-bold ${isCurrentUser ? 'text-white' : 'text-darts-green-500'}`}>
                      £{p.budgetRemaining.toLocaleString()}
                    </div>
                    
                    {/* Budget progress bar */}
                    <div className="mt-3 mb-2">
                      <div className="h-2 bg-darts-dark-900 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-500 ${
                            budgetPercent > 50 ? 'bg-darts-green-500' : 
                            budgetPercent > 25 ? 'bg-darts-gold-500' : 
                            'bg-darts-red-500'
                          }`}
                          style={{ width: `${budgetPercent}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className={`text-xs mt-2 ${isCurrentUser ? 'text-white/90' : 'text-gray-400'}`}>
                      Spent: £{p.totalSpent.toLocaleString()}
                    </div>
                    <div className={`text-xs ${isCurrentUser ? 'text-white/90' : 'text-gray-400'}`}>
                      Players: {p.playersWon.length}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Current Lot */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
              {currentPlayer ? (
                <div>
                  <h2 className="text-2xl font-bold mb-4 text-gray-900">Current Lot</h2>
                  
                  {/* Timer with urgency states */}
                  {(() => {
                    const s = Math.ceil((remainingMs ?? 0) / 1000);
                    const mm = String(Math.floor(s / 60)).padStart(2, "0");
                    const ss = String(s % 60).padStart(2, "0");
                    
                    // Determine urgency state
                    let timerClass = 'bg-darts-green-600 border-darts-green-700'; // Calm (20-30s)
                    let animation = '';
                    
                    if (s < 10) {
                      // Urgent: Red with fast pulse
                      timerClass = 'bg-darts-red-600 border-darts-red-700';
                      animation = 'animate-pulse-fast';
                    } else if (s < 20) {
                      // Warning: Gold with slow pulse
                      timerClass = 'bg-darts-gold-500 border-darts-gold-600';
                      animation = 'animate-pulse-slow';
                    }
                    
                    return (
                      <div className={`${timerClass} ${animation} text-white p-8 rounded-xl mb-6 text-center border-4 shadow-2xl transition-all duration-300`}>
                        <div className="text-7xl font-bold tracking-wider" data-testid="auction-timer">
                          {mm}:{ss}
                        </div>
                        <div className="text-lg font-semibold mt-3 uppercase tracking-wide">
                          {s < 10 ? '🔥 FINAL SECONDS!' : s < 20 ? '⚠️ HURRY!' : '⏱️ Time Remaining'}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Player Info Card */}
                  <PlayerCard player={currentPlayer} className="mb-6" />

                  {/* Current Highest Bid */}
                  {highestBid > 0 && (
                    <div className="bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
                      <div className="text-sm text-gray-600">Current Highest Bid</div>
                      <div className="text-3xl font-bold text-green-600">£{highestBid.toLocaleString()}</div>
                      {currentPlayerBids[0] && (
                        <div className="text-sm text-gray-600 mt-1">
                          by {currentPlayerBids[0].userName}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Bid Input */}
                  <div>
                    <div className="flex gap-4 mb-2">
                      <input
                        type="number"
                        placeholder="Enter bid amount"
                        className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                        value={bidAmount}
                        onChange={(e) => setBidAmount(e.target.value)}
                        data-testid="bid-amount-input"
                      />
                      <button
                        onClick={placeBid}
                        className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
                        data-testid="place-bid-button"
                      >
                        Place Bid
                      </button>
                    </div>
                    {participants.find((p) => p.userId === user?.id) && (
                      <p className="text-sm text-gray-600">
                        Your remaining budget: £{participants.find((p) => p.userId === user.id).budgetRemaining.toLocaleString()}
                      </p>
                    )}
                  </div>

                  {/* Bid History for Current Player */}
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Bid History</h4>
                    <div className="max-h-64 overflow-y-auto">
                      {currentPlayerBids.length === 0 ? (
                        <p className="text-gray-500">No bids yet</p>
                      ) : (
                        <div className="space-y-2">
                          {currentPlayerBids
                            .sort((a, b) => b.amount - a.amount)
                            .map((bid) => (
                              <div
                                key={bid.id}
                                className="flex justify-between items-center p-3 bg-gray-50 rounded"
                              >
                                <span className="font-semibold">{bid.userName}</span>
                                <span className="text-green-600 font-bold">£{bid.amount.toLocaleString()}</span>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-gray-700">
                    ⏱️ Lot will auto-complete when timer expires. Next player will load automatically.
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  {auction?.status === "waiting" ? (
                    // Waiting Room - Polished
                    <div className="bg-gradient-to-br from-darts-bg-900 to-darts-bg-800 p-12 rounded-2xl border-2 border-darts-dark-700 shadow-2xl">
                      <div className="text-center">
                        {/* Animated icon */}
                        <div className="text-8xl mb-6 animate-pulse-slow">🎯</div>
                        
                        <h2 className="text-5xl font-bold text-white mb-4 uppercase tracking-tight">
                          Auction Lobby
                        </h2>
                        
                        <p className="text-2xl text-gray-300 mb-8 font-medium">
                          {isCommissioner 
                            ? "Managers are gathering... Start when ready!" 
                            : "Waiting for commissioner to begin the action"}
                          <span className="animate-pulse">...</span>
                        </p>

                        {/* Participants Grid */}
                        <div className="bg-darts-bg-800 rounded-xl p-6 mb-8 border border-darts-dark-700">
                          <div className="text-darts-gold-500 font-bold text-lg uppercase tracking-wide mb-4">
                            Managers Ready ({participants.length})
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            {participants.map((p) => (
                              <div 
                                key={p.userId} 
                                className="flex items-center justify-center gap-2 bg-darts-dark-800 px-4 py-3 rounded-lg border border-darts-green-600"
                              >
                                <span className="text-darts-green-500 text-xl">✓</span>
                                <span className="text-white font-semibold">{p.userName}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Quick Facts */}
                        <div className="grid grid-cols-3 gap-4 mb-8">
                          <div className="bg-darts-dark-800 p-4 rounded-lg border border-darts-dark-700">
                            <div className="text-3xl font-bold text-darts-gold-500">
                              {players.length || 32}
                            </div>
                            <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">
                              Players
                            </div>
                          </div>
                          <div className="bg-darts-dark-800 p-4 rounded-lg border border-darts-dark-700">
                            <div className="text-3xl font-bold text-darts-green-500">
                              £100k
                            </div>
                            <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">
                              Budget
                            </div>
                          </div>
                          <div className="bg-darts-dark-800 p-4 rounded-lg border border-darts-dark-700">
                            <div className="text-3xl font-bold text-darts-red-500">
                              30s
                            </div>
                            <div className="text-xs text-gray-400 uppercase tracking-wide mt-1">
                              Per Lot
                            </div>
                          </div>
                        </div>

                        {/* Begin Button (Commissioner only) */}
                        {isCommissioner && (
                          <button
                            onClick={async () => {
                              try {
                                await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/begin`, {
                                  userId: user.id
                                });
                              } catch (e) {
                                console.error("Error beginning bidding:", e);
                                alert("Error beginning bidding: " + (e.response?.data?.detail || e.message));
                              }
                            }}
                            className="bg-gradient-to-r from-darts-green-600 to-darts-green-700 text-white px-12 py-6 rounded-xl hover:from-darts-green-700 hover:to-darts-green-800 font-bold text-2xl shadow-2xl transform hover:scale-105 transition-all duration-200 uppercase tracking-wide border-2 border-darts-green-500 animate-glow"
                          >
                            🚀 BEGIN THE ACTION
                          </button>
                        )}
                        
                        {/* Participant waiting message */}
                        {!isCommissioner && (
                          <div className="text-gray-400 text-lg italic">
                            The commissioner will start the auction shortly
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    // Other states (completed, loading)
                    <div>
                      <div className="text-6xl mb-4">⏳</div>
                      <h2 className="text-2xl font-bold text-gray-900 mb-4">
                        {auction?.status === "completed" ? "Auction Complete!" : "Loading Next Player..."}
                      </h2>
                      <p className="text-gray-600">
                        {auction?.status === "completed" 
                          ? "All players have been auctioned. Check the standings!" 
                          : "Players auto-load in random order. Next player starting soon..."}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Players Overview */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-gray-900">All Players in Auction</h3>
              
              {/* Summary Stats */}
              <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div className="bg-blue-50 p-2 rounded">
                  <div className="font-semibold text-blue-800">Total</div>
                  <div className="text-blue-600">{players.length}</div>
                </div>
                <div className="bg-green-50 p-2 rounded">
                  <div className="font-semibold text-green-800">Sold</div>
                  <div className="text-green-600">{players.filter(p => p.status === 'sold').length}</div>
                </div>
                <div className="bg-yellow-50 p-2 rounded">
                  <div className="font-semibold text-yellow-800">Current</div>
                  <div className="text-yellow-600">{players.filter(p => p.status === 'current').length}</div>
                </div>
                <div className="bg-gray-50 p-2 rounded">
                  <div className="font-semibold text-gray-800">Remaining</div>
                  <div className="text-gray-600">{players.filter(p => p.status === 'upcoming').length}</div>
                </div>
              </div>

              {/* Player List */}
              <div className="max-h-[500px] overflow-y-auto space-y-1">
                {players.map((player) => {
                  const statusColors = {
                    current: "bg-yellow-100 border-yellow-300 text-yellow-800",
                    upcoming: "bg-blue-50 border-blue-200 text-blue-800",
                    sold: "bg-green-50 border-green-200 text-green-800",
                    unsold: "bg-red-50 border-red-200 text-red-800"
                  };
                  
                  const statusIcons = {
                    current: "🔥",
                    upcoming: "⏳",
                    sold: "✅",
                    unsold: "❌"
                  };
                  
                  return (
                    <div
                      key={player.id}
                      className={`p-2 rounded-lg border text-xs ${statusColors[player.status] || 'bg-gray-50 border-gray-200'}`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold truncate">{player.name}</div>
                          <div className="text-xs opacity-75">{player.country}</div>
                        </div>
                        <div className="ml-2 flex flex-col items-end">
                          <div className="flex items-center gap-1">
                            <span>{statusIcons[player.status]}</span>
                            {/* Hide lot number to keep draw order secret */}
                          </div>
                          {player.status === 'sold' && player.winningBid && (
                            <div className="text-xs font-semibold">
                              £{player.winningBid.toLocaleString()}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {player.status === 'sold' && player.winner && (
                        <div className="text-xs mt-1 opacity-75">
                          Won by {player.winner}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 text-xs text-gray-500 space-y-1 border-t pt-3">
                <p>🔥 Current lot • ⏳ Upcoming • ✅ Sold • ❌ Unsold</p>
                <p>Order is randomized - use for strategy only</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
