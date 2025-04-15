import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
import io
import os
from typing import Dict, Optional, List
import re
import glob
import json

def get_current_csv_path() -> str:
    """
    Determine the appropriate CSV file path based on date and entry count rules.
    Returns path in format: 'craigslist_listings_YYYY_MM_DD.csv'
    """
    today = datetime.now().strftime('%Y_%m_%d')
    
    # Look for existing CSV files
    existing_files = glob.glob('craigslist_listings_*.csv')
    today_file = f'craigslist_listings_{today}.csv'
    
    # If today's file exists, use it
    if today_file in existing_files:
        return today_file
    
    # If no files exist or it's a new day, create today's file
    if not existing_files:
        return today_file
    
    # Check the most recent file's entry count
    latest_file = max(existing_files, key=os.path.getctime)
    if latest_file == today_file:
        return today_file
    
    try:
        df_latest = pd.read_csv(latest_file)
        # If it's a new day and the last file has ≥ 300 entries, create a new file
        if len(df_latest) >= 300:
            return today_file
        # If it's a new day but last file has < 300 entries, continue using it
        return latest_file
    except Exception as e:
        print(f"Error reading latest file: {e}")
        return today_file

def is_duplicate_listing(url: str) -> bool:
    """
    Check if the listing URL exists in any of the previous CSV files
    """
    csv_files = glob.glob('craigslist_listings_*.csv')
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if 'link' in df.columns and url in df['link'].values:
                return True
        except Exception as e:
            print(f"Error checking duplicates in {csv_file}: {e}")
            continue
    
    return False

def detect_watermark(image_url: str) -> bool:
    """
    Detect if an image has a watermark using basic image processing
    """
    # use a VLM here 
    try:
        # Download image
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        # Count white pixels (potential watermark)
        white_pixel_ratio = np.sum(thresh == 255) / thresh.size
        
        # If more than 5% of the image is white, might be a watermark
        return white_pixel_ratio > 0.05
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def extract_listing_details(url: str) -> Dict[str, any]:
    """
    Extract details from a Craigslist listing
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize details dictionary
        details = {
            'date_scraped': datetime.now().strftime('%Y-%m-%d'),
            'link': url,
            'price': None,
            'rooms': None,
            'separate_bath': False,
            'separate_kitchen': False,
            'neighborhood': None,
            'start_date': None,
            'num_images': 0,
            'has_watermark': False
        }
        
        # Extract price
        price_elem = soup.find('span', {'class': 'price'})
        if price_elem:
            price_text = price_elem.text.strip()
            details['price'] = int(re.sub(r'[^\d]', '', price_text))
        
        # Extract location/neighborhood
        location_elem = soup.find('div', {'class': 'mapaddress'})
        if location_elem:
            details['neighborhood'] = location_elem.text.strip()
        
        # Count images
        gallery = soup.find('div', {'id': 'thumb'})
        if gallery:
            image_elements = gallery.find_all('img')
            details['num_images'] = len(image_elements)
            
            # Check first image for watermark
            if image_elements:
                first_image_url = image_elements[0].get('src')
                if first_image_url:
                    details['has_watermark'] = detect_watermark(first_image_url)
        
        # Extract posting body text
        body = soup.find('section', {'id': 'postingbody'})
        if body:
            body_text = body.text.lower()
            
            # Check for room details in description
            details['separate_bath'] = any(term in body_text for term in ['private bath', 'own bath', 'separate bath'])
            details['separate_kitchen'] = any(term in body_text for term in ['private kitchen', 'own kitchen', 'separate kitchen'])
            
            # Try to extract number of rooms
            room_patterns = [r'(\d+)\s*bed', r'(\d+)\s*room']
            for pattern in room_patterns:
                match = re.search(pattern, body_text)
                if match:
                    details['rooms'] = int(match.group(1))
                    break
            
            # Try to extract start date
            date_patterns = [
                r'available\s+(\w+\s+\d{1,2})',
                r'starting\s+(\w+\s+\d{1,2})',
                r'from\s+(\w+\s+\d{1,2})'
            ]
            for pattern in date_patterns:
                match = re.search(pattern, body_text)
                if match:
                    try:
                        date_str = match.group(1)
                        # Add current year since Craigslist listings typically don't include it
                        details['start_date'] = datetime.strptime(
                            f"{date_str} {datetime.now().year}", 
                            '%B %d %Y'
                        ).strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
        
        return details
    
    except Exception as e:
        print(f"Error processing listing {url}: {e}")
        return None

def update_listings_csv(listing_url: str):
    """
    Process a listing and update the appropriate CSV file,
    handling duplicates and file size limits
    """
    # Check for duplicates across all existing CSVs
    if is_duplicate_listing(listing_url):
        print(f"Duplicate listing found, skipping: {listing_url}")
        return
    
    # Extract details from the listing
    details = extract_listing_details(listing_url)
    
    if not details:
        print(f"Could not process listing: {listing_url}")
        return
    
    # Update JSON database first
    if not update_json_database(details):
        print(f"Error updating JSON database: {listing_url}")
        return
    
    # If JSON update successful, update CSV
    csv_path = get_current_csv_path()
    
    # Convert details to DataFrame
    df_new = pd.DataFrame([details])
    
    # Load existing CSV or create new one
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_updated = df_new
    
    # Save updated DataFrame to CSV
    df_updated.to_csv(csv_path, index=False)
    print(f"Successfully updated both JSON and CSV with listing: {listing_url}")
    print(f"Updated {csv_path} with listing: {listing_url}")

def get_csv_stats():
    """
    Print statistics about all existing CSV files
    """
    csv_files = glob.glob('craigslist_listings_*.csv')
    
    if not csv_files:
        print("No CSV files found")
        return
    
    print("\nCSV File Statistics:")
    print("-" * 50)
    
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file)
            print(f"\nFile: {csv_file}")
            print(f"Number of entries: {len(df)}")
            print(f"Date range: {df['date_scraped'].min()} to {df['date_scraped'].max()}")
            print(f"File size: {os.path.getsize(csv_file) / 1024:.2f} KB")
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")

def load_json_database(json_path: str = 'listings_database.json') -> Dict[str, any]:
    """
    Load existing JSON database or create new one if it doesn't exist
    """
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading JSON database: {e}")
        return {}

def save_json_database(data: Dict[str, any], json_path: str = 'listings_database.json'):
    """
    Save updated database to JSON file
    """
    try:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving JSON database: {e}")

def update_json_database(listing_details: Dict[str, any]) -> bool:
    """
    Update JSON database with new listing details
    Returns True if update was successful, False if listing already exists
    """
    if not listing_details or 'link' not in listing_details:
        return False
    
    # Load existing database
    database = load_json_database()
    
    # Check if listing already exists
    if listing_details['link'] in database:
        return False
    
    # Add new listing
    database[listing_details['link']] = {
        k: v for k, v in listing_details.items() if k != 'link'
    }
    
    # Save updated database
    save_json_database(database)
    return True

def get_json_stats():
    """
    Print statistics about the JSON database
    """
    try:
        database = load_json_database()
        print("\nJSON Database Statistics:")
        print("-" * 50)
        print(f"Total listings: {len(database)}")
        
        # Get some basic stats
        prices = [entry['price'] for entry in database.values() if entry.get('price')]
        if prices:
            print(f"Price range: ${min(prices)} - ${max(prices)}")
            print(f"Average price: ${sum(prices)/len(prices):.2f}")
        
        # Count listings with images
        with_images = sum(1 for entry in database.values() if entry.get('num_images', 0) > 0)
        print(f"Listings with images: {with_images}")
        
        # File size
        file_size = os.path.getsize('listings_database.json') / 1024
        print(f"Database file size: {file_size:.2f} KB")
        
    except Exception as e:
        print(f"Error getting JSON statistics: {e}")

# Example usage
if __name__ == "__main__":
    # Example listing URL
    test_url = "https://vancouver.craigslist.org/example-listing"
    
    # Update CSV with new listing
    update_listings_csv(test_url)
    
    # Print statistics about all CSV files
    get_csv_stats()

    # Process multiple listings
    listings = [
        "https://vancouver.craigslist.org/listing1",
        "https://vancouver.craigslist.org/listing2"
    ]
    for listing in listings:
        update_listings_csv(listing)

    # Get statistics about both databases
    get_csv_stats()
    get_json_stats()

