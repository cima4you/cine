from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)
try:
    driver.get('https://www.imdb.com/title/tt1375666/')
    time.sleep(5)
    print('Page title:', driver.title)
    print('Current URL:', driver.current_url)
    
    if 'challenge' in driver.current_url or 'captcha' in driver.current_url:
        print('BLOCKED by challenge page!')
    else:
        with open('imdb_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print('Page saved, size:', len(driver.page_source))
        
        scripts = driver.find_elements('tag name', 'script')
        for s in scripts:
            html = s.get_attribute('innerHTML') or ''
            if 'ratingValue' in html:
                print('FOUND ratingValue in script')
                m = re.search(r'"ratingValue":\s*([\d.]+)', html)
                if m:
                    print('Rating:', m.group(1))
                break
        else:
            print('No ratingValue found in any script')
            # Print some script contents to debug
            for s in scripts[:5]:
                html = s.get_attribute('innerHTML') or ''
                if len(html) > 50:
                    print(f'Script: {html[:200]}...')
finally:
    driver.quit()
