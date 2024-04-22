import os
import uuid
import requests
from .settings import SLACK_BOT_TOKEN


def process_files(files):
    processed_files = []
    for file in files:
        filetype = file.get('filetype', None)
        if filetype == 'csv':
            processed_files.append(process_csv(file))
        else:
            print('----- Tipo de arquivo ainda não parametrizado -----')
            print(file)
            print('---------------------------------------------------')
    return processed_files


def process_csv(file):
    name = file.get('name', None)
    url_private = file.get('url_private_download', None)
    headers = {'Authorization': 'Bearer {}'.format(SLACK_BOT_TOKEN)}
    r = requests.get(url_private, allow_redirects=True, headers=headers)
    filename = 'media/{}_{}'.format(uuid.uuid4().hex, name)
    check_if_folder_exists(filename)
    open(filename, 'wb').write(r.content)
    return filename


def check_if_folder_exists(filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
