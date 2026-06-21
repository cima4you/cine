import sys, json
sys.path.insert(0, 'scripts/tuktukhd')
from scrape_foreign_series import episode_servers

# Test on an episode page
sv = episode_servers('https://tuktukhd.com/%D9%85%D8%B3%D9%84%D8%B3%D9%84-from-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%B1%D8%A7%D8%A8%D8%B9-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1/')
with open('scripts/tuktukhd/debug_servers.json', 'w', encoding='utf-8') as f:
    json.dump(sv, f, ensure_ascii=False, indent=2)
print('Servers found:', len(sv.get('watch', [])))
print('Downloads found:', len(sv.get('download', [])))
print('Done')
