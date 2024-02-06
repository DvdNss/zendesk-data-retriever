import json
import os

from dotenv import find_dotenv, load_dotenv
from zenpy import Zenpy

load_dotenv(find_dotenv())

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

tickets = zenpy_client.search(type='ticket', tags=['galaxy'])

print(len(tickets))

for ticket in tickets:
    print(json.dumps(ticket.to_dict(), indent=4))
    break
