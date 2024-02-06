import json
import os

from dotenv import find_dotenv, load_dotenv
from zenpy import Zenpy

# load .env
load_dotenv(find_dotenv())

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

# this will retrieve **ALL** tickets
tickets = zenpy_client.search(type='ticket')
# galaxy_tickets = zenpy_client.search(type='ticket', tags=['galaxy'])
# flex_tickets = zenpy_client.search(type='ticket', tags=['flex'])

print(f"Tickets found: {len(tickets)}.")

# iterate through tickets
for ticket in tickets:
    # do your stuff here
    print(json.dumps(ticket.to_dict(), indent=4))
