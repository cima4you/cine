import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find serverList and serverLabel in HTML
for term in ['id="serverList"', 'id="serverLabel"', 'id="seasonSelector"', 'id="episodeSelector"']:
    idx = content.find(term)
    if idx >= 0:
        print(f"Found {term}")
        print(content[max(0,idx-200):idx+200])
        print("---")

# Find <style> section
idx = content.find('<style')
if idx >= 0:
    end = content.find('</style>', idx)
    style = content[idx:end+8]
    # Look for relevant styles
    for word in ['server', 'season', 'episode', 'hidden', 'display']:
        if word in style.lower():
            # Print lines containing the word
            for line in style.split('\n'):
                if word in line.lower():
                    print(f"CSS: {line.strip()}")
