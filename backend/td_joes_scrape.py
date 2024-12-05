from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time

# Set up Chrome WebDriver using WebDriver Manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# CSV file setup
csv_filename = "trader_joes_products.csv"
fields = ["id", "store_name", "product_name", "url", "price", "last_checked_at"]

# Open the CSV file in write mode
with open(csv_filename, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fields)
    writer.writeheader()  # Write header row

    id_counter = 1  # Initialize ID counter
    
    # Base URL for the Trader Joe's page with placeholder for the page number
    base_url = "https://www.traderjoes.com/home/products/category/fresh-fruits-veggies-113?filters=%7B%22page%22%3A{}%7D"
    
    # 1. Scrape the first page (without page number manipulation)
    print("Scraping page 1...")
    driver.get("https://www.traderjoes.com/home/products/category/fresh-fruits-veggies-113")  # No page number query

    # Wait for the page content to load
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'ProductList_productList__item__1EIvq'))
        )
    except Exception as e:
        print(f"Timeout or error occurred while loading results for page 1: {e}")
        driver.quit()
        exit()  # Exit if there's an error

    # Get the page source after JavaScript loads
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find all <li> tags containing product info
    search_results = soup.find_all("li", class_="ProductList_productList__item__1EIvq")

    # If there are results, extract details
    if search_results:
        print(f"Found {len(search_results)} results on page 1.")

        for result in search_results:
            # Extract the product name
            title_tag = result.find("h2", class_="ProductCard_card__title__text__uiWLe")
            product_name = title_tag.text.strip() if title_tag else "No title found"
            
            # Extract the product link
            link_tag = result.find("a", class_="Link_link__1AZfr ProductCard_card__title__301JH ProductCard_card__title__large__3bAY6")
            product_link = f"https://www.traderjoes.com{link_tag['href']}" if link_tag else "No link found"
            
            # Extract the price
            price_tag = result.find("span", class_="ProductPrice_productPrice__price__3-50j")
            product_price = price_tag.text.strip() if price_tag else "No price found"
            
            # Get the current timestamp
            last_checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Write the extracted data to the CSV file
            writer.writerow({
                "id": id_counter,
                "store_name": "Trader Joe's",
                "product_name": product_name,
                "url": product_link,
                "price": product_price,
                "last_checked_at": last_checked_at
            })
            
            # Increment the ID counter
            id_counter += 1

            # Print feedback to console for tracking
            print(f"Added '{product_name}' to CSV.")
            print("-" * 40)

    else:
        print(f"No results found on page 1.")

    # 2. Scrape pages 2 to 4 using the URL with page number manipulation
    for page_num in range(2, 5):  # Loop from page 2 to page 4
        print(f"Scraping page {page_num}...")

        # Construct the URL for the current page
        url = base_url.format(page_num)
        driver.get(url)

        # Wait for the page content to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'ProductList_productList__item__1EIvq'))
            )
        except Exception as e:
            print(f"Timeout or error occurred while loading results for page {page_num}: {e}")
            continue  # Skip to the next page if there's an issue
        
        # Get the page source after JavaScript loads
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all <li> tags containing product info
        search_results = soup.find_all("li", class_="ProductList_productList__item__1EIvq")

        # If there are results, extract details
        if search_results:
            print(f"Found {len(search_results)} results on page {page_num}.")

            for result in search_results:
                # Extract the product name
                title_tag = result.find("h2", class_="ProductCard_card__title__text__uiWLe")
                product_name = title_tag.text.strip() if title_tag else "No title found"
                
                # Extract the product link
                link_tag = result.find("a", class_="Link_link__1AZfr ProductCard_card__title__301JH ProductCard_card__title__large__3bAY6")
                product_link = f"https://www.traderjoes.com{link_tag['href']}" if link_tag else "No link found"
                
                # Extract the price
                price_tag = result.find("span", class_="ProductPrice_productPrice__price__3-50j")
                product_price = price_tag.text.strip() if price_tag else "No price found"
                
                # Get the current timestamp
                last_checked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Write the extracted data to the CSV file
                writer.writerow({
                    "id": id_counter,
                    "store_name": "Trader Joe's",
                    "product_name": product_name,
                    "url": product_link,
                    "price": product_price,
                    "last_checked_at": last_checked_at
                })
                
                # Increment the ID counter
                id_counter += 1

                # Print feedback to console for tracking
                print(f"Added '{product_name}' to CSV.")
                print("-" * 40)

        else:
            print(f"No results found on page {page_num}.")

# Close the browser when done
driver.quit()

print(f"Scraping complete. Data saved to '{csv_filename}'.")
