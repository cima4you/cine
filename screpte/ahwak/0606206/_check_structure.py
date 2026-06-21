import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Read completed file
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\data-turkish-completed.js', 'r', encoding='utf-8') as f:
    content = f.read(5000)

# Find first complete object
start = content.find('const')
start = content.find('[', start) + 1
start = content.find('{', start)
if start >= 0:
    brace_count = 0
    for i in range(start, len(content)):
        ch = content[i]
        if ch == '{':
            brace_count += 1
        elif ch == '}':
            brace_count -= 1
            if brace_count == 0:
                obj_str = content[start:i+1]
                try:
                    obj = json.loads(obj_str)
                    print("Keys:", list(obj.keys()))
                    print("Title:", obj.get("title"))
                    # Check for seasons
                    if "seasons" in obj:
                        print("Seasons count:", len(obj["seasons"]))
                        for s in obj["seasons"]:
                            print(f"  Season {s.get('season')}: {len(s.get('episodes', []))} eps")
                    elif "episodes" in obj:
                        print("Flat episodes count:", len(obj["episodes"]))
                        if obj["episodes"]:
                            ep = obj["episodes"][0]
                            print("  First ep keys:", list(ep.keys()) if isinstance(ep, dict) else type(ep))
                            if isinstance(ep, dict) and "servers" in ep:
                                print("  First ep servers:", ep["servers"][:2])
                    # Check downloadServers
                    if "downloadServers" in obj:
                        print("Has downloadServers:", len(obj["downloadServers"]))
                except json.JSONDecodeError as e:
                    print("JSON parse error:", e)
                    print("obj_str[:200]:", obj_str[:200])
                break
