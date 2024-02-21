import json
import os.path

from tqdm import tqdm

products = {
    'galaxy': 'galaxy',
    'flex': 'flex',
    'radio_suite': 'radio_suite',
    'brio': 'brio',
    'amberfin': 'amberfin',
    'other': 'other',
    'entreprise': 'enterprise',
    'cube': 'cube',
    'pyramid': 'pyramid',
    'dalet_galaxy': 'galaxy',
    'dalet_flex': 'flex',
    'dalet_cube': 'cube'
}

os.makedirs('models', exist_ok=True)

[os.makedirs(os.path.join('models', v), exist_ok=True) for k, v in products.items()]

if os.path.isdir('ingest'):
    for file in tqdm(os.listdir('ingest'), desc="Parsing tickets"):
        with open(os.path.join('ingest', file), 'r') as ticket_data:
            ticket = json.load(ticket_data)

        if ticket.get('product'):
            with open(os.path.join('models', products[ticket.get('product')], file), 'w') as f:
                f.write(json.dumps(ticket, indent=4))
