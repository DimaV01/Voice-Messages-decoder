import os
import asyncio
import threading
import json
import shutil
import g4f
import curl_cffi, nest_asyncio
from telethon import TelegramClient, events
from moviepy.editor import VideoFileClip
from speech_recognition import Recognizer, AudioFile
from pydub import AudioSegment
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.splitter import Splitter
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics.context_instructions import Color

# Путь для сохранения медиа файлов
download_path = './downloads'

# Инициализация Telethon клиента
client = None

recognizer = Recognizer()

def punctuate_text(text):
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_4o_mini,
        messages=[
            {"role": "system", "content": "You are an assistant that helps with text punctuation. You can ONLY punctuate text."},
            {"role": "user", "content": f"Please punctuate the following text: {text}"}
        ]
    )
    bot_reply = ""               
    for message in response:
        bot_reply += message
        
    return bot_reply

def convert_to_wav(file_path):
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_path, format='wav')
    return wav_path

async def process_voice_message(event):
    sender = await event.get_sender()
    sender_id = sender.id
    sender_name = sender.username if sender.username else "Пользователь"

    file_path = await event.message.download_media(download_path)
    try:
        wav_path = convert_to_wav(file_path)
        audio = AudioFile(wav_path)

        with audio as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='ru-RU')
                punctuated_text = punctuate_text(text)
                await client.send_message(sender_id, f'Распознанное сообщение от {sender_name}:\n\n{punctuated_text}', reply_to=event.message.id)
            except Exception as e:
                await client.send_message(sender_id, f'Не удалось распознать сообщение: {e}', reply_to=event.message.id)
    finally:
        # Удаление файлов после обработки
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
async def process_video_message(event):
    sender = await event.get_sender()
    sender_id = sender.id
    sender_name = sender.username if sender.username else "Пользователь"

    file_path = await event.message.download_media(download_path)
    try:
        video = VideoFileClip(file_path)
        audio_path = file_path.replace('.mp4', '.wav')
        video.audio.write_audiofile(audio_path)
        video.close()

        wav_path = convert_to_wav(audio_path)
        audio = AudioFile(wav_path)
        with audio as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language='ru-RU')
                punctuated_text = punctuate_text(text)
                await client.send_message(sender_id, f'Распознанное сообщение от {sender_name}:\n\n{punctuated_text}', reply_to=event.message.id)
            except Exception as e:
                await client.send_message(sender_id, f'Не удалось распознать сообщение: {e}', reply_to=event.message.id)
    finally:
        # Удаление файлов после обработки
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

def create_downloads_folder():
    if not os.path.exists(download_path):
        os.makedirs(download_path)

def delete_downloads_folder():
    try:
        if os.path.exists(download_path):
            shutil.rmtree(download_path)
    except Exception as e:
        print(f'Не удалось удалить папку {download_path}. Причина: {e}')

class ColoredBoxLayout(BoxLayout):
    def __init__(self, rect_color=(0/255, 1/255, 43/255, 1), **kwargs):
        super().__init__(**kwargs)
        self.rect_color = rect_color  # Использование переданного цвета
        with self.canvas.before:
            Color(*self.rect_color)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos

class MyApp(App):
    def __init__(self, **kwargs):
        super(MyApp, self).__init__(**kwargs)
        self.client_initialized = False
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.bot_running = False
        self.allowed_users = []
        self.users_input = None
        self.shared_label = Label(text='Начальный текст', font_size='24sp', bold=True, size_hint_y=None, height=40)
    
    async def connect_client(self):
        global client
        client = TelegramClient('VMD', self.api_id_input.text, self.api_hash_input.text, system_version='4.16.30-vxCUSTOM')
        await client.connect()
        if await client.is_user_authorized():
            username = await self.get_username()
            self.label.text = f"Вход выполнен! Пользователь: {username}"
        else:
            client = None
    
    def build(self):
        # Главный вертикальный макет
        layout = ColoredBoxLayout(orientation='vertical', padding=10, spacing=10, rect_color=(0/255, 1/255, 20/255, 1))
        
        # Создание панели вкладок
        tab_panel = TabbedPanel(do_default_tab=False)
        
        # Вкладка для настроек подключения
        settings_tab = TabbedPanelItem(background_color=(54/255, 255/255, 255/255, 1), background_normal='res/settings_icon.png', background_down='res/settings_icon_active.png')
        settings_layout = self.build_settings_layout()
        settings_tab.add_widget(settings_layout)
        tab_panel.add_widget(settings_tab)

        # Вкладка для ввода пользователей
        users_tab = TabbedPanelItem(text='', background_color=(54/255, 255/255, 255/255, 1), background_normal='res/users_icon.png', background_down='res/users_icon_active.png')
        users_layout = self.build_users_layout()
        users_tab.add_widget(users_layout)
        tab_panel.add_widget(users_tab)
        
        layout.add_widget(tab_panel)
        
        self.load_data()
        
        if os.path.exists('VMD.session'):
            try:
                asyncio.run_coroutine_threadsafe(self.connect_client(), self.loop).result()
            except Exception as e:
                self.label.text = f"Ошибка при восстановлении сессии: {e}"
                
        return layout
    
    def build_users_layout(self):
        layout = ColoredBoxLayout(orientation='vertical', padding=10, spacing=10)

        self.label_users = Label(text='Слушать сообщения от:', font_size='24sp', bold=True, size_hint_y=None, height=40)
        layout.add_widget(self.label_users)

        self.users_input = TextInput(hint_text='Введите имена пользователей через запятую', multiline=True, background_color=(0/255, 6/255, 173/255, 1), foreground_color=(1,1,1,1), hint_text_color=(94/255, 96/255, 173/255, 1))
        layout.add_widget(self.users_input)

        self.save_users_button = Button(text='Сохранить пользователей', halign='center', valign='middle', background_color=(54/255, 151/255, 255/255, 1))
        self.save_users_button.bind(on_press=self.save_allowed_users)
        layout.add_widget(self.save_users_button)

        return layout
    
    def save_allowed_users(self, instance):
        if self.bot_running:
            self.label_users.text = 'Сначала остановите работу бота!'
            return
        
        users_text = self.users_input.text
        if users_text:
            self.allowed_users = [username.strip() for username in users_text.split(',')]
        else:
            self.allowed_users = []
        self.save_data()
    
    def build_settings_layout(self):     
        # Главный вертикальный макет
        layout = ColoredBoxLayout(orientation='vertical', padding=10, spacing=10)

        # Заголовок
        self.label = Label(text='Телеграм Клиент', font_size='24sp', bold=True, size_hint_y=None, height=40)
        layout.add_widget(self.label)

        # Разделитель
        layout.add_widget(Splitter(height=2, size_hint_y=None))

        # Ввод API ID
        self.api_id_input = TextInput(hint_text='API ID', multiline=False, background_color=(0/255, 6/255, 173/255, 1), foreground_color=(1,1,1,1), hint_text_color=(94/255, 96/255, 173/255, 1))
        layout.add_widget(self.api_id_input)

        # Ввод API Hash
        self.api_hash_input = TextInput(hint_text='API Hash', multiline=False, background_color=(0/255, 6/255, 173/255, 1), foreground_color=(1,1,1,1), hint_text_color=(94/255, 96/255, 173/255, 1))
        layout.add_widget(self.api_hash_input)

        # Разделитель
        layout.add_widget(Splitter(height=2, size_hint_y=None))

        # Горизонтальный макет для номера телефона и кнопки отправки кода
        phone_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.phone_number_input = TextInput(hint_text='Номер телефона', multiline=False, background_color=(0/255, 6/255, 173/255, 1), foreground_color=(1,1,1,1), hint_text_color=(94/255, 96/255, 173/255, 1))
        phone_layout.add_widget(self.phone_number_input)
        self.send_code_button = Button(text='Отправить код', size_hint_x=None, width=150, halign='center', valign='middle', background_color=(36/255, 41/255, 199/255, 1))
        self.send_code_button.bind(on_press=self.send_verification_code_wrapper)
        phone_layout.add_widget(self.send_code_button)
        layout.add_widget(phone_layout)

        # Горизонтальный макет для кода верификации и кнопки верификации
        code_layout = BoxLayout(orientation='horizontal', spacing=10)
        self.code_input = TextInput(hint_text='Код верификации', multiline=False, background_color=(0/255, 6/255, 173/255, 1), foreground_color=(1,1,1,1), hint_text_color=(94/255, 96/255, 173/255, 1))
        code_layout.add_widget(self.code_input)
        self.verify_code_button = Button(text='Верифицировать\nкод', size_hint_x=None, width=150, halign='center', valign='middle', background_color=(36/255, 41/255, 199/255, 1))
        self.verify_code_button.bind(on_press=self.verify_code_wrapper)
        code_layout.add_widget(self.verify_code_button)
        layout.add_widget(code_layout)

        # Разделитель
        layout.add_widget(Splitter(height=2, size_hint_y=None))

        # Горизонтальный макет для кнопок запуска бота и выхода
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=100)
        self.start_button = Button(text='Запустить Бота', halign='center', valign='middle', background_color=(54/255, 151/255, 255/255, 1))
        self.start_button.bind(on_press=self.toggle_bot)
        button_layout.add_widget(self.start_button)

        self.logout_button = Button(text='Выйти', halign='center', valign='middle', background_color=(255/255, 80/255, 0/255, 1))
        self.logout_button.bind(on_press=self.log_out)
        button_layout.add_widget(self.logout_button)

        layout.add_widget(button_layout)

        return layout
    
    async def get_username(self):
        global client
        if client:
            me = await client.get_me()
            return me.username
        else:
            return None
    
    def toggle_bot(self, instance):
        if self.bot_running:
            self.stop_bot()
            self.start_button.text = 'Запустить Бота'
            self.start_button.background_color = (54/255, 151/255, 255/255, 1)
        else:
            if os.path.exists('VMD.session') and not os.path.exists('VMD.session-journal'):
                asyncio.run_coroutine_threadsafe(self.connect_client(), self.loop).result()
                
            if not os.path.exists('VMD.session'):
                self.label.text = 'Пользователь не верифицирован. Пожалуйста, выполните вход.'
                return

            is_verified = asyncio.run_coroutine_threadsafe(self.is_user_verified(), self.loop).result()
            if is_verified:
                self.start_bot_wrapper(instance)
                self.start_button.text = 'Остановить Бота'
                self.start_button.background_color = (255/255, 0/255, 0/255, 1)
            else:
                self.label.text = 'Пользователь не верифицирован. Пожалуйста, выполните вход.'
    
    async def is_user_verified(self):
        global client
        if client:
            return await client.is_user_authorized()
        return False

    async def start_bot(self, instance):
        create_downloads_folder() 
        self.load_data()
        
        @client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if not event.is_private:
                return
            
            sender = await event.get_sender()
            sender_username = sender.username

            if self.allowed_users and sender_username not in self.allowed_users:
                return
            
            if event.message.voice:
                await process_voice_message(event)
            elif event.message.video:
                await process_video_message(event)

        self.label.text = 'Бот Запущен. Ожидание сообщений...'
        self.bot_running = True
        await client.run_until_disconnected()

    def start_bot_wrapper(self, instance):
        asyncio.run_coroutine_threadsafe(self.start_bot(instance), self.loop)

    async def send_verification_code(self, instance):
        global client
        api_id = self.api_id_input.text
        api_hash = self.api_hash_input.text
        phone_number = self.phone_number_input.text
        
        is_verified = await self.is_user_verified()
        if is_verified:
            self.label.text = 'Вы уже авторизованы!'
            return
        
        if not api_id or not api_hash or not phone_number:
            self.label.text = 'Введите данные!'
            return
        
        client = TelegramClient('VMD', api_id, api_hash, system_version='4.16.30-vxCUSTOM')
        await client.connect() 
         
        try:
            await client.send_code_request(phone_number)
            self.label.text = 'Код отправлен. Введите код верификации.'
        except Exception as e:
            self.label.text = f"Ошибка отправки кода: {e}"
        
    def send_verification_code_wrapper(self, instance):
        asyncio.run_coroutine_threadsafe(self.send_verification_code(instance), self.loop)

    async def verify_code(self, instance):
        global client
        phone_number = self.phone_number_input.text
        code = self.code_input.text
        
        is_verified = await self.is_user_verified()
        if is_verified:
            self.label.text = 'Вы уже авторизованы!'
            return
        
        if not phone_number or not code:
            self.label.text = 'Введите данные!'
            return
        
        try:
            await client.sign_in(phone_number, code)
            self.client_initialized = True
            username = await self.get_username()
            self.label.text = f"Вход выполнен! Пользователь: {username}"
        except Exception as e:
            self.label.text = f"Ошибка верификации кода: {e}"
    
    def verify_code_wrapper(self, instance):
        asyncio.run_coroutine_threadsafe(self.verify_code(instance), self.loop)

    def load_data(self):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                self.api_id_input.text = data['api_id']
                self.api_hash_input.text = data['api_hash']
                self.phone_number_input.text = data['phone_number']
                self.allowed_users = data.get('allowed_users', [])
                self.users_input.text = ', '.join(self.allowed_users)
        except FileNotFoundError:
            self.label.text = f"Файл data.json не найден"

    def save_data(self):
        data = {
            'api_id': self.api_id_input.text,
            'api_hash': self.api_hash_input.text,
            'phone_number': self.phone_number_input.text,
            'allowed_users': self.allowed_users
        }
        with open('data.json', 'w') as f:
            json.dump(data, f)

    def stop_bot(self):
        global client
        if client:
            asyncio.run_coroutine_threadsafe(self._disconnect_client(), self.loop).result()
        self.bot_running = False
        self.label.text = 'Бот остановлен.'
        self.label_users.text = 'Слушать сообщения от:'
        delete_downloads_folder()

    async def _disconnect_client(self):
        global client
        if client:
            await client.disconnect()

    def log_out(self, instance):
        try:
            if os.path.exists('VMD.session'):
                self.stop_bot()
                os.remove('VMD.session')
                self.label.text = 'Вы вышли из аккаунта.'
            return
            
        except Exception as e:
            self.label.text = f"Завершите работу бота: {e}"
    
    def on_stop(self):
        self.stop_bot()
        self.save_data()
        delete_downloads_folder()

if __name__ == '__main__':
    MyApp().run()