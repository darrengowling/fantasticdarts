import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PlayersList() {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("all");

  useEffect(() => {
    loadPlayers();
  }, []);

  const loadPlayers = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/darts/players`);
      setPlayers(response.data);
    } catch (e) {
      console.error("Error loading players:", e);
    } finally {
      setLoading(false);
    }
  };

  const countries = [...new Set(players.map((player) => player.country))].sort();

  const filteredPlayers = players.filter((player) => {
    const matchesSearch = player.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCountry = selectedCountry === "all" || player.country === selectedCountry;
    return matchesSearch && matchesCountry;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading players...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 py-8">
      <div className="container mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <button
            onClick={() => navigate("/")}
            className="text-green-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <h1 className="text-3xl font-bold mb-6 text-gray-900">
            PDC World Championship 2025/26
          </h1>
          <p className="text-gray-600 mb-6">
            Top 32 seeded players eligible for fantasy selection
          </p>

          {/* Filters */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Search</label>
              <input
                type="text"
                placeholder="Search players..."
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="player-search-input"
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Country</label>
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                value={selectedCountry}
                onChange={(e) => setSelectedCountry(e.target.value)}
                data-testid="player-country-filter"
              >
                <option value="all">All Countries</option>
                {countries.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Players Grid */}
          <div className="text-gray-600 mb-4">
            Showing {filteredPlayers.length} of {players.length} players
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPlayers.map((player) => (
              <div
                key={player.id}
                className="border rounded-lg p-6 hover:shadow-lg transition-shadow bg-white"
                data-testid={`player-card-${player.id}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{player.name}</h3>
                  <span className="text-3xl">{getCountryFlag(player.country)}</span>
                </div>
                <div className="text-gray-600 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-sm">Seed:</span>
                    <span className="font-semibold">#{player.seed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Country:</span>
                    <span>{player.country}</span>
                  </div>
                  {player.nickname && (
                    <div className="text-sm text-gray-500 italic mt-2">
                      "{player.nickname}"
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {filteredPlayers.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No players found matching your criteria
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getCountryFlag(country) {
  const flags = {
    England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    Wales: "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Northern Ireland": "🇬🇧",
    Netherlands: "🇳🇱",
    Belgium: "🇧🇪",
    Germany: "🇩🇪",
    Austria: "🇦🇹",
    Australia: "🇦🇺",
    "New Zealand": "🇳🇿",
    USA: "🇺🇸",
    Canada: "🇨🇦",
    Japan: "🇯🇵",
    China: "🇨🇳",
    Ireland: "🇮🇪",
    Poland: "🇵🇱",
    Denmark: "🇩🇰",
    Sweden: "🇸🇪",
    Switzerland: "🇨🇭",
    Spain: "🇪🇸",
    France: "🇫🇷",
    Italy: "🇮🇹",
    Portugal: "🇵🇹",
    Brazil: "🇧🇷",
    "South Africa": "🇿🇦"
  };
  return flags[country] || "🎯";
}
