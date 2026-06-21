import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import re, time, sys

def main():
    driver = uc.Chrome(headless=True, use_subprocess=False)
    
    driver.get('https://cimafre.site/')
    time.sleep(3)
    print('Homepage loaded')
    
    driver.get('https://cimafre.site/watch.php?vid=19997b01f')
    time.sleep(8)
    print('Watch page loaded')
    
    html = driver.page_source
    print(f'HTML size: {len(html)} bytes')
    
    m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', html, re.DOTALL)
    if m:
        print('\nWatchList FOUND!')
        print(m.group(0))
    else:
        print('\nWatchList NOT FOUND')
        wl_elements = driver.find_elements(By.CSS_SELECTOR, '.WatchList li, ul.WatchList')
        print(f'WatchList DOM elements: {len(wl_elements)}')
        wl_html = driver.execute_script("return document.querySelector('.WatchList') ? document.querySelector('.WatchList').outerHTML : 'null'")
        print(f'WatchList from JS: {wl_html[:500] if wl_html != 'null' else 'null'}')
    
    with open('screpte/cimafre/data/undetected_detail.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Saved!')
    
    driver.quit()

if __name__ == '__main__':
    main()
