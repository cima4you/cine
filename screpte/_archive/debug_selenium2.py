from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)
# Remove webdriver property to avoid detection
driver.execute_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

try:
    driver.get('https://www.imdb.com/title/tt1375666/')
    time.sleep(5)
    print('Page title:', driver.title)
    print('Current URL:', driver.current_url)
    
    if 'challenge' in driver.current_url or 'captcha' in driver.current_url or driver.title == '403 Forbidden':
        print('BLOCKED')
    else:
        scripts = driver.find_elements('tag name', 'script')
        for s in scripts:
            html = s.get_attribute('innerHTML') or ''
            if 'ratingValue' in html:
                m = re.search(r'"ratingValue":\s*([\d.]+)', html)
                if m:
                    print('Rating:', m.group(1))
                break
        else:
            print('No ratingValue found')
            
        # Try specific rating element
        try:
            el = driver.find_element('css selector', '[data-testid="hero-rating-bar__aggregate-rating__score"]')
            print('Found rating element:', el.text)
        except:
            print('No rating element found')
finally:
    driver.quit()
