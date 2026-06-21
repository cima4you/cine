import sys
sys.stdout.reconfigure(encoding='utf-8')
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\index.html', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('showMovieModal')
if idx >= 0:
    print(content[idx:idx+3000])
else:
    print("showMovieModal not found")
    # try openModal
    idx = content.find('openModal')
    if idx >= 0:
        print(content[idx:idx+2000])
