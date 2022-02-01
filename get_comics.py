from datetime import datetime
import os
from pathlib import Path
from urllib import parse
from urllib.parse import urlparse
import json

import requests


def download_image(url, full_filename, params=None):
    headers = {
        'User-Agent': 'curl',
        'Accept-Language': 'ru-RU'
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    with open(full_filename, 'wb') as file:
        file.write(response.content)


def get_file_ext_from_url(url):
    return Path(urlparse(url).path).name


def get_comics(comics_number):
    path_for_save = Path('files') / str(comics_number)
    os.makedirs(path_for_save, exist_ok=True)
    resp = requests.get(
        f'https://xkcd.com/{comics_number}/info.0.json',
    )
    resp.raise_for_status()
    parsed = resp.json()
    # print(json.dumps(parsed, indent=4))
    img_link = parsed['img']
    full_filename = Path.cwd() / Path(path_for_save) / get_file_ext_from_url(img_link)
    download_image(img_link, full_filename)
    return full_filename, parsed['title'], parsed['alt']


if __name__ == '__main__':
    print(get_comics(1))
