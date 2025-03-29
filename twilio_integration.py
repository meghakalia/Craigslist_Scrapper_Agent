

from twilio.rest import Client

from dotenv import load_dotenv
from craigs_list_beatiful_sup import scrape_craigslist

import os
import time

# Load variables from .env
load_dotenv()

# Get credentials from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
my_number = os.getenv("MY_PHONE_NUMBER")


client = Client(account_sid, auth_token)

# scrape craigslist
links = scrape_craigslist()

# combined_body = "\n".join([f"Link {i+1}: {link}" for i, link in enumerate(links[:2])])


# Send each link in a separate message s
for i, link in enumerate(links, 1):
    message = client.messages.create(
        body=f"Link {i}: {link}",
        from_=twilio_number,
        to=my_number
    )
    print(f"Sent message {i}: SID={message.sid}")
    time.sleep(1)  # Optional: small delay to avoid hitting rate limits



# client = Client(account_sid, auth_token)
# message = client.messages.create(
#   from_=twilio_number,
#   body=combined_body,
#   to=my_number
# )
# print(message.sid)

# print(f"Message sent! SID: {message.sid}")
