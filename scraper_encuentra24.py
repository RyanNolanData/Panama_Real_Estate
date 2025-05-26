import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random

# Constants
BASE_URL = 'https://www.encuentra24.com'
START_URL = 'https://www.encuentra24.com/panama-es/searchresult/bienes-raices-venta-de-propiedades?sort=f_added&dir=desc&q=f_price.-500000|f_square.70-'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Config: Set number of pages (None for all)
#MAX_PAGES = None  # Set to an integer like 5 to limit pages
MAX_PAGES = 5  # Set to an integer like 5 to limit pages


# Container for data
data = []

# Start scraping
current_url = START_URL
page_count = 0

while current_url:
    print(f"Scraping page {page_count + 1}: {current_url}")
    response = requests.get(current_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    ads = soup.find_all('div', class_='d3-ad-tile__content')

    for ad in ads:
        try:
            link_tag = ad.find('a', class_='d3-ad-tile__description')
            link = BASE_URL + link_tag['href'] if link_tag and link_tag.has_attr('href') else None

            location_tag = ad.find('div', class_='d3-ad-tile__location')
            location = location_tag.get_text(strip=True) if location_tag else None

            title_tag = ad.find('span', class_='d3-ad-tile__title')
            title = title_tag.get_text(strip=True) if title_tag else None

            description_tag = ad.find('div', class_='d3-ad-tile__short-description')
            description = description_tag.get_text(strip=True) if description_tag else None

            price_tag = ad.find('div', class_='d3-ad-tile__price')
            price_text = price_tag.get_text(strip=True) if price_tag else None
            price = int(re.sub(r'[^\d]', '', price_text)) if price_text else None

            m2 = None
            Bedrooms = None
            Bathrooms = None

            details = ad.find_all('li', class_='d3-ad-tile__details-item')
            for detail in details:
                icon = detail.find('use')
                text = detail.get_text(strip=True)
                if not icon or not text:
                    continue

                icon_href = icon.get('xlink:href', '')

                if '#resize' in icon_href:
                    match = re.search(r'(\d+)\s*m\s*2', text)
                    if match:
                        m2 = int(match.group(1))
                elif '#bed' in icon_href:
                    match = re.search(r'(\d+)', text)
                    if match:
                        Bedrooms = int(match.group(1))
                elif '#bath' in icon_href:
                    match = re.search(r'(\d+(\.\d+)?)', text)
                    if match:
                        Bathrooms = float(match.group(1))

            data.append({
                'title': title,
                'size': m2,
                'bedrooms': Bedrooms,
                'bathrooms': Bathrooms,
                'price': price,
                'description': description,
                'link': link,
                'location': location
            })

        except Exception as e:
            print(f"Error processing ad: {e}")

    page_count += 1
    if MAX_PAGES is not None and page_count >= MAX_PAGES:
        break

    # Find the next page link
    next_link = soup.find('a', class_='d3-pagination__arrow--next')
    if next_link and next_link.has_attr('href'):
        current_url = BASE_URL + next_link['href']
        delay = random.uniform(1, 5)
        print(f"Sleeping for {delay:.2f} seconds...\n")
        time.sleep(delay)
    else:
        break

# Convert to DataFrame
df = pd.DataFrame(data)
print(f"Total listings scraped: {len(df)}")

# Optionally save
# df.to_csv("real_estate_data.csv", index=False)


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



#Part 3
#Compare price per square meter to area-specific benchmarks (provided) -> Done
#Mark listings as “FLIPPABLE” if they meet all conditions -> FILTERED NOT FLIPPED
#Listings are considered flippable if their price per m² is 25% or more below the average benchmark for the area. -> Done
#Filter by Target areas: [Includes multiple neighborhoods in Panama City — will be provided] -> Done


#Part 4
#Export matching listings to Google Sheets
#All Listings Tab
#New Listings Tab




