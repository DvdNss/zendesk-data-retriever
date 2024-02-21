import json
import os
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm
from zenpy import Zenpy

# load .env
load_dotenv(find_dotenv())

try:
    os.mkdir('raw')
    os.mkdir('ingest')
except:
    pass

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

# tickets = zenpy_client.search(type='ticket')  # all tickets
# tickets = zenpy_client.search(type='ticket', tags=['galaxy'])  # galaxy tickets
tickets = zenpy_client.search(
    type='ticket',
    # flex tickets
)

print(f"\nTickets found: {len(tickets)}.\n")

sum_tickets = 23229
failed_tickets = []
for year in [2018, 2019, 2020, 2021, 2022, 2023, 2024]:
    for month in [i for i in range(1, 13)]:
        # december? month 13 doesn't exist so check from 12 to 1 of next year
        if month == 12:
            tmp_year = year + 1
            tmp_month = 1

        # retrieve tickets month by month, because zendesk api sucks
        tickets = zenpy_client.search(
            type='ticket',
            # tags=['flex'],
            created_between=
            [
                datetime(year, month, 1),
                datetime(year if month != 12 else tmp_year, month + 1 if month != 12 else tmp_month, 1)
            ]
        )

        # sum
        sum_tickets += len(tickets)

        # iterate through tickets
        for ticket in tqdm(tickets, f"Parsing tickets for {year}-{month} [sum: {sum_tickets}]"):
            ticket = ticket.to_dict()
            comments = sorted(
                [
                    comment.to_dict() for comment in zenpy_client.tickets.comments(ticket=ticket.get('id'))
                ], key=lambda x: x['created_at']
            )

            try:
                # raw format
                raw = ticket.copy()
                raw['comments'] = comments

                # ingest format
                ingest = {
                    'id': ticket.get('id'),
                    'url': f"https://dalet.zendesk.com/agent/tickets/{ticket.get('id')}",
                    'organization': zenpy_client.organizations(id=ticket.get('organization_id')).to_dict().get('name') if ticket.get('organization_id') else None,
                    'product': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                                custom_field.get('id') == 4827434148765][0],
                    'version': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                                custom_field.get('id') == 5706018204701][0],
                    'platform_type': [custom_field.get('value') for custom_field in ticket.get('custom_fields') if
                                      custom_field.get('id') == 4827478760349][0],
                    'subject': ticket.get('subject'),
                    'comments': [
                        {
                            'created_at': comment.get('created_at'),
                            'author': zenpy_client.users(id=comment.get('author_id')).to_dict().get('name'),
                            'body': comment.get('body')
                        } for comment in comments
                    ]
                }

                # save
                for k, v in {'raw': raw, 'ingest': ingest}.items():
                    with open(os.path.join(k, f"{ticket.get('id')}.json"), 'w') as json_to_save:
                        json_to_save.write(json.dumps(v, indent=4))
            except:
                failed_tickets.append(ticket.get('id'))
                print(f"Skipping ticket {ticket.get('id')}...")
print(sum_tickets)
print(f"Failed tickets: {failed_tickets}")
