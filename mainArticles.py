import json
import os

import requests
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
subdomain = creds['subdomain']

# rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)


# Retrieve all sections
sections = zenpy_client.help_center.sections()

# Iterate through the sections to fetch all pages
all_sections = []
for section in sections:
    all_sections.append(section)

categories = zenpy_client.help_center.categories().values

#Crating folders to save each article in its category
for category in categories:
    print (category.name)
    folder_name = f"articles/{category.name}"
    try:
        os.makedirs(folder_name, exist_ok=True)
        print(f"Created folder for category '{category.name}'")

    except:
        pass

articles = zenpy_client.help_center.articles()
def get_category_by_section_id(category_list, category_id):
    # Iterate through the section list
    for category in category_list:
        if category.id == category_id:
            # Return the categoryId of the section
            return category

    # Handle if section with given ID is not found
    return None

def get_ObjectInListById(objectList, ojectId):
    # Iterate through the section list
    for object in objectList:
        if object.id == ojectId:
            # Return the categoryId of the section
            return object

    # Handle if section with given ID is not found
    return None

#Zenpy has no built in way to retrieve article comments, will do it with a get request directly
def getArticleComments(articleId):
    # Get email and token from environment variables

    email = os.environ.get('ZD_EMAIL')
    token = os.environ.get('ZD_TOKEN')

    # Concatenate email and token to form the user string
    user = email + '/token'

    credentials = user, token
    url = f'https://{subdomain}.zendesk.com/api/v2/help_center/articles/{articleId}/comments.json'

    # Make the GET request
    response = requests.get(url, auth=credentials)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        comments = response.json()['comments']
        for comment in comments:
            print(f"Comment ID: {comment['id']}, Body: {comment['body']}")
    else:
        print(f"Failed to retrieve comments. Status code: {response.status_code}")
        return None

    return comments

for article in articles:
    categoryName = get_ObjectInListById(categories, article.section.category_id).name
    pathToSave = f"articles/{categoryName}"

    article = article.to_dict()

    sectionName = get_ObjectInListById(sections.values, article.get('section_id')).name

    # build our content
    output_dict = {
        'id': article.get('id'),
        'url': f"https://support.dalet.com/hc/en-us/articles/{article.get('id')}",
        'author': zenpy_client.users(id=article.get('author_id')).to_dict().get('name'),
        #'section': ticket.get('section'),
        'section': sectionName,
        'name': article.get('name'),
        'label_names': article.get('label_names'),
        'body': article.get('body'),
        'comments': sorted([
            {
                'created_at': comment.to_dict().get('created_at'),
                'author': zenpy_client.users(id=comment.to_dict().get('author_id')).to_dict().get('name'),
                'body': comment.to_dict().get('body')
            } for comment in getArticleComments(article.get('id'))
        ], key=lambda x: x['created_at'])
    }


    with open(os.path.join(pathToSave, f"{article.get('id')}.json"), 'w') as json_to_save:
        json_to_save.write(json.dumps(output_dict, indent=4))


