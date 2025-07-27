from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import random

# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv()

def setup_chrome_options():
    chrome_options = Options()
    
    # Use headless mode from environment variable
    if os.getenv('HEADLESS_MODE', 'True').lower() == 'true':
        chrome_options.add_argument('--headless=new')
    
    # Basic Chrome options for stability
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--enable-unsafe-swiftshader')
    chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # Set custom binary location if specified
    if chrome_binary := os.getenv('CHROME_BINARY_LOCATION'):
        chrome_options.binary_location = chrome_binary
        
    return chrome_options

# Get user agent from environment or use defaults
default_user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15',
]

user_agents = [os.getenv('USER_AGENT')] if os.getenv('USER_AGENT') else default_user_agents

def get_headers():
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def get_product_details(product_url: str) -> dict:
    product_details = {}
    driver = None
    try:
        # Get Chrome options using our setup function
        chrome_options = setup_chrome_options()
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--disable-web-security')
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Setup Chrome driver with new options
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Set page load timeout
        driver.set_page_load_timeout(30)
        
        # Add random delay between requests (2-4 seconds)
        time.sleep(random.uniform(2, 4))
        
        # Load the page with JavaScript rendering
        driver.get(product_url)
        
        # Wait for body to be present to ensure page is loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for and get the product title
        # Get page source first for BeautifulSoup parsing
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        # Try to get title using Selenium first
        try:
            title_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "productTitle"))
            )
            title = title_element.text.strip()
        except:
            # Fallback to using BeautifulSoup if Selenium fails
            title_element = soup.find('span', {'id': 'productTitle'})
            if not title_element:
                raise ValueError("Could not find product title")
            title = title_element.text.strip()
        
        # Store the title
        product_details['title'] = title
        
        # Wait a bit for dynamic content to load
        time.sleep(2)
        
        # Get product image using Selenium
        try:
            image_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#landingImage, #imgBlkFront"))
            )
            product_details['image_url'] = image_element.get_attribute('src')
        except:
            # If image not found, try alternate method
            try:
                image_element = driver.find_element(By.CSS_SELECTOR, "img.a-dynamic-image")
                product_details['image_url'] = image_element.get_attribute('src')
            except:
                product_details['image_url'] = ''

        # Get price using Selenium
        try:
            price_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".a-price-whole, .a-price"))
            )
            price = price_element.text.strip()
            price = ''.join(filter(str.isdigit, price))
            if len(price) % 2 == 0 and price[:len(price)//2] == price[len(price)//2:]:
                price = price[:len(price)//2]
        except:
            raise ValueError("Could not find product price")

        # Get product description
        description_element = soup.find('div', {'id': 'productDescription'})
        if description_element:
            product_details['description'] = description_element.get_text().strip()
        
        # Get product rating
        rating_element = soup.find('span', {'class': 'a-icon-alt'})
        if rating_element:
            product_details['rating'] = rating_element.get_text().strip()

        # Get product features
        feature_bullets = soup.find('div', {'id': 'feature-bullets'})
        if feature_bullets:
            features = feature_bullets.find_all('li')
            product_details['features'] = [feature.get_text().strip() for feature in features]

        # Get recommended products using Selenium
        recommended_products = []
        try:
            # Scroll to bring recommendations into view
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)  # Wait for recommendations to load
            
            # Try different selectors for recommendations
            selectors = [
                "div[data-cel-widget^='similar_to_this_item'] .a-carousel-card",
                "#similarity-cards .a-carousel-card",
                "#purchase-sims-feature .a-carousel-card",
                "[data-cel-widget='desktop-dp-sims'] .a-carousel-card"
            ]
            
            cards = []
            for selector in selectors:
                try:
                    cards = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if cards:
                        break
                except:
                    continue
            
            for card in cards[:4]:  # Limit to 4 recommendations
                try:
                    rec_product = {}
                    
                    # Scroll card into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    time.sleep(0.5)
                    
                    # Get image - try multiple selectors
                    try:
                        img = card.find_element(By.CSS_SELECTOR, "img[src*='images/']")
                        src = img.get_attribute('src')
                        if 'IconFarm' not in src and 'transparent-pixel' not in src:
                            rec_product['image'] = src
                    except:
                        continue
                    
                    # Get title - try multiple selectors
                    try:
                        title = card.find_element(By.CSS_SELECTOR, ".a-text-normal, .a-size-base")
                        title_text = title.text.strip()
                        if len(title_text) > 10:  # Ensure it's a real product title
                            rec_product['title'] = title_text
                        else:
                            continue
                    except:
                        continue
                    
                    # Get URL
                    try:
                        link = card.find_element(By.CSS_SELECTOR, "a[href*='/dp/']")
                        url = link.get_attribute('href')
                        if '/dp/' in url:  # Ensure it's a product URL
                            rec_product['url'] = url
                    except:
                        rec_product['url'] = ''
                    
                    if rec_product.get('image') and rec_product.get('title'):
                        recommended_products.append(rec_product)
                except Exception as e:
                    continue
        except:
            pass  # Continue without recommendations if they can't be loaded

        # Adding everything to the product details dictionary
        product_details.update({
            'title': title,
            'price': price,
            'product_url': product_url,
            'recommended_products': recommended_products[:4]  # Limit to 4 recommendations
        })

        # Return the product details dictionary
        return product_details
    except Exception as e:
        print('Could not fetch product details')
        print(f'Failed with exception: {e}')
        return {}
    finally:
        # Make sure to close the browser
        try:
            driver.quit()
        except:
            pass

# The script will now be controlled by the Flask app

