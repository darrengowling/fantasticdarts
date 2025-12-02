import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import CreateCompetition from "./pages/CreateCompetition";
import CompetitionDetail from "./pages/CompetitionDetail";
import PlayersList from "./pages/PlayersList";
import AuctionRoom from "./pages/AuctionRoom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Home = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [userForm, setUserForm] = useState({ name: "", email: "" });
  const [competitions, setCompetitions] = useState([]);
  const [inviteToken, setInviteToken] = useState("");

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      loadCompetitions(userData.id);
    }
  }, []);

  const loadCompetitions = async (userId) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/competitions`);
      // Filter to show only competitions where user is a participant
      if (userId) {
        const myCompetitions = response.data.filter(comp => 
          comp.participants.some(p => p.userId === userId)
        );
        setCompetitions(myCompetitions);
      } else {
        setCompetitions(response.data);
      }
    } catch (e) {
      console.error("Error loading competitions:", e);
    }
  };

  const handleUserSubmit = async (e) => {
    e.preventDefault();
    if (!userForm.name || !userForm.email) {
      alert("Please enter both name and email");
      return;
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/users`, userForm);
      setUser(response.data);
      localStorage.setItem("user", JSON.stringify(response.data));
      setShowUserDialog(false);
    } catch (e) {
      console.error("Error creating user:", e);
      alert("Error creating user");
    }
  };

  const handleSignOut = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  const handleJoinWithToken = async () => {
    if (!user) {
      alert("Please sign in first");
      return;
    }

    if (!inviteToken) {
      alert("Please enter an invite token");
      return;
    }

    try {
      // First, find the competition by invite token (case-insensitive)
      const response = await axios.get(`${BACKEND_URL}/darts/competitions`);
      const competition = response.data.find(
        (c) => c.inviteToken.toLowerCase() === inviteToken.toLowerCase()
      );

      if (!competition) {
        alert("Invalid invite token");
        return;
      }

      // Join the competition
      await axios.post(`${BACKEND_URL}/darts/competitions/${competition.id}/join`, {
        userId: user.id,
        inviteToken: inviteToken
      });

      alert("Joined competition successfully!");
      loadCompetitions(user.id); // Reload competitions list
      navigate(`/competition/${competition.id}`);
    } catch (e) {
      console.error("Error joining competition:", e);
      alert(e.response?.data?.detail || "Error joining competition");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900">
      {/* User Dialog */}
      {showUserDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">Enter Your Details</h2>
            <form onSubmit={handleUserSubmit}>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  data-testid="user-name-input"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  data-testid="user-email-input"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
                data-testid="user-submit-button"
              >
                Continue
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-4xl font-bold text-gray-900">
                🎯 Fantastic Darts
              </h1>
              {user ? (
                <div className="flex items-center gap-4">
                  <span className="text-gray-700">Welcome, {user.name}!</span>
                  <button
                    onClick={handleSignOut}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowUserDialog(true)}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
                >
                  Sign In
                </button>
              )}
            </div>
            <p className="text-gray-600 text-lg">
              Fantasy auction for PDC World Darts Championship 2025/26
            </p>
          </div>

          {/* Quick Actions */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <button
              onClick={() => navigate("/create-competition")}
              className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow text-left"
              disabled={!user}
            >
              <div className="text-3xl mb-3">🏆</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Create Competition</h3>
              <p className="text-gray-600">
                Start a new fantasy darts competition
              </p>
              {!user && <p className="text-red-500 text-sm mt-2">Sign in required</p>}
            </button>

            <button
              onClick={() => navigate("/players")}
              className="bg-white p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow text-left"
            >
              <div className="text-3xl mb-3">👤</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Browse Players</h3>
              <p className="text-gray-600">
                View all PDC players available
              </p>
            </button>

            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="text-3xl mb-3">ℹ️</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">How It Works</h3>
              <ul className="text-gray-600 text-sm space-y-1">
                <li>• Create or join a competition</li>
                <li>• Participate in live auction</li>
                <li>• Watch your players compete</li>
                <li>• Win based on performance</li>
              </ul>
            </div>
          </div>

          {/* Join Competition */}
          {user && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                🎫 Join Competition
              </h2>
              <p className="text-gray-600 mb-4">Have an invite token? Enter it below to join:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Enter 8-character token"
                  value={inviteToken}
                  onChange={(e) => setInviteToken(e.target.value)}
                  className="flex-1 px-4 py-3 border rounded-lg font-mono text-lg"
                  maxLength={8}
                />
                <button
                  onClick={handleJoinWithToken}
                  disabled={!inviteToken}
                  className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  Join
                </button>
              </div>
            </div>
          )}

          {/* Competitions List */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">
              My Competitions
            </h2>
            
            {competitions.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <p className="mb-4">No competitions yet</p>
                <button
                  onClick={() => navigate("/create-competition")}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  disabled={!user}
                >
                  Create the First One
                </button>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {competitions.map((competition) => (
                  <div
                    key={competition.id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => navigate(`/competition/${competition.id}`)}
                  >
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      {competition.name}
                    </h3>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div>Commissioner: {competition.commissionerName || 'Unknown'}</div>
                      <div>Budget: £{(competition.budget / 1000).toFixed(0)}k</div>
                      <div>Squad Size: {competition.squadSize} players</div>
                      <div>Status: <span className="font-semibold">{competition.status}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create-competition" element={<CreateCompetition />} />
        <Route path="/competition/:id" element={<CompetitionDetail />} />
        <Route path="/players" element={<PlayersList />} />
        <Route path="/auction/:auctionId" element={<AuctionRoom />} />
      </Routes>
    </BrowserRouter>
  );
}
