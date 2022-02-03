import os
from pathlib import Path
from urllib.parse import urlparse
import json

import requests


from config import VK_TOKEN


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

    img_link = parsed['img']
    full_filename = Path.cwd() / Path(path_for_save) / get_file_ext_from_url(img_link)
    download_image(img_link, full_filename)
    return {
        'full_filename': full_filename,
        'title': parsed['title'],
        'comment': parsed['alt'],
    }


def do_vk_method(method, add_params):
    params = {
        'access_token': VK_TOKEN,
        'v': '5.81',
    }
    params = params | add_params

    resp = requests.get(f'https://api.vk.com/method/{method}', params=params)
    resp.raise_for_status()
    return resp.json()


def get_vk_groups():
    return do_vk_method('groups.get', {'extended': '1'})


def get_group_id(groups, group_name):
    for group in groups['response']['items']:
        if group['name'] == group_name:
            return group['id']
    return None


def get_address_for_photos_upload(group_id):
    resp = do_vk_method('photos.getWallUploadServer', {'group_id': group_id})
    print(json.dumps(resp, indent=4))
    return resp['response']['upload_url']


def get_params_for_photos_upload(group_id):
    resp = do_vk_method('photos.getWallUploadServer', {'group_id': group_id})
    return resp['response']


def post_file(full_filename, url):
    with open(full_filename, 'rb') as file:
        files = {'photo': file}
        response = requests.post(url, files=files)
        response.raise_for_status()
        parsed = response.json()
        return None if not parsed['photo'] else parsed


def post_comics(comics, group_id):
    upload_params = get_params_for_photos_upload(group_id)
    print(f'upload_params: {json.dumps(upload_params, indent=4)}')
    # return
    post_file_resp = post_file(comics['full_filename'], upload_params['upload_url'])
    print(f'post_file_resp: {json.dumps(post_file_resp, indent=4)}')

    method_params = {
        # 'user_id': upload_params['user_id'],
        'group_id': group_id,
        'photo': post_file_resp['photo'],
        'server': post_file_resp['server'],
        'hash': post_file_resp['hash'],
        'caption': comics['title']
    }

    # print(f'method_params: {method_params}')
    # Сохраняем картинку на стену
    save_photo_resp = do_vk_method('photos.saveWallPhoto', method_params)
    save_photo_resp = save_photo_resp['response'][0]
    print('save_photo_resp:', json.dumps(save_photo_resp, indent=4))

    # Публикуем комикс на стене
    # method_params = {
    #     'owner_id': group_id,
    #     # 'owner_id': save_photo_resp['owner_id'],
    #     'message': comics['title'],
    #     'attachments': f"photo{save_photo_resp['owner_id']}_"
    #                    f"{save_photo_resp['id']}",
    #     # 'close_comments': '0',
    # }
    method_params = {
        'owner_id': group_id,
        'message': comics['title'],
        'attachments': f"photo{save_photo_resp['owner_id']}_"
                       f"{save_photo_resp['id']}",
    }
    print(f'method_params: {method_params}')
    resp = do_vk_method('wall.post', method_params)
    print(f'resp: {resp}')
    return resp['response']


if __name__ == '__main__':
    comics = get_comics(1)
    # print(comics_params)
    # exit()

    group_id = get_group_id(get_vk_groups(), 'devmanVKComicsProject')
    print(f'group_id: {group_id}')  # 210478891

    post_comics_resp = post_comics(comics, group_id)
    print(json.dumps(post_comics_resp, indent=4))


