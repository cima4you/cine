const fs = require('fs');

// Read the raw text
let raw = fs.readFileSync('scripts/tuktukhd/data/32.txt', 'utf-8');

// Fix missing commas between array elements: when '}' is followed by whitespace then '{'
// This is a common JSON generation error
raw = raw.replace(/\}\s*\n\s*\{/g, '},\n    {');

// Fix the first line if it was affected (should start with [)
raw = raw.replace(/^\[\s*,/, '[');

let data;
try {
  data = JSON.parse(raw);
  console.log('Successfully parsed ' + data.length + ' entries from 32.txt');
} catch (e) {
  console.error('JSON parse error:', e.message);
  // Try to find the position
  const pos = parseInt(e.message.match(/position (\d+)/)?.[1] || '0');
  console.error('Error at position:', pos);
  console.error('Context:', raw.substring(Math.max(0, pos - 50), pos + 50));
  process.exit(1);
}

// Extract existing titles from data-foreign-series.js
const existingJs = fs.readFileSync('split/data-foreign-series.js', 'utf-8');
const titleRegex = /"title":\s*"([^"]+)"/g;
let match;
const existingTitles = new Set();
while ((match = titleRegex.exec(existingJs)) !== null) {
  existingTitles.add(match[1]);
}
console.log('Existing entries: ' + existingTitles.size);

// Filter out existing entries and transform
let newCount = 0;
let skipCount = 0;

// Helper function to transform episode servers
function transformEpisode(ep) {
  const newEp = {
    episodeNumber: ep.episodeNumber,
    title: ep.title,
    duration: ''
  };
  if (ep.servers && ep.servers.watch) {
    newEp.servers = ep.servers.watch.map(s => ({
      name: s.name || '⭐  TukTuk Vip',
      url: s.url,
      isDefault: s.isDefault || false
    }));
  } else {
    newEp.servers = [];
  }
  if (ep.servers && ep.servers.download) {
    newEp.downloadServers = ep.servers.download.map(s => ({
      name: s.name || 'TukTuk Download',
      url: s.url
    }));
  } else {
    newEp.downloadServers = [];
  }
  return newEp;
}

// Helper to group episodes by season
function groupEpisodesBySeason(episodes, seasons) {
  if (!episodes || episodes.length === 0) return [];
  
  // Build a map of season numbers from the seasons array
  const seasonNames = {};
  if (seasons) {
    seasons.forEach(s => {
      seasonNames[s.seasonNumber] = s.name || ('الموسم ' + s.seasonNumber);
    });
  }
  
  // Group episodes by seasonNumber
  const seasonMap = {};
  episodes.forEach(ep => {
    const sn = ep.seasonNumber || 1;
    if (!seasonMap[sn]) {
      seasonMap[sn] = {
        seasonNumber: sn,
        episodes: []
      };
    }
    seasonMap[sn].episodes.push(transformEpisode(ep));
  });
  
  // Return sorted by season number
  return Object.keys(seasonMap).sort((a, b) => a - b).map(key => seasonMap[key]);
}

const newEntries = [];

data.forEach(item => {
  // Skip if already exists (case-insensitive comparison)
  if (existingTitles.has(item.title)) {
    skipCount++;
    return;
  }
  
  const newEntry = {
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
  
  newEntries.push(newEntry);
  newCount++;
});

console.log('Skipped (already exist): ' + skipCount);
console.log('New entries to add: ' + newCount);

// Generate the JS code for new entries
function entryToJS(entry, index) {
  const json = JSON.stringify(entry, null, 2);
  // Fix the object to not have quotes on property names (JS style)
  // Actually JSON.stringify produces valid JS object literal too
  return json;
}

let output = '\n';
newEntries.forEach((entry, i) => {
  const jsonStr = JSON.stringify(entry, null, 2);
  if (i > 0) {
    output += ',\n';
  }
  output += jsonStr;
});

// Insert new entries before the closing ] of the array (last line)
const lastBracketPos = existingJs.lastIndexOf('\n]');
if (lastBracketPos === -1) {
  console.error('Could not find closing ]');
  process.exit(1);
}

const newJs = existingJs.substring(0, lastBracketPos) + ',' + output + '\n]';

fs.writeFileSync('split/data-foreign-series.js', newJs, 'utf-8');
console.log('Successfully wrote ' + newCount + ' new entries to split/data-foreign-series.js');

// Also update the header comment
const headerComment = '// مسلسلات أجنبية من tuktukhd — ' + (existingTitles.size + newCount) + ' مسلسل\n// تم التوليد: ' + new Date().toISOString().replace('T', ' ').substring(0, 19) + '\n';
const finalJs = newJs.replace(/\/\/ مسلسلات أجنبية من tuktukhd.*\n\/\/ تم التوليد.*\n/, headerComment);
fs.writeFileSync('split/data-foreign-series.js', finalJs, 'utf-8');
console.log('Updated header comment');
