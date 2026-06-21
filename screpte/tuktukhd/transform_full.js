const fs = require('fs');

let raw = fs.readFileSync('scripts/tuktukhd/data/foreign_series_full.json', 'utf-8');
const data = JSON.parse(raw);
console.log('File: ' + data.length + ' entries');

// Read existing titles from JSON array (not regex, to avoid counting episode titles)
const existingJs = fs.readFileSync('split/data-foreign-series.js', 'utf-8');
const firstBrace = existingJs.indexOf('{');
const lastBrace = existingJs.lastIndexOf('}');
const existingArr = JSON.parse('[' + existingJs.slice(firstBrace, lastBrace + 1) + ']');
const existingTitles = new Set(existingArr.map(s => s.title));
console.log('Existing entries: ' + existingArr.length);

// Transform and filter
let newCount = 0, skipCount = 0;
const newEntries = [];

data.forEach(item => {
  // Transform tuktukhd format → site format
  function transformEpisode(ep) {
    return {
      episodeNumber: ep.episodeNumber,
      title: ep.title,
      duration: '',
      servers: (ep.servers && ep.servers.watch)
        ? ep.servers.watch.map(s => ({ name: s.name || 'TukTuk Vip', url: s.url, isDefault: s.isDefault || false }))
        : [],
      downloadServers: (ep.servers && ep.servers.download)
        ? ep.servers.download.map(s => ({ name: s.name || 'TukTuk Download', url: s.url }))
        : []
    };
  }

  function groupEpisodesBySeason(episodes, seasons) {
    if (!episodes || episodes.length === 0) return [];
    const seasonNames = {};
    if (seasons) seasons.forEach(s => { seasonNames[s.seasonNumber] = s.name || ('الموسم ' + s.seasonNumber); });
    const seasonMap = {};
    episodes.forEach(ep => {
      const sn = ep.seasonNumber || 1;
      if (!seasonMap[sn]) seasonMap[sn] = { seasonNumber: sn, episodes: [] };
      seasonMap[sn].episodes.push(transformEpisode(ep));
    });
    return Object.keys(seasonMap).sort((a, b) => a - b).map(k => seasonMap[k]);
  }

  const entry = {
    title: item.title,
    year: item.year || '',
    rating: item.rating || '',
    type: 'أجنبي',
    contentType: 'series',
    description: item.description || '',
    cast: item.cast || [],
    poster: item.poster || '',
    categories: item.genres || item.categories || [],
    quality: '',
    isComplete: false,
    seasons: groupEpisodesBySeason(item.episodes, item.seasons)
  };

  if (existingTitles.has(entry.title)) { skipCount++; return; }
  newEntries.push(entry);
  newCount++;
});

console.log('Skipped: ' + skipCount + ', New: ' + newCount);
if (newCount === 0) { console.log('No new entries. File unchanged.'); process.exit(0); }

// Append to file
let output = '\n';
newEntries.forEach((entry, i) => {
  if (i > 0) output += ',\n';
  output += JSON.stringify(entry, null, 2);
});

const lastBracketPos = existingJs.lastIndexOf('\n]');
if (lastBracketPos === -1) { console.error('No closing ]'); process.exit(1); }
// Strip trailing comma before adding new entries
let beforeArray = existingJs.substring(0, lastBracketPos).replace(/,\s*$/, '');
const newJs = beforeArray + ',' + output + '\n]';

const total = existingArr.length + newCount;
const header = '// مسلسلات أجنبية من tuktukhd — ' + total + ' مسلسل\n// تم التوليد: ' + new Date().toISOString().replace('T', ' ').substring(0, 19) + '\n';
const finalJs = newJs.replace(/\/\/ مسلسلات أجنبية من tuktukhd.*\n\/\/ تم التوليد.*\n/, header);

fs.writeFileSync('split/data-foreign-series.js', finalJs, 'utf-8');
console.log('Written! Total: ' + total);
