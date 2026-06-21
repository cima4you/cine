import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\data\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the full openModal function
idx = content.find('function openModal(item)')
if idx < 0:
    print("openModal not found")
    sys.exit(1)

# Find the end - look for next function
end = content.find('\n        function ', idx + 1)
if end < 0:
    end = idx + 8000

func = content[idx:end]
print("Function length:", len(func))
print()
print(func[:500])
print("...")
print(func[-500:])
