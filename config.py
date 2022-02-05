from decouple import config


VK_TOKEN = config('VK_ACCESS_TOKEN', '')
VK_GROUP = config('VK_GROUP', '')
ERROR_KEY = 'error'


class VKError(Exception):
    """
    Базовое исключение для игры
    """
    pass


