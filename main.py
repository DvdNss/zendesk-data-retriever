import json
import os

from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm
from zenpy import Zenpy

# load .env
load_dotenv(find_dotenv())

try:
    os.mkdir('tickets')
except:
    pass

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=700, **creds)

tickets = zenpy_client.search(type='ticket')  # all tickets
# tickets = zenpy_client.search(type='ticket', tags=['galaxy'])  # galaxy tickets
# tickets = zenpy_client.search(type='ticket', tags=['flex'])  # flex tickets

print(f"\nTickets found: {len(tickets)}.\n")

# iterate through tickets
for ticket in tqdm(tickets, "Parsing tickets"):
    ticket = ticket.to_dict()

    # build our content
    output_dict = {
        'id': ticket.get('id'),
        'url': f"https://dalet.zendesk.com/agent/tickets/{ticket.get('id')}",
        'organization': zenpy_client.organizations(id=ticket.get('organization_id')).to_dict().get('name'),
        'product': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if custom_field.get('id') == 4827434148765][0],
        'version': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if custom_field.get('id') == 5706018204701][0],
        'platform_type': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if custom_field.get('id') == 4827478760349][0],
        'subject': ticket.get('subject'),
        'comments': sorted([
            {
                'created_at': comment.to_dict().get('created_at'),
                'author': zenpy_client.users(id=comment.to_dict().get('author_id')).to_dict().get('name'),
                'body': comment.to_dict().get('body')
            } for comment in zenpy_client.tickets.comments(ticket=ticket.get('id'))
        ], key=lambda x: x['created_at'])
    }

    # write to local folder
    with open(os.path.join("tickets", f"{ticket.get('id')}.json"), 'w') as json_to_save:
        json_to_save.write(json.dumps(output_dict, indent=4))
