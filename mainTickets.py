import json
import os

from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm
from zenpy import Zenpy
import logging

# load .env
load_dotenv(find_dotenv())

# Create logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Create file handler and set its logging level
file_handler = logging.FileHandler('Logs/ticketsLogger.log')
file_handler.setLevel(logging.DEBUG)  # Set the logging level for this handler

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add file handler to the logger
logger.addHandler(file_handler)

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
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

# Define an empty list to store all tickets
all_tickets = []

# Initialize page number
page_number = 1

while True:
    # Fetch tickets for the current page
    page_tickets = zenpy_client.search(type='ticket', tags=['galaxy'], page=page_number)
    # tickets = zenpy_client.search(type='ticket')  # all tickets
    # tickets = zenpy_client.search(type='ticket', tags=['flex'])  # flex tickets

    # Append fetched tickets to the list of all tickets
    all_tickets.extend(page_tickets)

    # Check if there are more pages
    if len(page_tickets) < 100:  # If less than 100 tickets on the page, it's the last page
        break

    # Move to the next page
    page_number += 1

# Now all_tickets list contains all tickets
print("Total number of tickets:", len(all_tickets))

# iterate through tickets
for ticket in tqdm(all_tickets, "Parsing tickets"):
    try:
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

        logger.info(f"Saving JSON for article id {ticket.get('id')}")
        print(f"Saving Json for article id {ticket.get('id')}")
        # write to local folder
        with open(os.path.join("tickets", f"{ticket.get('id')}.json"), 'w') as json_to_save:
            json_to_save.write(json.dumps(output_dict, indent=4))


    except Exception as e:
        logger.error(f"An error occurred: {e}" + "for item " + str(ticket))
        continue