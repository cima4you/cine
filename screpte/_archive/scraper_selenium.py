import argparse
import json
import os
import sys
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- Chrome Configuration ----------
def configure_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-3d-apis")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--lang=ar")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

BASE_URL = "https://www.tuktukhd.com"
CATEGORY_HINDI = f"{BASE_URL}/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%89/"
CATEGORY_FOREIGN = f"{BASE_URL}/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A/"
def link_page(page_num, category_url):
    return f"{category_url}?page={page_num}"

# ---------- Scraping des Détails ----------
def extra_info(link, driver):
    try:
        driver.get(link)
        wait = WebDriverWait(driver, 20)

        print(f"🌐 فتح رابط التفاصيل: {link}")
        print(f"📄 عنوان الصفحة: {driver.title}")

        story_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.story')))
        story = story_el.text.strip()

        cats_links = driver.find_elements(By.CSS_SELECTOR, 'div.catssection a')
        catssection = [a.text.strip() for a in cats_links]

        info_dict = {}
        lis = driver.find_elements(By.CSS_SELECTOR, 'ul.RightTaxContent li')
        for li in lis:
            try:
                key = li.find_element(By.TAG_NAME, 'span').text.strip()
                value_parts = [
                    child.text.strip()
                    for child in li.find_elements(By.XPATH, './*')
                    if child.tag_name not in ['i', 'span']
                ]
                info_dict[key] = ' '.join(value_parts).strip()
            except:
                continue

        poster = ''
        try:
            poster_el = driver.find_element(By.CSS_SELECTOR, 'div.Poster--Block img')
            poster = poster_el.get_attribute('data-src') or poster_el.get_attribute('src') or ''
        except:
            pass
        if not poster or 'no.png' in poster:
            try:
                og_image = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                poster = og_image.get_attribute('content') or ''
            except:
                pass

        video_url = ''
        try:
            iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[data-crypt]')
            crypt = iframe.get_attribute('data-crypt')
            if crypt:
                video_url = base64.b64decode(crypt).decode('utf-8')
        except:
            pass
        if not video_url:
            try:
                iframe = driver.find_element(By.CSS_SELECTOR, 'div.player--iframe iframe[src]')
                src = iframe.get_attribute('src') or ''
                if src and 'blob:' not in src:
                    video_url = src
            except:
                pass

        watch_servers = []
        if video_url:
            watch_servers.append({
                'name': 'TukTuk Vip',
                'url': video_url,
                'isDefault': True
            })

        download_servers = []
        for link_el in driver.find_elements(By.CSS_SELECTOR, 'a[data-real-url]'):
            real_url = link_el.get_attribute('data-real-url')
            try:
                name_el = link_el.find_element(By.CSS_SELECTOR, 'div.download--item span')
                name = name_el.text.strip() or 'Download'
            except:
                try:
                    name_el = link_el.find_element(By.CSS_SELECTOR, 'span')
                    name = name_el.text.strip() or 'Download'
                except:
                    name = 'Download'
            if real_url:
                download_servers.append({'name': name, 'url': real_url})
        if not download_servers:
            download_servers.append({'name': 'الرسمي', 'url': link})

        return {
            "poster": poster,
            "video_url": video_url,
            "servers": {
                "watch": watch_servers,
                "download": download_servers
            },
            "info": {
                "story": story,
                "catssection": catssection,
                "details": info_dict
            }
        }
    except Exception as e:
        print(f"❌ خطأ في extra_info(): {e}")
        return {}

# ---------- Sauvegarde Incrementale ----------
def save_one_film(film, filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []
    else:
        existing = []

    if any(f['titre'] == film['titre'] for f in existing):
        print(f"  موجود مسبقاً: {film['titre']}")
        return False

    existing.append(film)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"  ✅ حفظ: {film['titre']}")
    return True

# ---------- Scraper Principal ----------
def scrape_page(page_num, start_from, max_films, detail_driver, filename, category_url):
    driver = configure_driver()
    wait = WebDriverWait(driver, 10)
    count = 0

    try:
        url = link_page(page_num, category_url)
        driver.get(url)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.Block--Item')))
        films = driver.find_elements(By.CSS_SELECTOR, 'div.Block--Item')[start_from-1:start_from-1+max_films]

        for i, film in enumerate(films, start=start_from):
            try:
                a = film.find_element(By.TAG_NAME, 'a')
                title = a.get_attribute("title")
                href = a.get_attribute("href")
                img = a.find_element(By.TAG_NAME, "img")
                img_src = img.get_attribute("data-src") or img.get_attribute("src") or ""

                print(f"🔍 Page {page_num} | Film {i}: {title}")
                detail = extra_info(href, detail_driver)

                if detail:
                    poster = detail.get('poster') or img_src
                    if 'no.png' in poster:
                        poster = img_src
                    entry = {
                        "titre": title,
                        "image": poster,
                        "video_url": detail.get('video_url', ''),
                        "servers": detail['servers'],
                        "info": detail['info']
                    }
                    if save_one_film(entry, filename):
                        count += 1

            except Exception as e:
                print(f"⚠️ خطأ في الفيلم {i} (الصفحة {page_num}) : {e}")
    finally:
        driver.quit()

    return count

# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Scraper de films depuis Tuktukhd")
    parser.add_argument("--start-page", type=int, default=1, help="رقم الصفحة التي تبدأ منها")
    parser.add_argument("--end-page", type=int, default=2, help="آخر صفحة يجب أن يتم استخراج الأفلام منها")
    parser.add_argument("--start-from", type=int, default=1, help="البداية من أي فيلم في الصفحة")
    parser.add_argument("--max-films", type=int, default=30, help="عدد الأفلام التي سيتم معالجتها في كل صفحة")
    parser.add_argument("--output", type=str, default="films.json", help="اسم ملف الخرج بصيغة JSON")
    parser.add_argument("--category", type=str, default="hindi", choices=["hindi", "foreign"], help="نوع الأفلام: hindi أو foreign")
    parser.add_argument("--url", type=str, default="", help="رابط كامل للتصنيف (يلغي --category)")

    args = parser.parse_args()

    if args.url:
        category_url = args.url
    elif args.category == "foreign":
        category_url = CATEGORY_FOREIGN
    else:
        category_url = CATEGORY_HINDI

    output_path = os.path.join(SCRIPT_DIR, args.output)
    total = 0
    detail_driver = configure_driver()

    for page in range(args.start_page, args.end_page + 1):
        total += scrape_page(page, args.start_from, args.max_films, detail_driver, output_path, category_url)

    detail_driver.quit()
    print(f"\nالمجموع: {total} فيلم جديد في {output_path}")

if __name__ == "__main__":
    main()
