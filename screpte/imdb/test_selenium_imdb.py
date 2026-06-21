from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

driver = webdriver.Chrome(options=options)
try:
    driver.get('https://www.imdb.com/title/tt1375666/')
    time.sleep(5)
    print('Title:', driver.title)
    
    # Try to get rating from JSON-LD or the page
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print('Body contains rating value:', 'ratingValue' in body_text)
    
    # Look for specific rating element
    try:
        rating_el = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="hero-rating-bar__aggregate-rating__score"] span')
        print('Rating:', rating_el.text)
    except:
        # Try JSON-LD
        scripts = driver.find_elements(By.TAG_NAME, 'script')
        for script in scripts:
            content = script.get_attribute('innerHTML')
            if content and 'ratingValue' in content:
                import re
                match = re.search(r'"ratingValue":\s*"([\d.]+)"', content)
                if match:
                    print('Rating from JSON-LD:', match.group(1))
                break
        else:
            print('Could not find rating')
            print('Page source snippet:', driver.page_source[:2000])
finally:
    driver.quit()
