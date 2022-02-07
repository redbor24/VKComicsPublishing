import json
import logging
import os
from pathlib import Path
from random import randint
from urllib.parse import urlparse

import requests

from config import VK_TOKEN, VK_GROUP, ERROR_KEY, VKError

logger = logging.getLogger()


def download_image(url, full_filename, params=None):
    headers = {
        'User-Agent': 'curl',
        'Accept-Language': 'ru-RU'
    }

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()

    with open(full_filename, 'wb') as file:
        file.write(resp.content)


def get_file_ext_from_url(url):
    return Path(urlparse(url).path).name


def get_max_comics_num():
    resp = requests.get('https://xkcd.com/info.0.json')
    resp.raise_for_status()
    parsed = resp.json()
    return parsed['num']


def get_random_comics():
    return get_comics(randint(1, get_max_comics_num()))


def get_comics(comics_number):
    path_for_save = Path('files')
    os.makedirs(path_for_save, exist_ok=True)
    resp = requests.get(f'https://xkcd.com/{comics_number}/info.0.json')
    resp.raise_for_status()
    parsed = resp.json()

    img_link = parsed['img']
    full_file_path = Path.cwd() / Path(path_for_save)
    file_ext = get_file_ext_from_url(img_link)
    full_filename = full_file_path / file_ext

    download_image(img_link, full_filename)
    return {
        'num': parsed['num'],
        'full_filename': full_filename,
        'title': parsed['title'],
        'comment': parsed['alt'],
    }


def do_vk_method(method, params):
    main_params = {
        'access_token': VK_TOKEN,
        'v': '5.81',
    }
    main_params = main_params | params

    resp = requests.get(f'https://api.vk.com/method/{method}',
                        params=main_params)
    resp.raise_for_status()
    parsed = resp.json()
    if ERROR_KEY in parsed:
        raise VKError({
            'error_code': parsed['error']['error_code'],
            'error_msg': parsed['error']['error_msg'],
            'method': method,
            'params': params,
        })
    return parsed


def get_vk_groups():
    return do_vk_method('groups.get', {'extended': '1'})


def get_group_id(groups, group_name):
    for group in groups['response']['items']:
        if group['name'] == group_name:
            return group['id']


def get_params_for_photos_upload(group_id):
    resp = do_vk_method('photos.getWallUploadServer', {'group_id': group_id})
    return resp['response']


def post_file(full_filename, url):
    with open(full_filename, 'rb') as file:
        files = {'photo': file}
        resp = requests.post(url, files=files)

    resp.raise_for_status()
    parsed = resp.json()
    if parsed['photo'] == '[]':
        raise Exception('Ошибка загрузки файла.'
                        ' Проверьте наименование метода и id группы,'
                        ' в которую вы хотите разместить картинку')
    return parsed


def post_photo_to_wall(group_id, vk_photo, server, hash, caption):
    method_params = {
        'group_id': group_id,
        'photo': vk_photo,
        'server': server,
        'hash': hash,
        'caption': caption
    }
    save_photo_resp = do_vk_method('photos.saveWallPhoto', method_params)
    save_photo_resp = save_photo_resp['response'][0]
    logger.info(f'save_photo_resp: {json.dumps(save_photo_resp, indent=4)}')
    return save_photo_resp


def post_comics_to_wall(group_id, message, owner_id, vk_photo_id):
    method_params = {
        'owner_id': f'-{group_id}',
        'message': message,
        'attachments': f'photo{owner_id}_{vk_photo_id}',
    }
    wall_post_resp = do_vk_method('wall.post', method_params)
    post_url = f'https://vk.com/wall-{group_id}_' \
               f'{wall_post_resp["response"]["post_id"]}'
    logger.info(f'wall.post: {json.dumps(wall_post_resp, indent=4)}')
    return wall_post_resp["response"]["post_id"], post_url


def post_comment(post_id, owner_id, comment):
    method_params = {
        'post_id': post_id,
        'owner_id': owner_id,
        'message': comment,
    }
    _ = do_vk_method('wall.createComment', method_params)
    logger.info(f'wall.createComment: {json.dumps(_, indent=4)}')


def post_comics(comics, group_id):
    upload_params = get_params_for_photos_upload(group_id)
    logger.info(f'upload_params: {json.dumps(upload_params, indent=4)}')
    post_file_resp = post_file(comics['full_filename'],
                               upload_params['upload_url'])
    logger.info(f'post_file_resp: {json.dumps(post_file_resp, indent=4)}')

    save_photo_resp = post_photo_to_wall(
        group_id,
        post_file_resp['photo'],
        post_file_resp['server'],
        post_file_resp['hash'],
        comics['title']
    )

    post_id, post_url = post_comics_to_wall(
        group_id,
        comics['title'],
        save_photo_resp['owner_id'],
        save_photo_resp['id']
    )

    if comics['comment']:
        post_comment(post_id, f'-{group_id}', comics['comment'])

    return post_url


if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    log_handler = logging.FileHandler('post_vk_comics.log', encoding='utf-8')
    log_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    logger.addHandler(log_handler)

    group = get_group_id(get_vk_groups(), VK_GROUP)
    if not group:
        err_msg = f'Ошибка! ВК-группа "{VK_GROUP}" не найдена.'
        logger.error(err_msg)
        print(err_msg)
        exit()

    # try:
    try:
        comics = get_random_comics()
        post_comics_link = post_comics(comics, group)
        print(f'Ссылка на опубликованный комикс: {post_comics_link}')
    except VKError as e:
        print(f'Ошибка размещения комикса на стене группы: {e}')
    finally:
        os.remove(comics['full_filename'])
