# Учебный проект devman "Публикация комиксов во Вконтакте"

### В VK создана группа [devmanVKComicsProject](https://vk.com/public210478891) 

При запуске программа публикует один случайный [комикс](https://xkcd.com) в 
заданной группе ВКонтакте.

### Зависимости
```
python-decouple==3.5
requests==2.26.0
```
### Переменные окружения
 - `VK_ACCESS_TOKEN=<value>` - токен для работы с VK API.
([получение токена](https://vk.com/dev/implicit_flow_user))
 - `VK_GROUP=<value>` - имя группы ВКонтакте, на стену которой будут размещаться комиксы. 
### Запуск скрипта
```
python get_comics.py 
```