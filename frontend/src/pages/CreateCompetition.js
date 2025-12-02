import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CreateCompetition() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [players, setPlayers] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState([]);
  const [form, setForm] = useState({
    name: "",
    budget: 100000, // £100k default budget
    squadSize: 2, // Players per participant
    numParticipants: 2, // Expected number of participants
  });

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      alert("Please sign in first");
      navigate("/");
    }
    loadPlayers();
  }, [navigate]);

  const loadPlayers = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/players`);
      setPlayers(response.data);
    } catch (e) {
      console.error("Error loading players:", e);
    }
  };

  const togglePlayer = (playerId) => {
    setSelectedPlayers((prev) =>
      prev.includes(playerId)
        ? prev.filter((id) => id !== playerId)
        : [...prev, playerId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      alert("Please sign in first");
      return;
    }

    const playersNeeded = form.numParticipants * form.squadSize;
    if (selectedPlayers.length !== playersNeeded) {
      alert(`Please select exactly ${playersNeeded} players (${form.numParticipants} participants × ${form.squadSize} squad size)`);
      return;
    }

    try {
      const response = await axios.post(`${BACKEND_URL}/darts/competitions`, {
        ...form,
        commissionerId: user.id,
        selectedPlayers: selectedPlayers,
      });
      alert("Competition created successfully!");
      navigate(`/competition/${response.data.id}`);
    } catch (e) {
      console.error("Error creating competition:", e);
      alert(e.response?.data?.detail || "Error creating competition");
    }
  };

  const selectTopPlayers = () => {
    const playersNeeded = form.numParticipants * form.squadSize;
    const topPlayers = players
      .sort((a, b) => a.seed - b.seed)
      .slice(0, playersNeeded)
      .map((p) => p.id);
    setSelectedPlayers(topPlayers);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
          <button
            onClick={() => navigate("/")}
            className="text-green-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <h1 className="text-3xl font-bold mb-6 text-gray-900">Create New Competition</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Competition Name</label>
              <input
                type="text"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                placeholder="e.g., Work Mates Darts 2025"
                data-testid="competition-name-input"
              />
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-gray-700 mb-2 font-semibold">
                  Number of Participants
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={form.numParticipants}
                  onChange={(e) => setForm({ ...form, numParticipants: Number(e.target.value) })}
                  min="2"
                  max="8"
                  required
                  data-testid="competition-num-participants-input"
                />
                <p className="text-sm text-gray-500 mt-1">How many people will play</p>
              </div>

              <div>
                <label className="block text-gray-700 mb-2 font-semibold">
                  Squad Size
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={form.squadSize}
                  onChange={(e) => setForm({ ...form, squadSize: Number(e.target.value) })}
                  min="1"
                  max="16"
                  required
                  data-testid="competition-squad-size-input"
                />
                <p className="text-sm text-gray-500 mt-1">Players per participant</p>
              </div>

              <div>
                <label className="block text-gray-700 mb-2 font-semibold">
                  Budget per Participant (£)
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  value={form.budget}
                  onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })}
                  min="10000"
                  required
                  data-testid="competition-budget-input"
                />
                <p className="text-sm text-gray-500 mt-1">Default: £100,000</p>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-gray-700 font-semibold">
                  Select Players for Competition
                </label>
                <button
                  type="button"
                  onClick={selectTopPlayers}
                  className="text-green-600 hover:text-green-700 font-semibold text-sm"
                >
                  Quick Select: Top {form.numParticipants * form.squadSize} Seeds
                </button>
              </div>
              <div className="text-sm text-gray-600 mb-3">
                Selected: {selectedPlayers.length} / {form.numParticipants * form.squadSize}
                <span className="ml-2 text-gray-500">
                  ({form.numParticipants} participants × {form.squadSize} squad size)
                </span>
              </div>

              <div className="border rounded-lg p-4 max-h-96 overflow-y-auto bg-gray-50">
                <div className="grid md:grid-cols-2 gap-2">
                  {players
                    .sort((a, b) => a.seed - b.seed)
                    .map((player) => (
                      <label
                        key={player.id}
                        className={`flex items-center p-3 rounded cursor-pointer transition-colors ${
                          selectedPlayers.includes(player.id)
                            ? "bg-green-100 border-green-500 border-2"
                            : "bg-white border border-gray-300 hover:bg-gray-100"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedPlayers.includes(player.id)}
                          onChange={() => togglePlayer(player.id)}
                          className="mr-3"
                        />
                        <div className="flex-1">
                          <div className="font-semibold text-gray-900">
                            {player.seed}. {player.name}
                          </div>
                          <div className="text-sm text-gray-600">{player.country}</div>
                        </div>
                      </label>
                    ))}
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-semibold text-lg disabled:bg-gray-400 disabled:cursor-not-allowed"
              disabled={selectedPlayers.length !== form.numParticipants * form.squadSize}
              data-testid="create-competition-submit"
            >
              {selectedPlayers.length === form.numParticipants * form.squadSize
                ? "Create Competition"
                : `Select ${(form.numParticipants * form.squadSize) - selectedPlayers.length} more players`}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
