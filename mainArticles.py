import json
import os
import logging
import requests
from dotenv import find_dotenv, load_dotenv
from zenpy import Zenpy

# Load .env
load_dotenv(find_dotenv())

# Create logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Create file handler and set its logging level
file_handler = logging.FileHandler('articlesLogger.log')
file_handler.setLevel(logging.DEBUG)  # Set the logging level for this handler

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add file handler to the logger
logger.addHandler(file_handler)

# Try to create 'articles' directory
try:
    os.mkdir('articles')
    logger.info("Created 'articles' directory")
except FileExistsError:
    logger.debug("'articles' directory already exists")

creds = {
    'email': os.environ.get('ZD_EMAIL'),
    'token': os.environ.get('ZD_TOKEN'),
    'subdomain': os.environ.get('ZD_SUBDOMAIN')
}

subdomain = creds['subdomain']

# Get email and token from environment variables
email = os.environ.get('ZD_EMAIL')
token = os.environ.get('ZD_TOKEN')

# Concatenate email and token to form the user string
user = email + '/token'

credentials = user, token

# Rate limiting of 200
zenpy_client = Zenpy(proactive_ratelimit=200, **creds)

# We will filter the attachment types to download to only what is useful for privateGPT (pdf, doc, xml, xsl, xslt, docx, csv, htm, html, dot, odt, txt)
# list here https://zappysys.zendesk.com/hc/en-us/articles/360034303774-Which-Content-Type-is-used-for-Multi-Part-Upload-File-Extension
usefulAttachmentTypes = ['application/pdf', 'application/msword', 'text/xml', 'application/xml', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'text/html', 'html', 'application/msword', 'application/vnd.oasis.opendocument.text', 'text/plain']

# Retrieve all sections
sections = zenpy_client.help_center.sections()

# Iterate through the sections to fetch all pages
all_sections = []
for section in sections:
    all_sections.append(section)

categories = zenpy_client.help_center.categories().values

# Creating folders to save each article in its category
for category in categories:
    logger.info(f"Creating folder for category '{category.name}'")
    folder_name = f"articles/{category.name}"
    subfolder1 = f"articles/{category.name}/json"
    subfolder2 = f"articles/{category.name}/attachments"

    try:
        os.makedirs(folder_name, exist_ok=True)
        os.makedirs(subfolder1, exist_ok=True)
        os.makedirs(subfolder2, exist_ok=True)
        logger.debug(f"Created folders for category '{category.name}'")

    except FileExistsError:
        logger.debug(f"Folder for category '{category.name}' already exists")

articles = zenpy_client.help_center.articles()


def get_ObjectInListById(objectList, object_id):
    # Iterate through the object list
    for object in objectList:
        if object.id == object_id:
            # Return the object if found
            return object

    # Return None if object with given ID is not found
    return None


# Zenpy has no built-in way to retrieve article comments, will do it with a GET request directly
def get_article_comments(article_id):
    url = f'https://{subdomain}.zendesk.com/api/v2/help_center/articles/{article_id}/comments.json'

    # Make the GET request
    response = requests.get(url, auth=credentials)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        comments = response.json()['comments']
        for comment in comments:
            logger.info(f"Comment ID: {comment['id']}, Body: {comment['body']}")
    else:
        logger.error(f"Failed to retrieve comments for article {article_id}. Status code: {response.status_code}")
        return None

    return comments


def get_attachment(article_id):
    endpoint_attachments = f'https://{subdomain}.zendesk.com/api/v2/help_center/articles/{article_id}/attachments'

    response = requests.get(endpoint_attachments, auth=credentials)
    if response.status_code != 200:
        logger.error(f"Failed to retrieve attachments for article {article_id}. Error code: {response.status_code}")
        return None

    data_attachments = response.json()
    return data_attachments


def download_file(url, destination):
    response = requests.get(url, auth=credentials)
    if response.status_code == 200:
        with open(destination, 'wb') as file:
            file.write(response.content)
        logger.info(f"File downloaded and saved at {destination}")
    else:
        logger.error(f"Failed to download file from {url}. Status code: {response.status_code}")


for article in articles:
    try:
        category_name = get_ObjectInListById(categories, article.section.category_id).name
        path_to_save_json = f"articles/{category_name}/json"

        article = article.to_dict()

        # Build content
        output_dict = {
            'id': article.get('id'),
            'url': f"https://support.dalet.com/hc/en-us/articles/{article.get('id')}",
            'author': zenpy_client.users(id=article.get('author_id')).to_dict().get('name'),
            'section': get_ObjectInListById(sections.values, article.get('section_id')).name,
            'name': article.get('name'),
            'label_names': article.get('label_names'),
            'body': article.get('body'),
            'comments': sorted([
                {
                    'created_at': comment.get('created_at'),
                    'author': zenpy_client.users(id=comment.get('author_id')).to_dict().get('name'),
                    'body': comment.get('body')
                } for comment in get_article_comments(article.get('id'))
            ], key=lambda x: x['created_at'])
        }

        logger.info(f"Saving JSON for article id {article.get('id')}")
        print(f"Saving Json for article id {article.get('id')}")
        with open(os.path.join(path_to_save_json, f"{article.get('id')}.json"), 'w') as json_to_save:
            json_to_save.write(json.dumps(output_dict, indent=4))

        # Download attachments of article
        attachments = get_attachment(article.get('id'))
        if attachments:
            for attachment in attachments['article_attachments']:
                if not attachment['content_type'] in usefulAttachmentTypes:
                    continue

                path_to_save_attachment = f"articles/{category_name}/attachments"
                filename = attachment['file_name']
                destination = os.path.join(path_to_save_attachment, filename)
                url_attachment = 'https://support.dalet.com/hc/en-us/article_attachments/' + str(
                    attachment['id'])
                download_file(url_attachment, destination)

    except Exception as e:
        logger.error(f"An error occurred: {e}" + "for item " + str(article))
        continue
