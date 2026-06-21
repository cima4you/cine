import sys, json
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])

series = [m for m in data if m.get('contentType') == 'series']
# Check seasons structure
s = series[0]
if 'seasons' in s:
    print('Seasons type:', type(s['seasons']))
    print('Seasons:', json.dumps(s['seasons'], ensure_ascii=False, indent=2)[:2000])
else:
    print('No seasons field')
    print('Keys:', list(s.keys()))
