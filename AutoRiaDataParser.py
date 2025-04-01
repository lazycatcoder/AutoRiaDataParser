import re
import random
import sqlite3 as sq
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time


user_agents=[
"Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0", 
"Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Safari/605.1.15",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0",
"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0",
"Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.0 Mobile Safari/537.36",
]

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
    }

options=webdriver.ChromeOptions()
options.add_argument(f"user-agent={random.choice(user_agents)}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--ignore-ssl-errors")
options.add_argument("--disable-web-security")

#link to web driver
chromedriver_path = r"D:\chromedriver.exe"
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

DB_PATH = r"D:\AR_data.db"

def create_db():
    """Creating a database."""
    with sq.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY,
                brand TEXT,
                model TEXT,
                year INTEGER,
                new INTEGER,
                color TEXT,
                mileage INTEGER,
                engine_capacity REAL,
                fuel_type TEXT,
                accident TEXT,
                owners_count INTEGER,
                car_number TEXT,
                vin TEXT,
                city TEXT,
                price INTEGER,
                phone_seller TEXT,
                name_seller TEXT,
                url TEXT,
                date TEXT
            )'''
        )

def get_total_pages(soup):
    """Determining the total number of pages in pagination."""
    try:
        last_page_span = soup.find("span", class_="page-item dhide text-c")
        if last_page_span:
            total_pages = int(last_page_span.text.split("/")[-1].strip().replace(" ", ""))
            return total_pages
        return 1
    except Exception as e:
        print(f"Error getting page count: {e}")
        return 1


def scrape_page(url):
    """Collecting links from one page."""
    try:
        driver.get(url)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        title_links = soup.find_all("div", class_="item ticket-title")

        links = [tlink.find("a").get("href").strip() for tlink in title_links if tlink.find("a")]
        print(f"Собрано {len(links)} ссылок с {url}")
        return links
    except Exception as e:
        print(f"Error processing page {url}: {e}")
        return []


def scrape_all_pages(base_url):
    """Bypass all pagination pages and link collection."""
    try:
        driver.get(base_url)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        total_pages = get_total_pages(soup)

        print(f"Total number of pages: {total_pages}")

        all_links = []
        for page in range(1, total_pages + 1):
            page_url = f"{base_url}&page={page}"
            links = scrape_page(page_url)
            all_links.extend(links)

        return all_links

    except Exception as e:
        print(f"Error while crawling pages: {e}")
        return []


def insert_links_into_db(links):
    """Inserting unique links into the database with the current date. Uniqueness check is performed only for the current date."""
    current_date = datetime.now().strftime("%Y-%m-%d")

    with sq.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('SELECT url FROM cars WHERE date = ?', (current_date,))
        existing_links = {row[0] for row in cursor.fetchall()}
        
        unique_count = 0
        
        for link in links:
            if link not in existing_links:
                try:
                    cursor.execute('INSERT INTO cars (url, date) VALUES (?, ?)', (link, current_date))
                    unique_count += 1
                except sq.IntegrityError:
                    pass

        conn.commit()
        print(f"Added {unique_count} unique links to the database.")


def fetch_links():
    """Get links to machines that have not yet been processed."""
    with sq.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, url FROM cars WHERE brand IS NULL OR brand = ''") 
        return cursor.fetchall()


def update_car_data(car_id, car_data, field, value):
    """Update a specific field in a table"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    with sq.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        update_query = f"""
            UPDATE cars SET {field} = ?, date = ? WHERE id = ?
        """
        cursor.execute(update_query, (value, current_date, car_id))
        conn.commit()


def parse_car_page(driver, url, car_id):
    driver.refresh()
    """Collect data from a single vehicle page"""
    driver.get(url)
    time.sleep(1)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    ActionChains(driver).move_by_offset(10, 10).click().perform()

    soup = BeautifulSoup(driver.page_source, "html.parser")
    car_data = {}
    
    current_url = driver.current_url
    if current_url != url:
        print(f"🔃 Redirect detected: {url} → {current_url}.❌ Entry Deleted.")
        car_data['brand'] = 'DELETED'
        update_car_data(car_id, car_data, 'brand', car_data['brand'])
        return
    
    try:
        car_data["brand"] = soup.find("span", text="Марка, модель, рік").find_next("span", class_="d-link__name").text.split()[0]
    except:
        try:
            car_data["brand"] = soup.find("section", class_="vin_checked").find("span", class_="label", text="Марка, модель, рік").find_next("span", class_="argument").text.strip().split()[0]
        except:
            try:
                car_data["brand"] = soup.find("h1", class_="head").text.split()[0]
            except:
                try:
                    car_data["brand"] = soup.find("h1", class_="auto-head_title").find("strong").text.strip().split()[1]
                except AttributeError:
                    car_data["brand"] = ""

    if "brand" not in car_data:
        car_data["brand"] = ""

    update_car_data(car_id, car_data, "brand", car_data["brand"])

    try:
        car_data["model"] = soup.find("span", text="Марка, модель, рік").find_next("span", class_="d-link__name").text.split()[1]
    except:
        try:
            car_data["model"] = soup.find("section", class_="vin_checked").find("span", class_="label", text="Марка, модель, рік").find_next("span", class_="argument").text.strip().split()[1]
        except:
            try:
                car_data["model"] = soup.find("h1", class_="head").text.split()[1]
            except:
                try:
                    car_data["model"] = soup.find("h1", class_="auto-head_title").find("strong").text.strip().split()[2]
                except AttributeError:
                    car_data["model"]=""

    if "model" not in car_data:
        car_data["model"] = ""

    update_car_data(car_id, car_data, "model", car_data["model"])

    try:
        car_data["year"] = soup.find("span", text="Марка, модель, рік").find_next("span", class_="d-link__name").text.split()[-1]
    except:
        try:
            car_data["year"] = soup.find("section", class_="vin_checked").find("span", class_="label", text="Марка, модель, рік").find_next("span", class_="argument").text.strip().split()[-1]
        except:
            try:
                car_data["year"] = soup.find("h1", class_="head").text.split()[-1]
            except:
                try:
                    car_data["year"] = soup.find("h1", class_="auto-head_title").find("strong").text.strip().split()[-1]    
                except AttributeError:
                    car_data["year"]=""

    if "year" not in car_data:
        car_data["year"] = ""

    update_car_data(car_id, car_data, "year", car_data["year"])

    try:             
        if soup.find("div", id="main-image-gallery").find("img")["alt"]:
            car_title = soup.find("div", id="main-image-gallery").find("img")["alt"].strip()
        elif soup.find("h1", class_="auto-head_title").find("strong").text:
            car_title = soup.find("h1", class_="auto-head_title").find("strong").text.strip().split()[0]

        if "Новий" in car_title:
            car_data["new"] = 1
        else:
            car_data["new"] = 0
    except AttributeError:
        car_data["new"] = 0

    if "new" not in car_data:
        car_data["new"] = ""

    update_car_data(car_id, car_data, "new", car_data["new"])

    try:
        car_data["color"] = soup.find("span", text="Колір").find_next("span", class_="argument").text.strip()
    except:
        try:
            car_data["color"] = soup.find("dd", class_="color").find_next("div", class_="body_color_name").text.strip()
        except:
            try:
                car_data["color"] = soup.find("div", class_="mb-8 m-padding").text.strip()
            except AttributeError:
                car_data["color"]="" 

    if "color" not in car_data:
            car_data["color"] = ""

    update_car_data(car_id, car_data, "color", car_data["color"])

    try:
        car_data["mileage"] = int(soup.find("span", text="Пробіг від продавця").find_next("span", class_="argument").text.split()[0].replace("тис.км", "")) * 1000
    except:
        car_data["mileage"]=""

    if "mileage" not in car_data:
        car_data["mileage"] = ""

    update_car_data(car_id, car_data, "mileage", car_data["mileage"])

    try:
        car_data["engine_capacity"] = float(soup.find("span", text="Двигун").find_next("span", class_="argument").text.split()[0]) 
    except:
        try:
            engine_capacity_data = soup.find("section", class_="vin_checked").find("span", class_="label", text="Двигун").find_parent("dd").find("span", class_="argument").text.replace("•", "").split()[0]

            if not engine_capacity_data.isdigit():
                car_data["engine_capacity"] = ""
            else:
                car_data["engine_capacity"] = engine_capacity_data
        except:
            try:
                engine_span = soup.find("div", class_="m-grid-2 mb-24 m-padding grid-2 gap-24").find("span", string=lambda text: text and "л" in text)
                car_data["engine_capacity"] = engine_span.text.split(",")[1].strip().split()[0]
            except AttributeError:
                car_data["engine_capacity"]=""

    if "engine_capacity" not in car_data:
        car_data["engine_capacity"] = ""

    update_car_data(car_id, car_data, "engine_capacity", car_data["engine_capacity"])

    try:
        car_title = soup.find("div", id="main-image-gallery").find("img")["alt"].strip()
    
        if "Новий" in car_title:
            car_data["fuel_type"] = soup.find("span", text="Двигун").find_next("span", class_="argument").text.strip().split("•")[-1].strip()
        else:
            car_data["fuel_type"] = soup.find("span", text="Двигун").find_next("span", class_="argument").text.split("•")[1].strip()
    except:
        try:
            car_data["fuel_type"] = soup.find("span", text="Двигун").find_next("span", class_="argument").text.strip().split()[-1].strip() 

            valid_fuel_types = ["Дизель", "Бензин", "Гібрид", "Електро"]

            if not any(fuel in car_data["fuel_type"] for fuel in valid_fuel_types):
                car_data["fuel_type"] = soup.find("span", text="Двигун").find_next("span", class_="argument").text.split("•")[1].strip()
        except:
            try:
                car_data["fuel_type"] = soup.find("span", class_="characteristic-value").text.strip() 
            except AttributeError:
                car_data["fuel_type"]=""

    if "fuel_type" not in car_data:
        car_data["fuel_type"] = ""

    update_car_data(car_id, car_data, "fuel_type", car_data["fuel_type"])

    try:
        car_data["accident"] = soup.find("span", class_="label", text="ДТП").find_next_sibling("span", class_="argument").text.strip()
    except:
        car_data["accident"]="" 

    if "accident" not in car_data:
        car_data["accident"] = ""

    update_car_data(car_id, car_data, "accident", car_data["accident"])

    try:
        car_data["owners_count"] = int(soup.find("span", text="Кількість власників").find_next("span", class_="argument").text)
    except:
        car_data["owners_count"]=""

    if "owners_count" not in car_data:
        car_data["owners_count"] = ""

    update_car_data(car_id, car_data, "owners_count", car_data["owners_count"])

    try:
        car_data["car_number"] = soup.find("div", class_="t-check").find("span", class_="state-num").contents[0].strip().replace(" ", "")
    except:
        car_data["car_number"]=""

    if "car_number" not in car_data:
        car_data["car_number"] = ""

    update_car_data(car_id, car_data, "car_number", car_data["car_number"])

    try:
        car_data["vin"] = soup.find("div", class_="t-check").find("span", class_="label-vin").text.strip()
    except:
        try:
            car_data["vin"] = soup.find("div", class_="t-check").find("span", class_="vin-code").text.strip()
        except:
            try:
                car_data["vin"] = soup.find("div", class_="t-check").find("span", class_="label_vin").text.strip()
            except:
                try:
                    car_data["vin"] = soup.find("section", class_="vin_checked mb-48").find_all("li", class_="flex f-center gap-8")[1].text.strip()
                except AttributeError:
                    car_data["vin"]=""    

    if "vin" not in car_data:
        car_data["vin"] = ""

    update_car_data(car_id, car_data, "vin", car_data["vin"])

    try:
        car_data["city"] = soup.find("section", id="userInfoBlock").find("li", class_="item").find_next("li", class_="item").find("div", class_="item_inner").text.strip()
    except:
        try:
            car_data["city"] = soup.find("ul", class_="checked-list").find_all("li", class_="item")[1].find("div", class_="item_inner").text.split("•")[-1].strip()
        except:
            try:
                car_data["city"] = soup.find("section", class_="seller").find("ul", class_="checked-list").find_next("li", class_="item").find_next("li", class_="item").text.strip()
            except:
                try:
                    location_div = soup.find("div", class_="m-grid-2 mb-24 m-padding grid-2 gap-24")

                    city_element = None
                    
                    if location_div:
                        spans = location_div.find_all("span", class_="flex f-center gap-8")
                        for span in spans:
                           
                            if span.find("use", href=lambda href: href and "i16_pin" in href):
                                city_span = span.find("span")
                                if city_span:
                                    city_element = city_span.text.strip()
                                    break
                    car_data["city"] = city_element
                except AttributeError:   
                    car_data["city"]=""
    
    if "city" not in car_data:
        car_data["city"] = ""

    update_car_data(car_id, car_data, "city", car_data["city"])

    try:
        car_data["price"] = soup.find("div", class_="price_value").find("strong").text.replace("$", "").replace(" ", "").strip()
    except:
        try:   
            price_elements = soup.find_all("div", class_="price_value")
    
            for price_element in price_elements:
                price_text = price_element.text.strip()

                if "$" in price_text:
                    price_match = re.search(r"(\d[\d\s]*)\s?\$", price_text)
                    if price_match:
                        car_data["price"] = price_match.group(1).replace(" ", "")
                        break
        except:
            try:
                car_data_price = soup.find("aside", class_="auto-aside mhide").text.split()
                dollar_index = car_data_price.index("$")
                price_part1 = car_data_price[dollar_index - 2]
                price_part2 = car_data_price[dollar_index - 1]
                car_data["price"] = price_part1 + price_part2
            except AttributeError:
                car_data["price"] = ""

    if "price" not in car_data:
        car_data["price"] = ""

    update_car_data(car_id, car_data, "price", car_data["price"])

    try:
        car_data["name_seller"] = soup.find("div", class_="seller_info_name bold").find_next("a", class_="sellerPro").text.strip()
    except:
        try:
            car_data["name_seller"] = soup.find("h4", class_="seller_info_name").find("a").text.strip()
        except:
            try:
                car_data["name_seller"] = soup.find("div", class_="seller_info_area").find("strong", class_="name").text.strip()
            except:
                try:
                    car_data["name_seller"] = soup.find("div", class_="seller_info_name").text.strip()
                except AttributeError:
                    car_data["name_seller"]=""

    if "name_seller" not in car_data:
        car_data["name_seller"] = ""

    update_car_data(car_id, car_data, "name_seller", car_data["name_seller"])

    try:
        main_window = driver.current_window_handle
        time.sleep(random.uniform(1, 2))

        show_button = ""
        try:
            show_button = driver.find_element(By.CSS_SELECTOR, "#react-phones-aside span.conversion_phone_newcars").click()
        except:  
            try:
                show_button = driver.find_element(By.XPATH, "//div[@id='react-phones']//span[contains(@class, 'show-phone-btn')]").click()
            except:
                try:
                    show_button = driver.find_element(By.CSS_SELECTOR, "a.phone_show_link").click()
                except:
                    raise NoSuchElementException("Button to show phone not found.")
                
        time.sleep(random.uniform(1, 2))

        # Check for opening a new tab
        if len(driver.window_handles) > 1:
            new_window = driver.window_handles[-1]
            driver.switch_to.window(new_window)
            driver.close()
            driver.switch_to.window(main_window)
    
        time.sleep(random.uniform(1, 2))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        phone_span = None

        try:
            phone_span = soup.find("span", class_="phone bold").text.strip().replace(" ", "")
        except:
            try:
                phone_span = soup.select_one("div.react_modal__body span.load_phone__item").text.strip().replace(" ", "")
            except:
                try:
                    phone_span = soup.find("section", class_="phones_modal__item").find("a", class_="phone unlink bold load_phone__item proven").text.strip().replace(" ", "")
                except:    
                    try:
                        phone_span = soup.select_one("div.react_modal__body a.load_phone__item").text.strip().replace(" ", "")
                    except:
                        try:
                            print("BeautifulSoup couldn't extract the number, trying Selenium.")
                            # If BeautifulSoup didn't find the phone, try Selenium with an explicit wait
                            if not phone_span:
                                wait = WebDriverWait(driver, 2)
                                modal_phone = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.react_modal__body a.load_phone__item")))
                                phone_span = modal_phone.text.strip().replace(" ", "")
                        except:
                            # Explicitly wait for a link with a phone number to appear in the window
                            wait = WebDriverWait(driver, 5)
                            modal_phone = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.load_phone__item")))
                            phone_span = modal_phone.text.strip().replace(" ", "")

        if phone_span:
            car_data["phone_seller"] = phone_span
        else:
            raise AttributeError("Phone number not found.")
    except (NoSuchElementException, TimeoutException, AttributeError) as e:
        car_data["phone_seller"] = ""

    if "phone_seller" not in car_data:
        car_data["phone_seller"] = ""

    update_car_data(car_id, car_data, "phone_seller", car_data["phone_seller"])

    return car_data
   

def main():
    # Link through which data will be collected
    base_url = "https://auto.ria.com/uk/search/?indexName=auto,order_auto,newauto_search&year[0].gte=2024&categories.main.id=1&brand.id[0]=24&country.import.usa.not=-1&price.currency=1&abroad.not=0&custom.not=1&page=0&size=20"

    # This block can be hidden when all necessary links are collected
    create_db()
    all_links = scrape_all_pages(base_url)
    print(f"Total {len(all_links)} links collected:")
    insert_links_into_db(all_links)
    # ----------------------------------------------------------

    links = fetch_links()
    
    if not links:
        print("There are no new links to process.")
        return
    
    total_links = len(links)
    for index, (car_id, url) in enumerate(links, 1):
        print(f"Link {index} of {total_links}")
        print(f"Processing {url}")
        car_data = parse_car_page(driver, url, car_id)


if __name__ == "__main__":
    main()
    print("⏳ Start of processing...")
    driver.close()
    driver.quit()
    print("✅ The processing is complete.")