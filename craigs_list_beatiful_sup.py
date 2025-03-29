

import requests
from bs4 import BeautifulSoup

def scrape_craigslist():
    url = 'https://vancouver.craigslist.org/search/sub?query=may+sublet&max_price=1200'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        # listings = soup.select("a") # links to the listing
        valid_links = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href and not href.startswith('#'):
                # Optional: Only include fully qualified URLs
                if href.startswith('http://') or href.startswith('https://'):
                    valid_links.append(href)
        return valid_links
        # agent to find whether the criterion is actually met. 
        # method wtihte hin in 

        print("🔍 Sublet Listings in Vancouver (May, under $1200):\n")
        for link in listings:
            print(f"🔗 {link['href']}\n")

    except requests.exceptions.RequestException as e:
        print("⚠️ Connection error:", e)
        return valid_links

# scrape_craigslist()