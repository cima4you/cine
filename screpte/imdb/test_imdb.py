import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

try:
    r = requests.get('https://www.imdb.com/find?q=Inception+2010', headers=headers, timeout=10)
    print('Status:', r.status_code)
    print('Length:', len(r.text))

    if 'captcha' in r.text.lower():
        print('CAPTCHA BLOCKED')
    elif 'verify' in r.text.lower()[:2000]:
        print('VERIFY CHECK')
    else:
        soup = BeautifulSoup(r.text, 'html.parser')
        section = soup.select_one('[data-testid="find-results-section-title"]')
        if section:
            links = section.select('a.ipc-metadata-list-summary-item__t')
            print('Links found:', len(links))
            for a in links[:3]:
                print(' ', a.text.strip(), '->', a.get('href',''))
        else:
            print('No results section found')
            # Show something useful
            scripts = soup.select('script[type="application/ld+json"]')
            if scripts:
                print('Found ld+json script')
            print('First 1500 chars:')
            print(r.text[:1500])
except Exception as e:
    print('ERROR:', e)
