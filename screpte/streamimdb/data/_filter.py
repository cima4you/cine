import json, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamimdb_movies.json')

with open(path, 'r', encoding='utf-8') as f:
    movies = json.load(f)

with_url = [m for m in movies if m.get('watch_server_url')]
without_url = [m for m in movies if not m.get('watch_server_url')]

# Save movies WITH url back to the main file
with open(path, 'w', encoding='utf-8') as f:
    json.dump(with_url, f, ensure_ascii=False, indent=2)

# Save movies WITHOUT url to a separate file
no_url_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'streamimdb_no_url.json')
with open(no_url_path, 'w', encoding='utf-8') as f:
    json.dump(without_url, f, ensure_ascii=False, indent=2)

print(f'With URL: {len(with_url)} -> streamimdb_movies.json')
print(f'Without URL: {len(without_url)} -> streamimdb_no_url.json')
