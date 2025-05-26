import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import re
import time

# Config
#MAX_PAGES = None  # Set to an integer like 5 to limit, or None for all pages
MAX_PAGES = 5  # Set to an integer like 5 to limit, or None for all pages


# Setup undetected Chrome
options = uc.ChromeOptions()
options.headless = False
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0")

driver = uc.Chrome(options=options)

# Start URL
url = 'https://www.compreoalquile.com/casas-o-apartamentos-en-venta-en-panama-provincia-ordenado-por-fechaonline-descendente.html'
driver.get(url)
time.sleep(10)

data = []
page_num = 1

while True:
    print(f"\n📄 Scraping page {page_num}...")
    time.sleep(10)  # Wait for JS & Cloudflare
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    cards = driver.find_elements(By.CLASS_NAME, "postingCard-module__posting-container")
    print(f"✅ Found {len(cards)} listings.")

    for card in cards:
        try:
            price_raw = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_PRICE"]').text
            price = int(re.sub(r"[^\d]", "", price_raw))

            desc_el = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_DESCRIPTION"] a')
            description = desc_el.text.strip().split(".")[0]

            size_el = card.find_element(By.CSS_SELECTOR, '[data-qa="POSTING_CARD_FEATURES"]')
            size_match = re.search(r'([\d.,]+)\s*m²', size_el.text)
            size = int(size_match.group(1).replace(".", "").replace(",", "")) if size_match else None

            relative_link = desc_el.get_attribute("href")
            link = relative_link if relative_link.startswith("http") else "https://www.compreoalquile.com" + relative_link

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

    # Stop if page limit is reached
    if MAX_PAGES is not None and page_num >= MAX_PAGES:
        print("🛑 Reached max page limit.")
        break

    # Try to go to next page
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, '[data-qa="PAGING_NEXT"]')
        if not next_button.get_attribute("href"):
            print("🚫 No more pages.")
            break
        driver.execute_script("arguments[0].click();", next_button)
        page_num += 1
        time.sleep(5)
    except NoSuchElementException:
        print("🚫 Next button not found.")
        break

driver.quit()

# DataFrame creation
df = pd.DataFrame(data)
print(f"\n📊 Total scraped listings: {len(df)}")

# Filter results
df2 = df[(df['size'] >= 70) & (df['price'] <= 500000)]
df2['price'].fillna(1)
df2['price_per_m2'] = df2['price'] / df2['size']

#CITIES PRICES ARE NOT FINAL!
city_prices = {
    'El Cangrejo': 2035,
    'El Carmen': 1770,
    'Obarrio': 2365,
    'Costa del Este': 2930,
    'Marbella': 2540,
    'Chanis': 1490,
    'La Alameda': 1665,
    'El Ingenio': 1530,
    'Betania': 1490,
    'Pueblo Nuevo': 1205,
    'Tumba Muerto': 1310,
    'Santa María': 3065,
    'San Miguel': 1160,
    'La Locería': 1620
}

#Filters down by city
df2 = df2[df2['location'].isin(city_prices)].copy()

df2['avg_city_price'] = df2['location'].map(city_prices)

df2 = df2[df2['price_per_m2'] <= 0.75 * df2['avg_city_price']].reset_index(drop=True)


#(Optional) Detect specific keywords like “remodelar”, “rebajada”, etc.
# Define synonym lists
renovation_keywords = [
    'remodelar', 
    'reformar', 
    'renovar', 
    'reparar', 
    'actualizar', 
    'mejorar', 
    'para remodelar', 
    'necesita renovación'
]

reduced_keywords = [
    'rebajada', 
    'descuento', 
    'oferta', 
    'negociable', 
    'bajada de precio'
]

negotiate_keywords = [
    'precio negociable',
    'se puede negociar',
    'negociable',
    'acepta ofertas',
    'dispuesto a negociar',
    'precio conversable',
    'negociación disponible',
    'abierto a ofertas'
]

urgent_keywords = [
    'urgente',
    'venta rápida',
    'se necesita vender pronto',
    'liquidación',
    'venta inmediata',
    'apresurada',
    'se escucha oferta urgente',
    'venta por motivo urgente'
]

# Combine keywords into regex patterns
renovation_pattern = '|'.join(renovation_keywords)
reduced_pattern = '|'.join(reduced_keywords)
negotiate_pattern = '|'.join(negotiate_keywords)
urgent_pattern = '|'.join(urgent_keywords)

# Create the new boolean columns
df2['needs_renovation'] = df2['description'].str.contains(renovation_pattern, case=False, na=False)
df2['price_reduced'] = df2['description'].str.contains(reduced_pattern, case=False, na=False)
df2['negotiate'] = df2['description'].str.contains(negotiate_pattern, case=False, na=False)
df2['urgent'] = df2['description'].str.contains(urgent_pattern, case=False, na=False)



print(df2)
