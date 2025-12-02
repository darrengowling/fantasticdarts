import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CompetitionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [competition, setCompetition] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [inviteToken, setInviteToken] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      alert("Please sign in first");
      navigate("/");
    }
    loadCompetition();
    
    // Auto-refresh every 5 seconds to see new participants
    const interval = setInterval(loadCompetition, 5000);
    return () => clearInterval(interval);
  }, [id, navigate]);

  const loadCompetition = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/competitions/${id}`);
      setCompetition(response.data);
      setParticipants(response.data.participants || []);
      setLoading(false);
    } catch (e) {
      console.error("Error loading competition:", e);
      alert("Competition not found");
      navigate("/");
    }
  };

  const handleJoinWithToken = async () => {
    if (!inviteToken) {
      alert("Please enter an invite token");
      return;
    }

    try {
      await axios.post(`${BACKEND_URL}/darts/competitions/${id}/join`, {
        userId: user.id,
        inviteToken: inviteToken
      });
      alert("Joined competition successfully!");
      loadCompetition();
    } catch (e) {
      console.error("Error joining competition:", e);
      alert(e.response?.data?.detail || "Error joining competition");
    }
  };

  const handleStartAuction = async () => {
    if (competition.commissionerId !== user.id) {
      alert("Only the commissioner can start the auction");
      return;
    }

    if (participants.length < 2) {
      alert("Need at least 2 participants to start auction");
      return;
    }

    try {
      let auctionId;
      
      // Try to get existing auction first
      try {
        const existingAuction = await axios.get(`${BACKEND_URL}/darts/competitions/${competition.id}/auction`);
        auctionId = existingAuction.data.id;
        console.log("Using existing auction:", auctionId);
      } catch (e) {
        // Auction doesn't exist, create it
        if (e.response?.status === 404) {
          const response = await axios.post(`${BACKEND_URL}/darts/competitions/${competition.id}/auction`, {
            competitionId: competition.id,
            bidTimer: 60,
            antiSnipeSeconds: 30
          });
          auctionId = response.data.id;
          console.log("Created new auction:", auctionId);
        } else {
          throw e;
        }
      }
      
      // Start the auction
      await axios.post(`${BACKEND_URL}/darts/auctions/${auctionId}/start`, {
        userId: user.id
      });
      
      navigate(`/auction/${auctionId}`);
    } catch (e) {
      console.error("Error starting auction:", e);
      console.error("Error response:", e.response);
      
      // Handle different error formats
      let errorMsg = "Error starting auction";
      if (e.response?.data?.detail) {
        if (typeof e.response.data.detail === 'string') {
          errorMsg = e.response.data.detail;
        } else if (Array.isArray(e.response.data.detail)) {
          errorMsg = e.response.data.detail.map(err => err.msg).join(', ');
        } else {
          errorMsg = JSON.stringify(e.response.data.detail);
        }
      } else if (e.message) {
        errorMsg = e.message;
      }
      
      alert(errorMsg);
    }
  };

  const copyInviteToken = () => {
    if (competition.inviteToken) {
      navigator.clipboard.writeText(competition.inviteToken);
      alert("Invite token copied to clipboard!");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  const isCommissioner = competition.commissionerId === user?.id;
  const hasJoined = participants.some(p => p.userId === user?.id);

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
            <button
              onClick={() => navigate("/")}
              className="text-green-600 hover:text-green-700 mb-4"
            >
              ← Back to Home
            </button>
            
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {competition.name}
            </h1>
            
            <div className="grid md:grid-cols-3 gap-4 mt-4 text-sm">
              <div>
                <span className="text-gray-600">Budget:</span>
                <span className="font-semibold ml-2">
                  £{(competition.budget / 1000).toFixed(0)}k
                </span>
              </div>
              <div>
                <span className="text-gray-600">Squad Size:</span>
                <span className="font-semibold ml-2">{competition.squadSize}</span>
              </div>
              <div>
                <span className="text-gray-600">Players:</span>
                <span className="font-semibold ml-2">
                  {competition.selectedPlayers?.length || 32}
                </span>
              </div>
            </div>
          </div>

          {/* Invite Section */}
          {isCommissioner && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                📨 Invite Participants
              </h2>
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <p className="text-gray-700 mb-2">Share this invite token:</p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={competition.inviteToken}
                    className="flex-1 px-4 py-3 bg-white border rounded-lg font-mono text-2xl font-bold text-center"
                  />
                  <button
                    onClick={copyInviteToken}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Join Section (for non-commissioners) */}
          {!isCommissioner && !hasJoined && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Join This Competition
              </h2>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Enter invite token"
                  value={inviteToken}
                  onChange={(e) => setInviteToken(e.target.value.toUpperCase())}
                  className="flex-1 px-4 py-2 border rounded-lg"
                  maxLength={8}
                />
                <button
                  onClick={handleJoinWithToken}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
                >
                  Join
                </button>
              </div>
            </div>
          )}

          {/* Participants */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                👥 Participants ({participants.length})
              </h2>
              <button
                onClick={loadCompetition}
                className="text-sm text-green-600 hover:text-green-700 font-semibold"
              >
                🔄 Refresh
              </button>
            </div>
            
            {participants.length === 0 ? (
              <p className="text-gray-500">No participants yet</p>
            ) : (
              <div className="space-y-2">
                {participants.map((participant) => (
                  <div
                    key={participant.userId}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-semibold text-gray-900">
                        {participant.userName}
                        {participant.userId === competition.commissionerId && (
                          <span className="ml-2 text-xs bg-green-600 text-white px-2 py-1 rounded">
                            Commissioner
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600">{participant.userEmail}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Start Auction Button */}
          {isCommissioner && !competition.auctionId && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <button
                onClick={handleStartAuction}
                disabled={participants.length < 2}
                className="w-full bg-green-600 text-white py-4 rounded-lg hover:bg-green-700 font-bold text-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {participants.length < 2
                  ? `Need ${2 - participants.length} more participant(s) to start`
                  : "🎯 Start Auction"}
              </button>
            </div>
          )}

          {/* Auction Started */}
          {competition.auctionId && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <button
                onClick={() => navigate(`/auction/${competition.auctionId}`)}
                className="w-full bg-green-600 text-white py-4 rounded-lg hover:bg-green-700 font-bold text-lg"
              >
                🎯 Go to Auction Room
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
