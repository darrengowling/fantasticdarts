import React from 'react';

/**
 * PlayerCard - PDC-styled player display component
 * Used in auction room to showcase current player up for bidding
 */
export default function PlayerCard({ player, className = '' }) {
  if (!player) return null;

  // Get country flag emoji (basic implementation)
  const getFlagEmoji = (nationality) => {
    const flagMap = {
      'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
      'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
      'Wales': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
      'Netherlands': '🇳🇱',
      'Belgium': '🇧🇪',
      'Germany': '🇩🇪',
      'Austria': '🇦🇹',
      'Australia': '🇦🇺',
      'New Zealand': '🇳🇿',
      'USA': '🇺🇸',
      'Ireland': '🇮🇪',
      'Northern Ireland': '🇬🇧',
      'Spain': '🇪🇸',
      'Poland': '🇵🇱',
      'Czech Republic': '🇨🇿',
      'South Africa': '🇿🇦',
      'Japan': '🇯🇵',
    };
    return flagMap[nationality] || '🎯';
  };

  // Determine seed badge color
  const getSeedBadgeColor = (seed) => {
    if (!seed) return null;
    if (seed <= 8) return 'bg-yellow-500 text-gray-900'; // Top 8
    if (seed <= 16) return 'bg-yellow-600 text-white'; // Top 16
    return 'bg-gray-600 text-white'; // 17-32
  };

  const seedBadgeColor = getSeedBadgeColor(player.seed);

  return (
    <div className={`bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-8 shadow-2xl border-2 border-gray-600 ${className}`}>
      {/* Header with badges */}
      <div className="flex justify-between items-start mb-6">
        {/* Seed badge */}
        {player.seed && (
          <div className={`${seedBadgeColor} px-4 py-2 rounded-full font-bold text-sm shadow-lg`}>
            SEED #{player.seed}
          </div>
        )}
        
        {/* PDC Ranking badge */}
        {player.pdcRanking && (
          <div className="bg-red-600 text-white px-4 py-2 rounded-full font-bold text-sm shadow-lg">
            RANK #{player.pdcRanking}
          </div>
        )}
      </div>

      {/* Player name and nationality */}
      <div className="text-center mb-6">
        <h3 className="text-5xl font-bold text-white mb-3 tracking-tight uppercase">
          {player.name}
        </h3>
        
        <div className="flex items-center justify-center gap-3">
          <span className="text-4xl">{getFlagEmoji(player.nationality)}</span>
          <p className="text-2xl text-gray-300 font-semibold">
            {player.nationality}
          </p>
        </div>
      </div>

      {/* Stats row (if available) */}
      {player.stats && (
        <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-600">
          {player.stats.titles && (
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">
                {player.stats.titles}
              </div>
              <div className="text-xs text-gray-300 uppercase tracking-wide mt-1">
                Titles
              </div>
            </div>
          )}
          
          {player.stats.average && (
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">
                {player.stats.average}
              </div>
              <div className="text-xs text-gray-300 uppercase tracking-wide mt-1">
                Avg
              </div>
            </div>
          )}
          
          {player.stats.highCheckout && (
            <div className="text-center">
              <div className="text-3xl font-bold text-red-400">
                {player.stats.highCheckout}
              </div>
              <div className="text-xs text-gray-300 uppercase tracking-wide mt-1">
                High CO
              </div>
            </div>
          )}
        </div>
      )}

      {/* Profile image placeholder */}
      {player.profileImageUrl ? (
        <div className="mt-6 flex justify-center">
          <img 
            src={player.profileImageUrl} 
            alt={player.name}
            className="w-32 h-32 rounded-full border-4 border-yellow-500 shadow-xl object-cover"
          />
        </div>
      ) : (
        <div className="mt-6 flex justify-center">
          <div className="w-32 h-32 rounded-full border-4 border-gray-600 bg-gray-700 flex items-center justify-center shadow-xl">
            <span className="text-5xl">🎯</span>
          </div>
        </div>
      )}
    </div>
  );
}
