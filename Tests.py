from dotenv import find_dotenv, load_dotenv
from zenpy import Zenpy
import os

# load .env
load_dotenv(find_dotenv())

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=700, **creds)

article = zenpy_client.help_center.articles(id=9073079217181)

comments = # Construct the URL
url = f'https://dalet.zendesk.com/api/v2/help_center/articles/9073079217181/comments.json'


