import json
import os

from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm
from zenpy import Zenpy

# load .env
load_dotenv(find_dotenv())

try:
    os.mkdir('articles')
except:
    pass

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

articles = zenpy_client.get_articles()

print(f"\nArticles found: {len(articles)}.\n")

# iterate through articles
for article in tqdm(articles, "Parsing articles"):
    article = article.to_dict()

    # build our content
    output_dict = {
        'id': article.get('id'),
        'url': f"https://dalet.zendesk.com/hc/en-us/articles/{article.get('id')}",
        'title': article.get('title'),
        'body': article.get('body'),
        # Add more fields as needed
    }

    # write to local folder
    with open(os.path.join("articles", f"{article.get('id')}.json"), 'w') as json_to_save:
        json_to_save.write(json.dumps(output_dict, indent=4))