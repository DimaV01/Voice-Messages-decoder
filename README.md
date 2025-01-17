# Телеграмм Бот для Распознавания Голосовых и Видео Сообщений
## Обзор
Этот скрипт создает Телеграмм-бота, который может обрабатывать голосовые и видео сообщения, отправленные ему. Бот использует библиотеку Telethon для взаимодействия с API Телеграмма и библиотеку SpeechRecognition для распознавания речи из голосовых и видео сообщений. Распознанный текст затем отправляется обратно пользователю в виде текстового сообщения.

## Функции
- Обрабатывает голосовые и видео сообщения, отправленные боту
- Распознает речь из сообщений с помощью SpeechRecognition
- Отправляет распознанный текст обратно пользователю в виде текстового сообщения
- Позволяет пользователям указать список разрешенных пользователей, которые могут отправлять сообщения боту
- Сохраняет конфигурацию бота и разрешенных пользователей в файле JSON
## Требования
- Python 3.7 или выше
- Библиотека Telethon 
- Библиотека SpeechRecognition 
- Библиотека Pydub 
- Библиотека Kivy 
- Библиотека g4f 
- Библиотека asyncio
- Библиотека threading
- Библиотека curl_cffi
- Библиотека moviepy
# Конфигурация
Конфигурация бота хранится в файле JSON под названием data.json. Этот файл содержит следующие настройки:

- api_id: ID API Телеграмм-бота
- api_hash: Хэш API Телеграмм-бота
- phone_number: Номер телефона аккаунта Телеграмма, который будет использоваться ботом
- allowed_users: Список имен пользователей, которым разрешено отправлять сообщения боту
## Использование
### Запуск Бота
Чтобы запустить бота, просто выполните скрипт с помощью Python:

```bash
python main.py
```
- Получить ваши api_id и api_hash [здесь](https://tlgrm.ru/docs/api/obtaining_api_id#:~:text=Для%20получения%20API%20id%20и,development%20tools'%20и%20заполнить%20форму.).
- Ввести данные
- Нажать кнопку "Старт"
Бот запустится и начнет слушать входящие сообщения.

## Лицензия
Этот скрипт распространяется под лицензией Apache. См. файл LICENSE для подробностей.

 
