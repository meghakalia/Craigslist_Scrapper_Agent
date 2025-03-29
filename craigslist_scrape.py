

from craigslist import CraigslistHousing

cl = CraigslistHousing(site='vancouver')
print(cl.show_filters())

# Create a search object for sublets/temporary housing
cl_housing = CraigslistHousing(
    site='vancouver',
    area='van',
    category='sub',  # 'sub' is for sublets / temporary
    filters={
        'max_price': 1200,
        'availability_mode': 1,  # Only show listings with specific availability
    }
)

# Fetch and print top results
results = cl_housing.get_results(sort_by='newest', limit=10)

print("🔍 Sublet Listings in Vancouver (May, under $1200):\n")
for result in results:
    print(f"🏠 {result['name']}")
    print(f"💰 {result.get('price', 'N/A')}")
    print(f"🔗 {result['url']}\n")

