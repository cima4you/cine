import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    line = f.readline()
print('First 100 chars:', repr(line[:100]))
