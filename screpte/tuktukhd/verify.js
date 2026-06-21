const fs = require('fs');
const js = fs.readFileSync('split/data-foreign-series.js', 'utf-8');
const titleRegex = /"title":\s*"([^"]+)"/g;
let match;
const titles = [];
while ((match = titleRegex.exec(js)) !== null) {
  titles.push(match[1]);
}
console.log('Total entries in file: ' + titles.length);
console.log('First 10 entries:');
titles.slice(0, 10).forEach((t, i) => console.log((i+1) + '. ' + t));
console.log('');
console.log('Last 10 entries:');
titles.slice(-10).forEach((t, i) => console.log(titles.length - 10 + i + 1 + '. ' + t));

// Check for duplicates
const unique = new Set(titles);
if (unique.size !== titles.length) {
  console.log('\nWARNING: Duplicates found!');
  // Find duplicates
  const seen = {};
  titles.forEach((t, i) => {
    if (seen[t] !== undefined) {
      console.log('Duplicate: "' + t + '" at lines ' + (seen[t] + 1) + ' and ' + (i + 1));
    }
    seen[t] = i;
  });
} else {
  console.log('\nNo duplicates - OK');
}

// Check for undefined or empty titles
titles.forEach((t, i) => {
  if (!t || t.trim() === '') {
    console.log('WARNING: Empty title at entry ' + (i + 1));
  }
});
