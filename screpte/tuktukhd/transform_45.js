const fs = require('fs');

let raw = fs.readFileSync('scripts/tuktukhd/data/45.txt', 'utf-8');
console.log('45.txt size: ' + (raw.length / 1024 / 1024).toFixed(2) + ' MB');

const commentIdx = raw.indexOf('// مسلسلات أجنبية');
let allEntries = [];

// --- Section 1 ---
let section1 = raw.substring(0, commentIdx).trim();
section1 = section1.replace(/,\s*$/, '');
if (!section1.endsWith(']')) section1 += '\n]';
section1 = section1.replace(/\}\r?\n\s*\{/g, '},\n  {');
try {
  const s1 = JSON.parse(section1);
  console.log('Section 1: ' + s1.length + ' entries');
  allEntries = allEntries.concat(s1);
} catch (e) {
  console.error('Section 1 error: ' + e.message.slice(0, 150));
  process.exit(1);
}

// --- Section 2 ---
const constIdx = raw.indexOf('const cd_foreign_series', commentIdx);
if (constIdx > -1) {
  const section2Start = raw.indexOf('[', constIdx);
  let depth = 0, endIdx = -1;
  for (let i = section2Start; i < raw.length; i++) {
    if (raw[i] === '[') depth++;
    else if (raw[i] === ']') { depth--; if (depth === 0) { endIdx = i; break; } }
  }
  if (endIdx > -1) {
    try {
      const s2 = JSON.parse(raw.substring(section2Start, endIdx + 1));
      console.log('Section 2: ' + s2.length + ' entries');
      allEntries = allEntries.concat(s2);
    } catch (e) {
      console.error('Section 2 error: ' + e.message.slice(0, 150));
      process.exit(1);
    }
  }
}

console.log('Total entries: ' + allEntries.length);

// Read existing titles
const existingJs = fs.readFileSync('split/data-foreign-series.js', 'utf-8');
const titleRegex = /"title":\s*"([^"]+)"/g;
let match;
const existingTitles = new Set();
while ((match = titleRegex.exec(existingJs)) !== null) {
  existingTitles.add(match[1]);
}
console.log('Existing entries: ' + existingTitles.size);

// Filter and normalize
let newCount = 0, skipCount = 0;
const newEntries = [];

allEntries.forEach(item => {
  if (item.episodes) {
    item.episodes.forEach(ep => {
      if (ep.servers && !Array.isArray(ep.servers)) {
        const srv = ep.servers;
        ep.servers = (srv.watch || []).map(s => ({
          name: s.name || 'TukTuk Vip',
          url: s.url,
          isDefault: s.isDefault || false
        }));
        ep.downloadServers = (srv.download || []).map(s => ({
          name: s.name || 'TukTuk Download',
          url: s.url
        }));
      }
      if (!ep.duration) ep.duration = '';
    });
    if (!item.seasons || !item.seasons.length) {
      const seasonMap = {};
      item.episodes.forEach(ep => {
        const sn = ep.seasonNumber || 1;
        if (!seasonMap[sn]) seasonMap[sn] = { seasonNumber: sn, episodes: [] };
        delete ep.seasonNumber;
        seasonMap[sn].episodes.push(ep);
      });
      item.seasons = Object.keys(seasonMap).sort((a,b)=>a-b).map(k=>seasonMap[k]);
      delete item.episodes;
    }
  }
  if (item.genres && !item.categories) item.categories = item.genres;
  delete item.genres;
  if (!item.type) item.type = 'أجنبي';
  if (!item.contentType) item.contentType = 'series';
  item.categories = item.categories || [];
  item.seasons = item.seasons || [];
  item.quality = item.quality || '';
  item.isComplete = item.isComplete || false;
  item.year = item.year || '';
  item.rating = item.rating || '';
  item.description = item.description || '';
  item.cast = item.cast || [];
  item.poster = item.poster || '';

  if (existingTitles.has(item.title)) { skipCount++; return; }
  newEntries.push(item);
  newCount++;
});

console.log('Skipped: ' + skipCount + ', New: ' + newCount);

// Append to file
let output = '\n';
newEntries.forEach((entry, i) => {
  if (i > 0) output += ',\n';
  output += JSON.stringify(entry, null, 2);
});

const lastBracketPos = existingJs.lastIndexOf('\n]');
if (lastBracketPos === -1) { console.error('No closing ]'); process.exit(1); }
const newJs = existingJs.substring(0, lastBracketPos) + ',' + output + '\n]';

const total = existingTitles.size + newCount;
const header = '// مسلسلات أجنبية من tuktukhd — ' + total + ' مسلسل\n// تم التوليد: ' + new Date().toISOString().replace('T', ' ').substring(0, 19) + '\n';
const finalJs = newJs.replace(/\/\/ مسلسلات أجنبية من tuktukhd.*\n\/\/ تم التوليد.*\n/, header);

fs.writeFileSync('split/data-foreign-series.js', finalJs, 'utf-8');
console.log('Written! Total: ' + total);
