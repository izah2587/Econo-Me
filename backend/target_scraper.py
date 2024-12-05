from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import csv

# Set up Chrome WebDriver using WebDriver Manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# CSV file setup
csv_filename = "target_products.csv"
fields = ["id", "store_name", "product_name", "url", "price", "last_checked_at"]

# Open the CSV file in write mode
with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()  # Write header row

    seen_links = set()  # To avoid scraping duplicate products
    product_data = []  # List to store all scraped products
    
    # Base URL for the Target product page (without Nao parameter)
    base_url = "https://www.target.com/c/fresh-vegetables-produce-grocery/-/N-4tglh?Nao="

    # Function to scrape product data from a page using Selenium
    def scrape_page(driver, page_number):
        # Construct the URL for the current page
        url = base_url + str(page_number * 12) + "&moveTo=product-list-grid"  # Nao=12 for page 1, Nao=24 for page 2, etc.
        driver.get(url)

        # Allow time for the page to load
        time.sleep(5)

        # Find all product elements on the page
        products = driver.find_elements(By.CSS_SELECTOR, 'div[data-test="@web/ProductCard/body"]')

        # Extract data from the products on the current page
        for product in products:
            try:
                # Extract product link
                link = product.find_element(By.CSS_SELECTOR, 'a[data-test="product-title"]')
                link_href = link.get_attribute('href') if link else 'No link available'
            except:
                link_href = 'No link available'

            # Skip the product if it's already in the set of seen links
            if link_href in seen_links:
                continue
            seen_links.add(link_href)

            try:
                # Extract product name
                name = product.find_element(By.CSS_SELECTOR, 'a[data-test="product-title"]')
                product_name = name.text.strip() if name else 'No name available'
                product_name = product_name.split(' -')[0]  # Clean up the name if it contains variants
            except:
                product_name = 'No name available'

            try:
                # Extract product price
                price = product.find_element(By.CSS_SELECTOR, 'span[data-test="current-price"]')
                price_text = price.text.strip() if price else 'No price available'
            except:
                price_text = 'No price available'

            # Add store name and timestamp
            store_name = "Target"  # Static store name since we're scraping Target
            last_checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Append the extracted product data to the list
            product_data.append({
                'id': len(product_data) + 1,  # Auto-increment ID
                'store_name': store_name,
                'product_name': product_name,
                'url': link_href,
                'price': price_text,
                'last_checked_at': last_checked_at
            })

    # Scrape pages 1 to 10
    for page in range(1,10):
        scrape_page(driver, page)

    # Write the scraped data to the CSV file
    for data in product_data:
        print(data)  # Optional: print the data to the console
        writer.writerow(data)

# Close the browser when done
driver.quit()

print(f"Scraping complete. Data saved to '{csv_filename}'.")
