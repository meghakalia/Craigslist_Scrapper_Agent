import requests
from bs4 import BeautifulSoup
from typing import Optional

def build_craigslist_url(
    city: str = 'vancouver',
    category: str = 'sub',  # sub = sublets/temporary
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    postal_code: Optional[str] = None,
    search_distance: Optional[int] = None,
    query: Optional[str] = None
) -> str:
    """
    Build a Craigslist URL based on search parameters.
    
    Args:
        city: City to search in (e.g., 'vancouver', 'seattle', 'toronto')
        category: Listing category (e.g., 'sub' for sublets, 'apa' for apartments)
        max_price: Maximum price filter
        min_price: Minimum price filter
        postal_code: Postal/ZIP code to search around
        search_distance: Search radius in miles from postal code
        query: Search terms
    """
    # Base URL construction
    base_url = f'https://{city}.craigslist.org/search/{category}'
    
    # Build query parameters
    params = {}
    if query:
        params['query'] = query
    if max_price:
        params['max_price'] = str(max_price)
    if min_price:
        params['min_price'] = str(min_price)
    if postal_code:
        params['postal'] = postal_code
    if search_distance:
        params['search_distance'] = str(search_distance)
    
    # Construct URL with parameters
    if params:
        param_strings = [f"{key}={value}" for key, value in params.items()]
        return f"{base_url}?{'&'.join(param_strings)}"
    return base_url

def scrape_craigslist(
    city: str = 'vancouver',
    category: str = 'sub',
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    postal_code: Optional[str] = None,
    search_distance: Optional[int] = None,
    query: Optional[str] = None
):
    url = build_craigslist_url(
        city=city,
        category=category,
        max_price=max_price,
        min_price=min_price,
        postal_code=postal_code,
        search_distance=search_distance,
        query=query
    )

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

# Example usage:
if __name__ == "__main__":
    # # Example 1: Basic search for sublets in Vancouver under $1200
    # results = scrape_craigslist(
    #     city='vancouver',
    #     max_price=1200,
    #     query='may sublet'
    # )
    
    # Example 2: Search for apartments within 5 miles of a specific postal code
    results = scrape_craigslist(
        city='Vancouver',
        category='sub',  # apartments
        max_price=2400,
        postal_code='V6H3E9',
        search_distance=3
    )

    for link in results:
        print(link)