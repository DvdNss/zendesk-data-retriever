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
file_handler = logging.FileHandler('Logs/AllticketsLogger.log')
file_handler.setLevel(logging.DEBUG)  # Set the logging level for this handler

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add file handler to the logger
logger.addHandler(file_handler)

try:
    os.mkdir('tickets/raw')
    os.mkdir('tickets/processed')
except:
    pass

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=600, **creds)

total_tickets = len(zenpy_client.search(type='ticket'))
logger.info(f"Total number of tickets is {total_tickets}")
print(f"Total number of tickets is {total_tickets}")

count_savedTickets = 0

def saveTickets(tickets, count_savedTickets=None):
    # iterate through tickets
    for ticket in tqdm(tickets, "Parsing tickets"):
        try:
            ticket = ticket.to_dict()

            # build our content
            output_dict = {
                'id': ticket.get('id'),
                'url': f"https://dalet.zendesk.com/agent/tickets/{ticket.get('id')}",
                'organization': zenpy_client.organizations(id=ticket.get('organization_id')).to_dict().get('name'),
                'product': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                            custom_field.get('id') == 4827434148765][0],
                'version': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                            custom_field.get('id') == 5706018204701][0],
                'platform_type': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                                  custom_field.get('id') == 4827478760349][0],
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

            # write to local folder

            # saving raw ticket in case we want it later
            with open(os.path.join("tickets/raw", f"{ticket.get('id')}.json"), 'w') as json_to_save:
                json_to_save.write(json.dumps(ticket, indent=4))

            # saving our processed ticket
            with open(os.path.join("tickets/processed", f"{ticket.get('id')}.json"), 'w') as json_to_save:
                json_to_save.write(json.dumps(output_dict, indent=4))

            count_savedTickets += 1

        except Exception as e:
            logger.error(f"An error occurred: {e}" + "for item " + str(ticket))
            continue

page_number = 1
page_size = 100  # Maximum page size allowed by Zendesk API

while True:
    page_tickets = zenpy_client.search(type='ticket', page=page_number, per_page=page_size)
    logger.info("page_number is " + str(page_number))
    print("page_number is " + str(page_number))

    if not page_tickets:
        print("No more tickets to fetch.")
        logger.info("No more tickets to fetch.")
        break

    saveTickets(page_tickets, count_savedTickets)
    page_number += 1
    print("Total tickets handled: ", count_savedTickets)
    logger.info("Total tickets handled: ", count_savedTickets)
