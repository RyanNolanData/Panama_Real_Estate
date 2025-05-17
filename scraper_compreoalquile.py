#one page atm need to expand

#pip install beautifulsoup4
#pip install pandas
#pip install selenium webdriver-manager
#pip install setuptools

#pip install undetected-chromedriver pandas 
#This needs to be in an advanced video # You're being served a bot protection / challenge page, not the real content. This is typically from Cloudflare or a similar service that detects automation.



import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import re
import time

# Setup undetected Chrome with anti-bot evasion
options = uc.ChromeOptions()
options.headless = False  # Must be False or you'll be blocked
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0")

driver = uc.Chrome(options=options)

# Load the target URL
url = 'https://www.compreoalquile.com/casas-o-apartamentos-en-venta-en-panama-provincia-mas-de-70-metros-cuadrados-hasta-500000-dolares-ordenado-por-fechaonline-descendente.html'
driver.get(url)

# Wait for Cloudflare and JS rendering
time.sleep(10)

# Scroll to trigger lazy loading
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(5)

# Grab all listing containers
cards = driver.find_elements(By.CLASS_NAME, "postingCard-module__posting-container")
print(f"✅ Found {len(cards)} listings.")

data = []

for card in cards:
    try:
        # Price
        price_raw = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_PRICE"]').text
        price = int(re.sub(r"[^\d]", "", price_raw))

        # Description
        desc_el = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_DESCRIPTION"] a')
        description = desc_el.text.strip().split(".")[0]

        # Size
        size_el = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_FEATURES"]')
        size_match = re.search(r'([\d.,]+)\s*m²', size_el.text)
        size = int(size_match.group(1).replace(".", "").replace(",", "")) if size_match else None

        # Link
        relative_link = desc_el.get_attribute("href")
        link = relative_link if relative_link.startswith("http") else "https://www.compreoalquile.com" + relative_link

        # Location
        location_el = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_LOCATION"]')
        location = location_el.text.strip().split(",")[0]

        data.append({
            "price": price,
            "description": description,
            "size": size,
            "link": link,
            "location": location
        })

    except Exception as e:
        print("⚠️ Skipping one due to error:", e)
        continue

driver.quit()

# Create DataFrame
df = pd.DataFrame(data)
print("\n📄 All Listings:")
print(df)


df2 = df[(df['size'] >= 70) & (df['price'] <= 500000)]
df2['price'].fillna(1)
df2['price_per_m2'] = df2['price'] / df2['size']


#(Optional) Detect specific keywords like “remodelar”, “rebajada”, etc.
# Define synonym lists
renovation_keywords = ['remodelar', 'reformar', 'renovar', 'reparar', 'actualizar', 'mejorar']
reduced_keywords = ['rebajada', 'descuento', 'oferta', 'negociable', 'bajada de precio']

# Combine keywords into regex patterns
renovation_pattern = '|'.join(renovation_keywords)
reduced_pattern = '|'.join(reduced_keywords)

# Create the new boolean columns
df2['needs_renovation'] = df2['description'].str.contains(renovation_pattern, case=False, na=False)
df2['price_reduced'] = df2['description'].str.contains(reduced_pattern, case=False, na=False)

print(df2)















#Ryan Notes:
#1 PAB = 1 USD
#B/.129,900 = $129,000


#https://www.compreoalquile.com/casas-o-apartamentos-en-venta-en-panama-provincia-mas-de-70-metros-cuadrados-hasta-500000-dolares-ordenado-por-fechaonline-descendente.html
#^URL For Most Recent, Filter Under 500k, over 70m^2




#Part 1
#Extract key property details: price, size, location, link, description, etc.


#Part 2 Data Cleanup
#Remove Currency, use as an int, make sure its under 500000
#Calculate price per square meter
#Maximum purchase price: $500,000 USD
#Minimum size: 70 m²




#Part 3
#Compare price per square meter to area-specific benchmarks (provided)
#Mark listings as “FLIPPABLE” if they meet all conditions
#Listings are considered flippable if their price per m² is 25% or more below the average benchmark for the area.
#Filter by Target areas: [Includes multiple neighborhoods in Panama City — will be provided]
#(Optional) Detect specific keywords like “remodelar”, “rebajada”, etc.



#Part 4
#Export matching listings to Google Sheets
#All Listings Tab
#New Listings Tab
