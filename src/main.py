from telegram.ext import ConversationHandler
import telebot
from telebot import types
import sqlite3
import os
import datetime
import requests
import json
import logging
import time
from dotenv import load_dotenv

#Загрузка переменных окружения из .env файла
load_dotenv()

# --- Конфигурация YandexGPT ---
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
YANDEX_GPT_MODEL = os.getenv('YANDEX_GPT_MODEL')

# --- конфиг hh ---
HH_API_URL = os.getenv('HH_API_URL')
HH_COMPANY_ID = os.getenv('HH_COMPANY_ID')

# URL API YandexGPT
YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Заголовки для запроса
YANDEX_HEADERS = {
    "Authorization": f"Bearer {YANDEX_API_KEY}",  
    "x-folder-id": YANDEX_FOLDER_ID,
    "Content-Type": "application/json"
}

API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

DATABASE_NAME = os.getenv('DATABASE_NAME')

#соединение с бдй
conn = None
cursor = None

#Обработчики Команд и Текста 
@bot.message_handler(commands=["start"])
def handle_start(message):
    if not cursor or not conn: # Проверка, что БД инициализирована
        bot.send_message(message.chat.id, "Бот временно недоступен, проблема с базой данных. Попробуйте позже.")
        return
    # Отправляем изображение 
    try:
        with open("src/RODANIKA.jpg", "rb") as photo:
            # Текст под изображением
            caption = """
            <b>Добро пожаловать в HR-бот компании Rodanika!</b>
            <b>Я ваш персональный помощник по кадровым вопросам.</b>
            """
            caption = "\n".join(line.strip() for line in caption.splitlines())  # Убираем пробелы в начале каждой строки
            # Отправка фото с подписью (parse_mode для форматирования текста)
            bot.send_photo(
                chat_id = message.chat.id,
                photo = photo,
                caption = caption,
                parse_mode = "HTML"
            )
            
    except FileNotFoundError:
        print("Изображение 'src/RODANIKA.jpg' не найдено")
        # Отправляем только текст, если изображение не найдено
        bot.send_message(
        message.chat.id,
       bot.send_message(
       message.chat.id,
            f"<b>Привет, {registered_name}!</b>\nЯ HR-бот компании Rodanika. Чем могу помочь?",
            parse_mode="HTML",
            reply_markup=main_reply_markup)
)
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name if message.from_user.first_name else "Гость" # На случай если имя не указано
    username = message.from_user.username

    try:
        cursor.execute("SELECT registered_name FROM users WHERE telegram_id = ?", (telegram_id,))
        user_data = cursor.fetchone()

        if user_data and user_data[0]: # Проверка что registered_name не None и не пустая строка
            registered_name = user_data[0]
            bot.send_message(
            message.chat.id,
                f"<b>Привет, {registered_name}! Чем могу помочь?</b>",
                parse_mode="HTML",
                reply_markup=main_reply_markup
)
        else:
            # Если пользователь есть, но имя не зарегистрировано, или новый пользователь
            cursor.execute("""
                INSERT INTO users (telegram_id, first_name, username)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username
            """, (telegram_id, first_name, username))
            conn.commit()
            bot.send_message(message.chat.id,
                             f"Здравствуйте, {first_name}! Добро пожаловать в HR-бот компании Rodanika. "
                             "Чтобы я мог обращаться к вам удобнее, подскажите, как вас зовут (имя или имя и фамилия)?")
            bot.register_next_step_handler(message, process_name_step)
    except sqlite3.Error as e:
        print(f"Ошибка SQLite в /start: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")

def process_name_step(message):
    if not cursor or not conn:
        bot.send_message(message.chat.id, "Бот временно недоступен, проблема с базой данных. Попробуйте позже.")
        return
    try:
        telegram_id = message.from_user.id
        registered_name = message.text.strip()

        if not registered_name: # Проверка на пустой ввод
            bot.send_message(message.chat.id, "Имя не может быть пустым. Пожалуйста, введите ваше имя.")
            bot.register_next_step_handler(message, process_name_step)
            return

        if registered_name.startswith('/'): # Проверка, чтобы имя не было командой
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное имя, а не команду.")
            bot.register_next_step_handler(message, process_name_step)
            return

        cursor.execute("UPDATE users SET registered_name = ? WHERE telegram_id = ?", (registered_name, telegram_id))
        conn.commit()
        bot.send_message(message.chat.id,
                         f"Отлично, {registered_name}! Я запомнил ваше имя. Чем могу помочь?",
                         reply_markup=main_reply_markup) # Показ основной клавиатуры

    except sqlite3.Error as e:
        print(f"Ошибка SQLite в process_name_step: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при сохранении вашего имени. Попробуйте позже.")
    except Exception as e: # Ловим другие возможные ошибки
        print(f"Непредвиденная ошибка в process_name_step: {e}")
        bot.send_message(message.chat.id, "Что-то пошло не так при обработке вашего имени. Пожалуйста, попробуйте еще раз.")


@bot.message_handler(func=lambda message: message.text.lower() in ['привет', 'привет!', 'здравствуй', 'здравствуйте', 'hi', 'hello'])
def handle_greeting(message):
    # Отправляем приветственное сообщение
    greeting_text = f"""
<b>Привет, {message.from_user.first_name}!</b> 👋

Я HR-бот компании Rodanika. Вот что я могу для вас сделать:
"""
    bot.send_message(message.chat.id, greeting_text, parse_mode="HTML")
    
    # Отправляем изображение (необязательно)
    try:
        with open("src/RODANIKA.jpg", "rb") as photo:
            bot.send_photo(message.chat.id, photo)
    except FileNotFoundError:
        pass
    
    # Показываем основную клавиатуру
    bot.send_message(
        message.chat.id,
        "Выберите нужный раздел:",
        reply_markup=main_reply_markup
    )

def create_back_button_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = types.KeyboardButton("Назад")
    keyboard.add(back_button)
    return keyboard

#Инициализация Базы Данных 
def init_db():
    global conn, cursor
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
#таблица для пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        first_name TEXT,
        username TEXT,
        registered_name TEXT
    )
""")
    
    # Таблица для запросов документов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS document_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        additional_info TEX
                   T,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        estimated_completion TEXT,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )
    """)
    

  
# Таблица для новостей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hr_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(hr_id) REFERENCES users(telegram_id)
    )
    """)

# Таблица для подписчиков новостей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS news_subscribers (
        user_id INTEGER PRIMARY KEY,
        subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )
    """)

#Таблица для прав HR 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hr_rights (
        user_id INTEGER PRIMARY KEY,
        granted_by INTEGER,
        grant_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )
""")
#Таблица с сообщениями пользователям
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hr_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Таблица FAQ
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keywords TEXT, /* Ключевые слова для более умного поиска */
        question TEXT UNIQUE,
        answer TEXT
        )
    """)

# Таблица отзывов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        rating INTEGER NOT NULL,
        comments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(telegram_id)
    )
    """)

#Таблица вакансии    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vacancy_id TEXT NOT NULL,
            answers TEXT NOT NULL,
            applied_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(telegram_id)
        )
    """)
    
       
    conn.commit()
    print(f"База данных '{DATABASE_NAME}' инициализирована/подключена.")

#Код для отправки запроса к YandexGPT API 
def ask_yandex_gpt(prompt, temperature=0.5):
    """
    Корректная реализация запроса к YandexGPT
    :param prompt: Текст запроса
    :param temperature: Креативность (0-1)
    :return: Ответ модели или None
    """
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",     
        "completionOptions": {
            "temperature": temperature,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты HR-ассистент компании Rodanika. Отвечай вежливо и профессионально."
            },
            {
                "role": "user",
                "text": prompt
            }
        ]
    }

    try:
        response = requests.post(
            YANDEX_GPT_URL,
            headers=YANDEX_HEADERS,
            json=data,
            timeout=30
        )
        
        # Для отладки
        print("Request Data:", json.dumps(data, indent=2, ensure_ascii=False))
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        
        response.raise_for_status()
        result = response.json()
        
        return result['result']['alternatives'][0]['message']['text']
        
    except Exception as e:
        print(f"YandexGPT Error: {str(e)}")
        return None


def generate_feedback_report(rating, comments):
    """Генерирует расширенный отчет с помощью YandexGPT"""
    prompt = f"""
    Проанализируй отзыв сотрудника и составь профессиональный отчет для HR.
    Оценка: {rating}/5
    Комментарий: {comments}
    
    В отчете укажи:
    1. Основные темы и проблемы
    2. Эмоциональную окраску
    3. Рекомендации по улучшению
    4. Ключевые слова для категоризации
    
    Отчет должен быть кратким (не более 200 слов).
    """
    
    gpt_response = ask_yandex_gpt(prompt)
    
    if gpt_response:
        return f"""📊 Расширенный отчет (сгенерирован YandexGPT):
{gpt_response}"""
    else:
        # Фолбэк если GPT не ответил
        sentiment = "положительный" if rating >=4 else "нейтральный" if rating ==3 else "отрицательный"
        return f"""📊 Базовый отчет:
- Оценка: {rating}/5
- Тональность: {sentiment}
- Длина комментария: {len(comments.split())} слов"""


def add_faq_entry(keywords, question, answer):
    if not cursor or not conn:
        print("Ошибка: База данных не инициализирована для добавления FAQ.")
        return
    try:
        cursor.execute("INSERT INTO faq (keywords, question, answer) VALUES (?, ?, ?)",
                       (keywords, question, answer))
        conn.commit()
        print(f"Добавлен FAQ: {question[:40]}...")
    except sqlite3.IntegrityError:
        print(f"FAQ '{question[:40]}...' уже существует.") 
    except sqlite3.Error as e:
        print(f"Ошибка SQLite при добавлении FAQ: {e}")

# Основная клавиатура (ReplyKeyboardMarkup)
main_reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
main_reply_markup.add(
    types.KeyboardButton("Частые вопросы ❓"),
    types.KeyboardButton("Вакансии 🏢"),
    types.KeyboardButton("Карьерный помощник 🚀"),
    types.KeyboardButton("Адаптация сотрудников 🛠"),
    types.KeyboardButton("Обратная связь 📋"),
    types.KeyboardButton("Что умеет этот бот? 🦾"),
    #types.KeyboardButton("Помощь в использовании бота 🤝"),
    types.KeyboardButton("Новости HR 📢"),
    types.KeyboardButton("Запрос справки/документа 📄")  # Новая кнопка
)

# Инлайн-клавиатура для ссылки на сайт (пример)
inline_markup_website = types.InlineKeyboardMarkup()
inline_markup_website.add(types.InlineKeyboardButton("Перейти на сайт компании 🌐", url="https://rodanika.ru/"))

@bot.message_handler(func=lambda message: message.text == "Назад")
def handle_back(message):
    bot.send_message(
        message.chat.id,
        "Возвращаемся в главное меню",
        reply_markup=main_reply_markup
    )




# класс для работы с вакансиями на hh.ru
class VacancyManager:
    @staticmethod
    def get_vacancies():
        try:
            params = {
                'employer_id': HH_COMPANY_ID,
                'per_page': 10,
                'page': 0,
                'only_with_salary': True
            }
            response = requests.get(HH_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'items' not in data:
                print("Некорректный ответ от API HH.ru:", data)
                return []
                
            return data.get('items', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Ошибка сети при запросе вакансий: {str(e)}")
            return []
        except json.JSONDecodeError:
            print("Ошибка парсинга JSON ответа")
            return []
        
    @staticmethod
    def format_vacancy(vacancy):
        salary = vacancy.get('salary') or {}
        salary_str = ""
        # Упрощенная обработка зарплаты
        if salary.get('from') or salary.get('to'):
            parts = []
            if salary.get('from'): parts.append(f"от {salary['from']}")
            if salary.get('to'): parts.append(f"до {salary['to']}")
            salary_str = " ".join(parts) + f" {salary.get('currency', '')}"
        # Безопасное получение snippet
        snippet = vacancy.get('snippet', {})
        
        return f"""
    <b>{vacancy.get('name', 'Без названия')}</b>
    🏢 {vacancy.get('employer', {}).get('name', '')}
    📍 {vacancy.get('area', {}).get('name', '')}
    💰 Зарплата: {salary_str if salary_str else 'не указана'}
    📅 Опубликовано: {vacancy.get('published_at', '')[:10]}
    📌 {snippet.get('requirement', '')}
    🔗 <a href="{vacancy.get('alternate_url', '#')}">Подробнее на hh.ru</a>
    """

# обработчик для кнопки вакансий
@bot.message_handler(func=lambda message: message.text == "Вакансии 🏢")
def handle_vacancies(message):
    try:
        vacancies = VacancyManager.get_vacancies()
        
        if not vacancies:
            bot.send_message(
                message.chat.id, 
                "На данный момент открытых вакансий нет.\nПопробуйте проверить позже.",
                reply_markup=main_reply_markup
            )
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for vac in vacancies[:]:  # Показываем первые 5 вакансий
            btn_text = f"{vac['name']} ({vac['area']['name']})"
            markup.add(types.InlineKeyboardButton(
                text=btn_text,
                callback_data=f"vacancy_{vac['id']}"
            ))
        
        bot.send_message(
            message.chat.id,
            "📌 <b>Актуальные вакансии:</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Общая ошибка при обработке вакансий: {str(e)}")
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка при загрузке вакансий. Попробуйте позже.",
            reply_markup=main_reply_markup
        )

# Обработчик просмотра конкретной вакансии
@bot.callback_query_handler(func=lambda call: call.data.startswith('vacancy_'))
def handle_vacancy_view(call):
    vacancy_id = call.data.split('_')[1]
    try:
        response = requests.get(f"{HH_API_URL}/{vacancy_id}")
        vacancy = response.json()
        
        #проверка на наличие вакансии
        if 'id' not in vacancy:
            bot.answer_callback_query(call.id, "Вакансия больше не доступна")
            return
        
        text = VacancyManager.format_vacancy(vacancy)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            text="📨 Откликнуться",
            callback_data=f"apply_{vacancy_id}"
        ))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
    except requests.exceptions.RequestException as e:
        bot.answer_callback_query(call.id, "Ошибка при загрузке вакансии")
        print(f"Ошибка запроса вакансии: {str(e)}")
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка")
        print(f"Общая ошибка: {str(e)}")
        
        
# Обработчик отклика на вакансию
@bot.callback_query_handler(func=lambda call: call.data.startswith('apply_'))
def handle_vacancy_apply(call):
    vacancy_id = call.data.split('_')[1]
    user_id = call.from_user.id
    
    # Получаем данные пользователя из БД
    cursor.execute("SELECT registered_name FROM users WHERE telegram_id = ?", (user_id,))
    user_data = cursor.fetchone()
    user_name = user_data[0] if user_data else call.from_user.first_name
    
    msg = bot.send_message(
        call.message.chat.id,
        f"✍️ <b>Отклик на вакансию</b>\n\n"
        f"Пожалуйста, ответьте на несколько вопросов:\n"
        f"1. Был ли у вас опыт работы по этой вакансии?\n"
        f"2. Почему вы хотите работать у нас?\n"
        f"3. Какие ваши ожидания по зарплате?\n\n"
        f"Пожалуйста, напишите ответы одним сообщением:",
        parse_mode="HTML"
    )
    
    bot.register_next_step_handler(msg, process_application, vacancy_id, user_name)

def process_application(message, vacancy_id, user_name):
    try:
        # Получаем полные данные о вакансии
        response = requests.get(f"{HH_API_URL}/{vacancy_id}")
        vacancy = response.json()
        
        # Формируем заявку для HR
        application_text = f"""
📨 <b>Новый отклик на вакансию</b>
👤 <b>Кандидат:</b> {user_name} (@{message.from_user.username if message.from_user.username else 'нет'})
📝 <b>Вакансия:</b> {vacancy['name']}
🔗 <b>Ссылка:</b> {vacancy['alternate_url']}

<b>Ответы кандидата:</b>
{message.text}

<b>Контакты:</b>
Telegram: @{message.from_user.username or 'не указан'}
ID: {message.from_user.id}
"""
        #Отправление HR 
        hr_chat_ids = [5026101856]  
        for chat_id in hr_chat_ids:
            try:
                bot.send_message(chat_id, application_text, parse_mode="HTML")
            except:
                pass
        
        bot.send_message(
            message.chat.id,
            "✅ Ваш отклик успешно отправлен! HR свяжется с вами в ближайшее время.",
            reply_markup=main_reply_markup
        )
        # Логирование в базу данных
        cursor.execute("""
            INSERT INTO applications (user_id, vacancy_id, answers, applied_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (message.from_user.id, vacancy_id, message.text))
        conn.commit()
        
    except Exception as e:
        print(f"Ошибка при обработке отклика: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка при отправке отклика. Пожалуйста, попробуйте позже.",
            reply_markup=main_reply_markup
        )
        
@bot.message_handler(func=lambda message: message.text == "Карьерный помощник 🚀")
def handle_career_helper(message):
    try:
        # Проверяем существование файла
        if not os.path.exists("src/career_helper.png"):  # Используем английское название
            raise FileNotFoundError("Файл изображения не найден")
            
        with open("src/career_helper.png", "rb") as photo:
            # Отправляем фото с краткой подписью
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption="<b>🤖 Карьерный помощник Rodanika</b>",
                parse_mode="HTML"
            )
            
            # Создаем клавиатуру
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(
                types.KeyboardButton("Анализ резюме"),
                types.KeyboardButton("Советы по собеседованию"),
                types.KeyboardButton("Назад")
            )
            
            # Отправляем основное сообщение с клавиатурой
            bot.send_message(
                chat_id=message.chat.id,
                text="<b>Выберите опцию:</b>",
                reply_markup=markup,
                parse_mode="HTML"
            )
    
    except Exception as e:
        print(f"Ошибка при обработке команды: {e}")
        
        # Создаем клавиатуру даже при ошибке
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton("Анализ резюме"),
            types.KeyboardButton("Советы по собеседованию"),
            types.KeyboardButton("Назад")
        )
        
        # Отправляем сообщение об ошибке
        bot.send_message(
            chat_id=message.chat.id,
            text="<b>🤖 Карьерный помощник Rodanika</b>\n\nВыберите опцию:",
            reply_markup=markup,
            parse_mode="HTML"
        )
    
#кнопка анализ резюме
@bot.message_handler(func=lambda message: message.text == "Анализ резюме")
def handle_resume_analysis(message):
    msg = bot.send_message(
        message.chat.id,
        "📝 Пришлите текст вашего резюме, и я дам профессиональную оценку:",
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, process_resume_analysis)

def process_resume_analysis(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, 'typing')  # "печатает"
    
    prompt = f"""
    Проанализируй резюме и дай развернутую оценку:
    {user_text}
    
    Оцени:
    1. Структуру и оформление
    2. Полноту информации
    3. Сильные стороны
    4. Рекомендации по улучшению
    """
    
    analysis = ask_yandex_gpt(prompt)
    
    if analysis:
        # Форматируем ответ
        formatted_response = f"""
<b>📊 Анализ вашего резюме:</b>

<b>{analysis}</b>

<b>Рекомендации:
• Проверьте контакты и актуальность информации
• Убедитесь, что опыт работы описан подробно
• Добавьте ключевые навыки, соответствующие вакансии</b>
"""
        bot.send_message(
            message.chat.id,
            formatted_response,
            parse_mode="HTML",
            reply_markup=main_reply_markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "Извините, не удалось проанализировать резюме. Попробуйте позже.",
            reply_markup=main_reply_markup
        )

@bot.message_handler(func=lambda message: message.text == "Советы по собеседованию")
def handle_interview_tips(message):
    prompt = """Составь подробный чек-лист подготовки к собеседованию в компании по производству кваса, морса и напитков"""
    
    bot.send_chat_action(message.chat.id, 'typing')
    tips = ask_yandex_gpt(prompt)
    
    if tips:
        # Форматируем ответ
        response = f"""
<b>📝 Чек-лист подготовки к собеседованию в Rodanika:</b>

<b>{tips}</b>

<b>Дополнительные рекомендации:
• Подготовьте примеры из опыта
• Изучите нашу продукцию
• Продумайте вопросы о компании</b>
"""
    else:
        response = """
<b>📝 Основные моменты подготовки:
1. Изучите компанию: миссия, проекты, технологии
2. Продумайте ответы на типовые вопросы
3. Подготовьте вопросы работодателю
4. Проверьте технику для онлайн-собеседования</b>
"""
    
    bot.send_message(
        message.chat.id,
        response,
        parse_mode="HTML",
        reply_markup=create_back_button_keyboard()
    )

# Обработчики для подразделов советов по собеседованию
@bot.message_handler(func=lambda message: message.text == "Подготовка к собеседованию")
def handle_interview_preparation(message):
    prompt = """Составь подробный чек-лист подготовки к собеседованию в компании по производству кваса, морса и напитков, включая:
1. Что нужно изучить о компании
2. Как подготовить портфолио
3. Что надеть
4. Какие вопросы подготовить
5. Технические аспекты подготовки"""
    
    bot.send_chat_action(message.chat.id, 'typing')
    tips = ask_yandex_gpt(prompt)
    
    if tips:
        response = f"📝 <b>Чек-лист подготовки к собеседованию:</b>\n\n{tips}"
    else:
        response = """📝 <b>Основные моменты подготовки:</b>
1. Изучите компанию: миссия, проекты, технологии
2. Продумайте ответы на типовые вопросы
3. Подготовьте вопросы работодателю
4. Проверьте технику для онлайн-собеседования"""
    bot.send_message(
        message.chat.id,
        response,
        parse_mode="HTML",
        reply_markup=create_back_button_keyboard()
    )

#Кнопка частые вопросы на собеседовании
@bot.message_handler(func=lambda message: message.text == "Частые вопросы на собеседовании")
def handle_common_questions(message):
    prompt = """Перечисли 10 самых частых вопросов на собеседовании в компании по производству кваса и напитков с примерами хороших ответов. 
Включи технические и поведенческие вопросы."""
    
    bot.send_chat_action(message.chat.id, 'typing')
    questions = ask_yandex_gpt(prompt)
    
    if questions:
        response = f"❓ <b>Частые вопросы и ответы:</b>\n\n{questions}"
    else:
        response = """❓ <b>Частые вопросы:</b>
1. Расскажите о себе (концентрируйтесь на профессиональном опыте)
2. Почему хотите работать у нас? (покажите знание компании)
3. Ваши сильные/слабые стороны (будьте честны, но тактичны)
4. Где видите себя через 5 лет?"""
    
    bot.send_message(
        message.chat.id,
        response,
        parse_mode="HTML",
        reply_markup=create_back_button_keyboard()
    )
# Добавляем состояние диалога
user_states = {}

def set_user_state(user_id, state):
    user_states[user_id] = state

def get_user_state(user_id):
    return user_states.get(user_id)


# Модифицированный обработчик для требований к кандидату
@bot.message_handler(func=lambda message: message.text == "Требования к кандидату")
def handle_soft_skills(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Коммуникация", "Умение работать в команде", "Ответственность", "Другое")
    
    msg = bot.send_message(
        message.chat.id,
        "🤝 <b>Какие навыки вы хотите развить?</b>",
        parse_mode="HTML",
        reply_markup=markup
    )
    set_user_state(message.from_user.id, "awaiting_trebovania_skill")
    bot.register_next_step_handler(msg, process_trebovania_skills)

def process_trebovania_skills(message):
    if message.text == "Назад":
        #handle_skills_development(message)
        return
    
    skill = message.text
    msg = bot.send_message(
        message.chat.id,
        f"⏳ Составляю программу развития {skill}...",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    prompt = f"""Придумай небольшой план развития навыка {skill} для специалиста работающего на производсве кваса. Включи:
1. Развивать комуникацию  
2. Советы по применению в работе"""
    
    response = ask_yandex_gpt(prompt)
    
    if not response:
        response = f"""📈 <b>План развития {skill}:</b>
1. Ежедневные практические задания
2. Участие в групповых обсуждениях
3. Рефлексия прогресса"""
    
    bot.send_message(
        message.chat.id,
        response,
        parse_mode="HTML",
        reply_markup=create_back_button_keyboard()
    )
    set_user_state(message.from_user.id, None)


# Общий обработчик для кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад")
def handle_back(message):
    current_state = get_user_state(message.from_user.id)
    
    if current_state and current_state.startswith("awaiting"):
        set_user_state(message.from_user.id, None)
    
    #handle_skills_development(message)

FEEDBACK_LIMIT = 5
@bot.message_handler(func=lambda message: message.text == "Обратная связь 📋")
def start_feedback(message):
    user_id = message.from_user.id
    try:
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE user_id = ?", (user_id,))
        feedback_count = cursor.fetchone()[0]

        if feedback_count >= FEEDBACK_LIMIT:
            bot.send_message(
                message.chat.id,
                f"Вы уже оставили максимальное количество отзывов ({FEEDBACK_LIMIT}). Спасибо за вашу активность!",
                reply_markup=main_reply_markup
            )
            return

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("1 ⭐️", "2 ⭐️⭐️", "3 ⭐️⭐️⭐️", "4 ⭐️⭐️⭐️⭐️", "5 ⭐️⭐️⭐️⭐️⭐️")

        msg = bot.send_message(
            message.chat.id,
            "<b>Пожалуйста, оцените ваше впечатление от работы с ботом (1-5 звезд):</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_feedback_rating) # Регистрируем обработчик только один раз

    except sqlite3.Error as e:
        print(f"Database error checking feedback count: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла ошибка при проверке возможности оставить отзыв. Пожалуйста, попробуйте позже.",
            reply_markup=main_reply_markup
        )
    except Exception as e:
        print(f"Unexpected error in start_feedback: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла непредвиденная ошибка при запуске обратной связи. Пожалуйста, попробуйте позже.",
            reply_markup=main_reply_markup
        )


def process_feedback_rating(message):
    try:
        rating = int(message.text[0])
        if not 1 <= rating <= 5:
            raise ValueError

        user_data = {'rating': rating}
        markup = types.ForceReply(selective=False)
        msg = bot.send_message(message.chat.id,
                               "<b>Спасибо! Пожалуйста, напишите ваши предложения по улучшению:</b>",
                               reply_markup=markup, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_feedback_comments, user_data)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, выберите оценку от 1 до 5 звезд")
        start_feedback(message) #Вызываем start_feedback заново при ошибке
    except Exception as e:
        print(f"Ошибка в process_feedback_rating: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")
def process_feedback_rating(message):
    try:
        rating = int(message.text[0])  # Извлекаем число из "1 ⭐️"
        if not 1 <= rating <= 5:
            raise ValueError
            
        # Сохранение оценки в контексте пользователя
        user_data = {'rating': rating}
        
        markup = types.ForceReply(selective=False)
        msg = bot.send_message(message.chat.id, 
                             "<b>Спасибо! Пожалуйста, напишите ваши предложения по улучшению:</b>",
                             reply_markup=markup, parse_mode="HTML")
        bot.register_next_step_handler(msg, process_feedback_comments, user_data)
    except:
        bot.send_message(message.chat.id, "Пожалуйста, выберите оценку от 1 до 5 звезд")
        start_feedback(message)

# Клавиатура с кнопкой "Назад" для подразделов
def get_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="adapt_back"))
    return markup

def process_feedback_comments(message, user_data):
    try:
        comments = message.text
        
        # Сохраняем в базу данных
        cursor.execute("""
        INSERT INTO feedback (user_id, rating, comments)
        VALUES (?, ?, ?)
        """, (message.from_user.id, user_data['rating'], comments))
        conn.commit()
        
        # Формируем отчет
        report = generate_feedback_report(user_data['rating'], comments)
        
        bot.send_message(message.chat.id, 
                        f"Спасибо за ваш отзыв!\n\nВаша оценка: {user_data['rating']}⭐\n"
                        f"Ваши комментарии: {comments}\n\n"
                        f"Краткий отчет:\n{report}",
                        reply_markup=main_reply_markup)
        
        # Отправляем админу
        send_feedback_to_admin(message.from_user, user_data['rating'], comments)
        
    except Exception as e:
        print(f"Ошибка при обработке фидбека: {e}")
        bot.send_message(message.chat.id, 
                        "Произошла ошибка при сохранении вашего отзыва. Пожалуйста, попробуйте позже.",
                        reply_markup=main_reply_markup)

def generate_feedback_report(rating, comments):
    """Генерирует простой отчет без GPT"""
    sentiment = "положительный" if rating >=4 else "нейтральный" if rating ==3 else "отрицательный"
    keywords = {
        1: "критика, проблемы",
        2: "недовольство, улучшения",
        3: "нейтрально, предложения",
        4: "доволен, положительно",
        5: "отлично, восторг"
    }.get(rating, "")
    
    return f"""📊 Отчет по отзыву:
- Оценка: {rating}/5
- Тональность: {sentiment}
- Ключевые аспекты: {keywords}
- Длина комментария: {len(comments.split())} слов
"""

def send_feedback_to_admin(user, rating, comments):
    """Отправляет уведомление админам"""
    admin_chat_ids = [5026101856]  
    
    feedback_text = f"""
📩 Новый отзыв от пользователя:
👤 {user.first_name} (@{user.username})
⭐ Оценка: {rating}/5
📝 Комментарий:
{comments}
"""
    
    for chat_id in admin_chat_ids:
        try:
            bot.send_message(chat_id, feedback_text)
        except Exception as e:
            print(f"Ошибка при отправке фидбека админу {chat_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Что умеет этот бот? 🦾")
def handle_what_can_bot_do(message):
    with open("src/что умеет бот.png", "rb") as photo:  
        bot.send_photo(message.chat.id, photo)
    text = """
<b>👋 Я — HR-бот компании Rodanika! Вот что я умею:

❓ Отвечаю на часто задаваемые вопросы  
🚀 Помогаю с поиском актуальных вакансий  
🛠 Помогаю новому сотруднику адаптироваться на первом этапе — даю нужные ссылки, контакты, план не первую неделю
🤝 Помогаю разобраться в работе бота  
🎯 Даю советы для успешного первого собеседования  
📋 Рассказываю, какими навыками должен обладать кандидат

🔍 Встроенная модель GPT помогает:  
1️⃣ Проанализировать ваше резюме  
2️⃣ Подготовится к собеседованию
3️⃣ Дать актуальные советы, и рассказать про ошибки на собеседовании


💡 Бот может найти все актуальные вакансии с hh.ru за несколько секунд и отправить их в чат, впоследствии в боте можно откликнуться на вакансию и заявка отправится администратору бота в HR отдел.


📢 Администратор регулярно отправляет новости, а вы можете подписываться или отписываться от рассылок.


🌐 Больше информации о нашей компании на сайте!:</b>
    """
    bot.send_message(message.chat.id, text, reply_markup=inline_markup_website, parse_mode="HTML")



# Клавиатура с кнопкой "Назад" для подразделов
def get_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="adapt_back"))
    return markup

@bot.message_handler(func=lambda message: message.text == "Адаптация сотрудников 🛠")
def handle_adaptation(message):
    try:
        # Проверка существования файла перед открытием
        file_path = "src/адаптация .png"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден по пути: {file_path}")
        
        # Открытие и отправка фото
        with open(file_path, "rb") as photo:
            # Логирование перед отправкой
            
            caption = """<b>🔹 Программа адаптации новых сотрудников 🔹</b>
            
Выберите интересующий раздел:"""
            
            # Отправка с таймаутом
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=adaptation_markup,
                timeout=30  # Увеличиваем таймаут
            )
    
    except Exception as e:
        error_msg = f"⚠️ Ошибка при отправке фото: {str(e)}"
        print(error_msg)
        
        # Отправка текстового сообщения с ошибкой (для админа)
        bot.send_message(
            chat_id=message.chat.id,
            text=f"<b>🔹 Программа адаптации 🔹</b>\n\n{error_msg}\n\nВыберите раздел:",
            parse_mode="HTML",
            reply_markup=adaptation_markup
        )
# Инлайн-клавиатуры для адаптации
adaptation_markup = types.InlineKeyboardMarkup()
adaptation_markup.row(
    types.InlineKeyboardButton("Приветствие", callback_data="adapt_welcome"),
    types.InlineKeyboardButton("1-я неделя", callback_data="adapt_first_week")
)
adaptation_markup.row(
    types.InlineKeyboardButton("Контакты", callback_data="adapt_contacts"),
    types.InlineKeyboardButton("Полезные ссылки", callback_data="adapt_links")
)

# Кнопка "Назад" для подразделов
def get_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="adapt_back"))
    return markup

#кнопка "приветствие"
@bot.callback_query_handler(func=lambda call: call.data.startswith('adapt_'))
def handle_adaptation_callback(call):
    try:
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        # Удаляем исходное сообщение с фото
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as delete_error:
            print(f"Ошибка при удалении сообщения: {delete_error}")

        if call.data == "adapt_welcome":
            text = """👋 <b>Добро пожаловать в команду Rodanika!</b>

<b>Мы безумно рады приветствовать тебя в нашей дружной и креативной семье! Представляем, что сейчас ты чувствуешь себя как герой фильма, который только что ворвался в захватывающий мир Rodanika! 😉

Чтобы твой дебют был ярким и незабываемым, вот несколько советов для комфортного старта:

⦁ Не стесняйся задавать вопросы! Задавай всё, что взбредёт тебе в голову – мы с удовольствием на всё ответим! Даже если вопрос кажется тебе супер-простым – не бойся, лучше переспросить сто раз, чем один раз сделать неправильно! 😅
⦁ Знакомься с коллегами! Наши сотрудники – это классные ребята! Найди себе единомышленников, обсуждай любимые сериалы, делись рецептами вкусных обедов (или рассказывай о своих похождениях на выходных!) – создавай свою команду поддержки! 🤗
⦁ Изучи наши корпоративные ценности! Это не скучная лекция, а настоящий компас, который поможет тебе ориентироваться в мире Rodanika и всегда быть на верном пути! ✨
⦁ Запланируй встречи с HR и руководителем! Это как встреча с гидами по твоему новому приключению – они помогут тебе освоиться и покажут все самые интересные места в нашей компании! 🗺️

Желаем тебе успехов, море позитива и невероятных достижений в Rodanika! Let's go! 🚀</b>"""

            bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_markup=get_back_button()
            )

        elif call.data == "adapt_first_week":
            text = """<b>🗓 Недельный план адаптации на производстве кваса</b>

<u>День 1: Знакомство с производством</u>
🕘 9:00-10:30 — Вводный инструктаж по технике безопасности
• Особенности работы с оборудованием
• Требования к гигиене и спецодежде
🕥 10:30-12:00 — Экскурсия по цехам:
🔸 Сырьевой склад (мука, солод, дрожжи)
🔸 Бродильное отделение 
🔸 Линия розлива
🔸 Лаборатория контроля качества
🕐 13:00-14:30 — Знакомство с командой:
• Распределение обязанностей в смене
• Система наставничества

<u>День 2: Основные технологические процессы</u>
🕘 9:00-11:00 — Теория:
📚 Этапы приготовления сусла
📚 Принципы брожения
📚 Нормы ГОСТ для кваса
🕚 11:30-13:00 — Практикум:
• Подготовка дрожжевой закваски
• Контроль температуры брожения
🕑 14:00-15:30 — Работа с документацией:
• Журналы учета параметров
• Система HACCP

<u>День 3: Работа с наставником</u>
🕗 8:30-12:00 — Совместное выполнение задач:
🔹 Прием и проверка сырья
🔹 Запуск бродильных танков
🔹 Отбор проб для анализа
🕧 12:30-14:00 — Разбор типовых ситуаций:
• Действия при отклонении параметров
• Алгоритм аварийной остановки линии

<u>День 4: Самостоятельная практика</u>
🕘 9:00-11:00 — Работа на участках:
▶️ Приготовление сусла
▶️ Контроль процесса ферментации
▶️ Мойка и дезинфекция оборудования
🕧 12:30-14:30 — Освоение системы:
• Работа с автоматизированной линией розлива
• Настройка параметров пастеризации

<u>День 5: Итоговая аттестация</u>
🕙 10:00-12:00 — Тестирование:
📝 Технологические нормативы
📝 Правила безопасности
🕐 13:00-15:00 — Обратная связь:
• Анализ выполнения нормативов
• Рекомендации по улучшению навыков
• Вручение сертификата о прохождении адаптации"""

            bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_markup=get_back_button()
            )

        elif call.data == "adapt_contacts":
            text = """📞 <b>Важные контакты</b>

<b>HR-менеджер:</b> @hr_rodanika
<b>Техподдержка:</b> @it_support_rodanika
<b>Ваш наставник:</b> (информация будет предоставлена)
<b>Бухгалтерия:</b> finance@rodanika.ru"""

            bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_markup=get_back_button()
            )

        elif call.data == "adapt_links":
            text = """🔗 <b>Полезные ссылки</b>

1. Внутренний портал: https://portal.rodanika.ru
2. Корпоративная почта: https://mail.rodanika.ru
3. База знаний: https://wiki.rodanika.ru
4. Календарь мероприятий: https://events.rodanika.ru"""

            bot.send_message(
                chat_id,
                text,
                parse_mode="HTML",
                reply_markup=get_back_button()
            )

        elif call.data == "adapt_back":
            # Повторно отправляем меню с фото
            try:
                with open("src/адаптация .png", "rb") as photo:
                    bot.send_photo(
                        chat_id,
                        photo,
                        caption="<b>🔹 Программа адаптации новых сотрудников 🔹</b>\n\nВыберите интересующий раздел:",
                        parse_mode="HTML",
                        reply_markup=adaptation_markup
                    )
            except FileNotFoundError:
                bot.send_message(
                    chat_id,
                    "<b>🔹 Программа адаптации новых сотрудников 🔹</b>\n\nВыберите интересующий раздел:",
                    parse_mode="HTML",
                    reply_markup=adaptation_markup
                )

    except Exception as e:
        print(f"Ошибка в handle_adaptation_callback: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка, попробуйте позже")

#кнопка надад в меню
adaptation_markup.row(
    types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_main_menu")
)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main_menu")
def handle_back_to_main_menu(call):
    try:
        # Удаляем предыдущее сообщение (если нужно)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")

        # Отправляем главное меню
        bot.send_message(
            call.message.chat.id,
            "<b>Вы в главном меню:</b>",
            parse_mode="HTML",
            reply_markup=main_reply_markup
        )
    except Exception as e:
        print(f"Ошибка при обработке возврата в меню: {e}")
        bot.answer_callback_query(call.id, "⚠️ Произошла ошибка, попробуйте снова")
#ЧАСтЫЕ ВОПРОСЫ
@bot.message_handler(func=lambda message: message.text == "Частые вопросы ❓")
def handle_faq_list_button(message):
    with open("src/частые вопросы .png", "rb") as photo:  
        bot.send_photo(message.chat.id, photo)
    if not cursor or not conn:
        bot.send_message(message.chat.id, "Бот временно недоступен, проблема с базой данных. Попробуйте позже.")
        return

    faq_inline_markup = types.InlineKeyboardMarkup(row_width=1)
    try:
        cursor.execute("SELECT id, question FROM faq ORDER BY id LIMIT 10") 
        questions = cursor.fetchall()

        if not questions:
            bot.send_message(message.chat.id, "Извините, список частых вопросов пока пуст. Мы работаем над этим!", reply_markup=create_back_button_keyboard())
            return
        for q_id, q_text in questions:
            button = types.InlineKeyboardButton(text=q_text, callback_data=f"faq_{q_id}")
            faq_inline_markup.add(button)

        # Добавляем Inline-кнопку "Назад" в ту же клавиатуру
        back_button = types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")
        faq_inline_markup.add(back_button)

        bot.send_message(
            message.chat.id,
            "Выберите интересующий вас вопрос:",
            reply_markup=faq_inline_markup
        )

    except sqlite3.Error as e:
        print(f"Ошибка SQLite при получении списка FAQ: {e}")
        bot.send_message(message.chat.id, "Не удалось загрузить список вопросов. Попробуйте позже.", reply_markup=create_back_button_keyboard())


# Обработка нажатия Inline-кнопки "Назад"
@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def handle_back_button(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Вы вернулись назад. Чем могу помочь?",
        reply_markup=None
    )

@bot.message_handler(commands=['help'])
def handle_help_usage(message):
    with open("src/помощь.png", "rb") as photo:  
        bot.send_photo(message.chat.id, photo)
    text = """
    <b>Помощь по боту:
Используйте команду /start для начала или перезапуска диалога, а также для регистрации вашего имени.

Основные функции доступны через кнопки внизу экрана:</b>
     <b>❓ Часто задаваемые вопросы: У вас есть вопросы о нашей компании или процессе работы? Здесь вы найдете ответы на самые распространенные запросы.</b>
     <b>🚀 Вакансии: Ищете работу? Узнайте о текущих вакансиях и возможностях в нашей команде.</b>
     <b>🛠  Адаптация новых сотрудников: Мы подготовили информацию и ресурсы для тех, кто только начинает свой путь в нашей компании.</b>
     <b>📚 Карьерный помощник: поможет анализировать ваше резюме и дать советы на собеседовании.</b>
     <b>🤝 Поддержка и помощь: Если у вас возникли вопросы по работе с ботом или вам нужна дополнительная информация, просто дайте знать!</b>
     <b>📱 Обратная связь: Вы можете оставить отзыв о работе бота.</b>
<b>Если у вас возникли проблемы или есть предложения, пожалуйста, свяжитесь с администратором бота: @devlifee</b>
"""

    bot.send_message(message.chat.id, text, parse_mode="HTML")

# Добавляем команды для управления подпиской
@bot.message_handler(commands=['subscribe_news'])
def subscribe_news_command(message):
    """Команда для подписки на новости (/subscribe_news)"""
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO news_subscribers (user_id)
            VALUES (?)
        """, (message.from_user.id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.reply_to(message, "✅ Вы успешно подписались на новости HR!")
        else:
            bot.reply_to(message, "ℹ️ Вы уже подписаны на новости.")
    except Exception as e:
        print(f"Ошибка подписки: {e}")
        bot.reply_to(message, "⚠️ Не удалось оформить подписку. Попробуйте позже.")

@bot.message_handler(commands=['unsubscribe_news'])
def unsubscribe_news_command(message):
    """Команда для отписки от новостей (/unsubscribe_news)"""
    try:
        cursor.execute("""
            DELETE FROM news_subscribers
            WHERE user_id = ?
        """, (message.from_user.id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.reply_to(message, "✅ Вы отписались от новостей HR.")
        else:
            bot.reply_to(message, "ℹ️ Вы не были подписаны на новости.")
    except Exception as e:
        print(f"Ошибка отписки: {e}")
        bot.reply_to(message, "⚠️ Не удалось отписаться. Попробуйте позже.")

# Команда для добавления новости (только для админов)
@bot.message_handler(commands=['add_news'])
def add_news_command(message):
    """Команда для добавления новости (/add_news)"""
    try:
        if message.from_user.id not in [5026101856]:
            bot.reply_to(message, "⛔ Только администраторы могут публиковать новости.")
            return
            
        msg = bot.send_message(
            message.chat.id,
            "📝 Введите заголовок новости (не более 100 символов):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_news_title_command)
        
    except Exception as e:
        print(f"Ошибка при добавлении новости: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка. Попробуйте позже.")

def process_news_title_command(message):
    if len(message.text) > 100:
        bot.send_message(message.chat.id, "❌ Слишком длинный заголовок. Максимум 100 символов.")
        return add_news_command(message)
        
    msg = bot.send_message(
        message.chat.id,
        "📝 Теперь введите текст новости (не более 2000 символов):",
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, process_news_content_command, message.text)

def process_news_content_command(message, title):
    if len(message.text) > 2000:
        bot.send_message(message.chat.id, "❌ Слишком длинный текст. Максимум 2000 символов.")
        return add_news_command(message)
        
    try:
        # Сохраняем новость в БД
        cursor.execute("""
            INSERT INTO news (hr_id, title, content)
            VALUES (?, ?, ?)
        """, (message.from_user.id, title, message.text))
        conn.commit()
        
        # Рассылаем подписчикам
        send_news_to_subscribers(message.from_user.id, title, message.text)
        
        bot.send_message(
            message.chat.id,
            "✅ Новость успешно опубликована и разослана подписчикам!",
            reply_markup=create_back_button_keyboard()
        )
    except Exception as e:
        print(f"Ошибка публикации новости: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось опубликовать новость. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )



# Обработчик раздела новостей
@bot.message_handler(func=lambda message: message.text == "Новости HR 📢")
def handle_hr_news(message):
    # Проверяем права HR для отображения дополнительных опций
    is_hr = False
    try:
        cursor.execute("SELECT 1 FROM hr_rights WHERE user_id = ?", (message.from_user.id,))
        is_hr = cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Ошибка проверки прав HR: {e}")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [
        types.KeyboardButton("Последние новости"),
        types.KeyboardButton("Подписаться на новости"),
        types.KeyboardButton("Отписаться от новостей")
    ]
    
    #if is_hr:
    #    buttons.append(types.KeyboardButton("Добавить новость"))
    
    buttons.append(types.KeyboardButton("Назад"))
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "<b>📢 Новости HR-службы</b>\n\nВыберите действие:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# Просмотр последних новостей
@bot.message_handler(func=lambda message: message.text == "Последние новости")
def show_latest_news(message):
    try:
        cursor.execute("""
            SELECT n.title, n.content, n.created_at, u.registered_name 
            FROM news n
            JOIN users u ON n.hr_id = u.telegram_id
            ORDER BY n.created_at DESC
            LIMIT 5
        """)
        news = cursor.fetchall()
        
        if not news:
            bot.send_message(message.chat.id, "Пока нет новостей.", reply_markup=create_back_button_keyboard())
            return
            
        response = "<b>📰 Последние 5 новостей:</b>\n\n"
        for idx, (title, content, date, author) in enumerate(news, 1):
            response += f"<b>{idx}. {title}</b>\n"
            response += f"<i>{content}</i>\n"
            response += f"📅 {date[:10]} | 👤 {author}\n\n"
            
        bot.send_message(
            message.chat.id,
            response,
            parse_mode="HTML",
            reply_markup=create_back_button_keyboard()
        )
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось загрузить новости. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )

# Подписка на новости
@bot.message_handler(func=lambda message: message.text == "Подписаться на новости")
def subscribe_to_news(message):
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO news_subscribers (user_id)
            VALUES (?)
        """, (message.from_user.id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.send_message(
                message.chat.id,
                "✅ Вы успешно подписались на новости HR!",
                reply_markup=create_back_button_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "ℹ️ Вы уже подписаны на новости.",
                reply_markup=create_back_button_keyboard()
            )
    except Exception as e:
        print(f"Ошибка подписки: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось оформить подписку. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )

# Отписка от новостей
@bot.message_handler(func=lambda message: message.text == "Отписаться от новостей")
def unsubscribe_from_news(message):
    try:
        cursor.execute("""
            DELETE FROM news_subscribers
            WHERE user_id = ?
        """, (message.from_user.id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            bot.send_message(
                message.chat.id,
                "✅ Вы отписались от новостей HR.",
                reply_markup=create_back_button_keyboard()
            )
        else:
            bot.send_message(
                message.chat.id,
                "ℹ️ Вы не были подписаны на новости.",
                reply_markup=create_back_button_keyboard()
            )
    except Exception as e:
        print(f"Ошибка отписки: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось отписаться. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )

# Добавление новости (для HR)
@bot.message_handler(func=lambda message: message.text == "Добавить новость")
def add_news_start(message):
    try:
        # Проверка прав HR
        cursor.execute("SELECT 1 FROM hr_rights WHERE user_id = ?", (message.from_user.id,))
        if not cursor.fetchone():
            bot.send_message(message.chat.id, "⛔ Только HR-специалисты могут публиковать новости.")
            return
            
        msg = bot.send_message(
            message.chat.id,
            "📝 Введите заголовок новости (не более 100 символов):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_news_title)
        
    except Exception as e:
        print(f"Ошибка при добавлении новости: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )

def process_news_title(message):
    if len(message.text) > 100:
        bot.send_message(message.chat.id, "Слишком длинный заголовок. Максимум 100 символов.")
        return add_news_start(message)
        
    msg = bot.send_message(
        message.chat.id,
        "📝 Теперь введите текст новости (не более 2000 символов):",
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, process_news_content, message.text)

def process_news_content(message, title):
    if len(message.text) > 2000:
        bot.send_message(message.chat.id, "Слишком длинный текст. Максимум 2000 символов.")
        return add_news_start(message)
        
    try:
        # Сохраняем новость в БД
        cursor.execute("""
            INSERT INTO news (hr_id, title, content)
            VALUES (?, ?, ?)
        """, (message.from_user.id, title, message.text))
        conn.commit()
        
        # Рассылаем подписчикам
        send_news_to_subscribers(message.from_user.id, title, message.text)
        
        bot.send_message(
            message.chat.id,
            "✅ Новость успешно опубликована и разослана подписчикам!",
            reply_markup=create_back_button_keyboard()
        )
    except Exception as e:
        print(f"Ошибка публикации новости: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Не удалось опубликовать новость. Попробуйте позже.",
            reply_markup=create_back_button_keyboard()
        )

# Функция рассылки новостей подписчикам
def send_news_to_subscribers(hr_id, title, content):
    try:
        # Получаем имя автора
        cursor.execute("SELECT registered_name FROM users WHERE telegram_id = ?", (hr_id,))
        author = cursor.fetchone()[0] or "HR"
        
        # Формируем текст новости
        news_text = f"""
<b>📢 Новая новость от {author}:</b>

<b>{title}</b>

{content}

<i>Чтобы отписаться от новостей, используйте кнопку в разделе "Новости HR"</i>
        """
        
        # Получаем подписчиков
        cursor.execute("SELECT user_id FROM news_subscribers")
        subscribers = [row[0] for row in cursor.fetchall()]
        
        # Рассылаем с ограничением 30 сообщений в секунду (лимит Telegram)
        for i, user_id in enumerate(subscribers):
            try:
                if i % 20 == 0 and i > 0:
                    time.sleep(1)  # Пауза для соблюдения лимитов
                
                bot.send_message(user_id, news_text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки новости пользователю {user_id}: {e}")
                # Удаляем неактивного подписчика
                cursor.execute("DELETE FROM news_subscribers WHERE user_id = ?", (user_id,))
                conn.commit()
                
    except Exception as e:
        print(f"Ошибка рассылки новостей: {e}")


# ОТПРАВКА СООБЩЕНИЙ ВСЕМ ПОЛЬЗОВАТЕЛЯМ
# Обработчик команды /broadcast
@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    try:
        # Проверка прав HR
        user_id = message.from_user.id
        cursor.execute("SELECT 1 FROM hr_rights WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            bot.reply_to(message, "⛔ У вас нет прав для этой команды!")
            return

        # Запрашиваем сообщение для рассылки
        msg = bot.send_message(message.chat.id, "📢 Введите сообщение для рассылки:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_broadcast_message)

    except Exception as e:
        logging.error(f"Broadcast error: {str(e)}")
        bot.reply_to(message, "❌ Ошибка при запуске рассылки")

def process_broadcast_message(message):
    try:
        if message.text.lower() == 'отмена':
            bot.send_message(message.chat.id, "❌ Рассылка отменена", reply_markup=main_reply_markup)
            return

        # Запрос подтверждения
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Да", "❌ Нет")
        
        bot.send_message(message.chat.id, 
                       f"✉️ Сообщение для рассылки:\n\n{message.text}\n\nОтправить?",
                       reply_markup=markup)
        bot.register_next_step_handler(message, lambda m: confirm_broadcast(m, message.text))

    except Exception as e:
        logging.error(f"Broadcast processing error: {str(e)}")
        bot.send_message(message.chat.id, "❌ Ошибка при обработке сообщения")

def confirm_broadcast(message, broadcast_text):
    try:
        if message.text != '✅ Да':
            bot.send_message(message.chat.id, "❌ Рассылка отменена", reply_markup=main_reply_markup)
            return

        # Получаем всех пользователей
        cursor.execute("SELECT telegram_id FROM users")
        users = cursor.fetchall()
        
        sent = 0
        errors = 0
        
        # Отправка сообщений с паузами
        for i, user in enumerate(users):
            try:
                if i % 20 == 0 and i != 0:  # Пауза каждые 20 сообщений
                    time.sleep(1)
                
                bot.send_message(user[0], f"📢 Сообщение от HR:\n\n{broadcast_text}")
                sent += 1
            except Exception as e:
                errors += 1
                logging.error(f"Error sending to {user[0]}: {str(e)}")

        # Логируем рассылку
        cursor.execute("""
            INSERT INTO broadcasts (hr_id, message)
            VALUES (?, ?)
        """, (message.from_user.id, broadcast_text))
        conn.commit()

        # Формируем отчет
        report = f"""✅ Рассылка завершена!
┌ Всего получателей: {len(users)}
├ Успешно: {sent}
└ Ошибок: {errors}"""
        
        bot.send_message(message.chat.id, report, reply_markup=main_reply_markup)

    except Exception as e:
        logging.error(f"Broadcast error: {str(e)}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при рассылке")
@bot.message_handler(commands=['grant_hr'])
def handle_grant_hr(message):
    try:
        # Только главный админ
        if message.from_user.id not in [5026101856]:  
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "❌ Ответьте на сообщение пользователя")
            return

        target_id = message.reply_to_message.from_user.id
        
        # Добавляем в таблицу прав
        cursor.execute("""
            INSERT OR IGNORE INTO hr_rights (user_id, granted_by)
            VALUES (?, ?)
        """, (target_id, message.from_user.id))
        conn.commit()
        
        bot.reply_to(message, f"✅ Пользователь @{message.reply_to_message.from_user.username} стал HR")

    except Exception as e:
        logging.error(f"Ошибка назначения прав: {str(e)}")

@bot.message_handler(commands=['clear_faq'])
def handle_clear_faq(message):
    # Проверка прав (только для админов)
    if message.from_user.id not in [5026101856]:
        bot.reply_to(message, "⛔ У вас нет прав для этой команды!")
        return
    
    try:
        cursor.execute("DELETE FROM faq")
        conn.commit()
        bot.reply_to(message, "✅ Таблица faq успешно очищена")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Ошибка при очистке таблицы: {str(e)}")

# Обработчик для запроса документов
@bot.message_handler(func=lambda message: message.text == "Запрос справки/документа 📄")
def handle_document_request(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Справка о трудоустройстве"),
        types.KeyboardButton("Справка 2-НДФЛ"),
        types.KeyboardButton("Копия трудового договора"),
        types.KeyboardButton("Другая справка"),
        types.KeyboardButton("Назад")
    )
    
    bot.send_message(
        message.chat.id,
        "📄 <b>Выберите тип нужного документа:</b>",
        parse_mode="HTML",
        reply_markup=markup
    )

# Обработчик выбора типа документа
@bot.message_handler(func=lambda message: message.text in [
    "Справка о трудоустройстве", 
    "Справка 2-НДФЛ", 
    "Копия трудового договора",
    "Другая справка"
])
def handle_document_type(message):
    document_type = message.text
    if document_type == "Другая справка":
        msg = bot.send_message(
            message.chat.id,
            "✏️ Укажите, какая именно справка или документ вам нужны:",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_custom_document_type)
    else:
        msg = bot.send_message(
            message.chat.id,
            f"✏️ Укажите дополнительную информацию для запроса {document_type.lower()} (например, срок действия, количество копий и т.д.):",
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, process_document_request, document_type)

def process_custom_document_type(message):
    document_type = message.text
    msg = bot.send_message(
        message.chat.id,
        f"✏️ Укажите дополнительную информацию для запроса '{document_type}':",
        reply_markup=types.ForceReply()
    )
    bot.register_next_step_handler(msg, process_document_request, document_type)

def process_document_request(message, document_type):
    additional_info = message.text
    user_id = message.from_user.id
    
    try:
        # Сохраняем запрос в базу данных
        cursor.execute("""
            INSERT INTO document_requests (user_id, document_type, additional_info, estimated_completion)
            VALUES (?, ?, ?, ?)
        """, (user_id, document_type, additional_info, "1-3 рабочих дня"))
        conn.commit()
        
        # Получаем имя пользователя для уведомления HR
        cursor.execute("SELECT registered_name FROM users WHERE telegram_id = ?", (user_id,))
        user_data = cursor.fetchone()
        user_name = user_data[0] if user_data else message.from_user.first_name
        
        # Формируем уведомление для HR
        notification_text = f"""
📄 <b>Новый запрос документа</b>
👤 <b>Сотрудник:</b> {user_name} (@{message.from_user.username if message.from_user.username else 'нет'})
📝 <b>Тип документа:</b> {document_type}
ℹ️ <b>Доп. информация:</b> {additional_info}
🆔 <b>User ID:</b> {user_id}
"""
        # Отправляем уведомление HR (email/Telegram/таблица)
        send_document_request_notification(notification_text)
        
        # Отправляем подтверждение пользователю
        bot.send_message(
            message.chat.id,
            f"✅ <b>Ваш запрос на {document_type.lower()} принят!</b>\n\n"
            f"Примерный срок выполнения: 1-3 рабочих дня\n"
            f"HR свяжется с вами, когда документ будет готов.",
            parse_mode="HTML",
            reply_markup=main_reply_markup
        )
        
    except Exception as e:
        print(f"Ошибка при обработке запроса документа: {e}")
        bot.send_message(
            message.chat.id,
            "⚠️ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.",
            reply_markup=main_reply_markup
        )

def send_document_request_notification(notification_text):
    """Отправляет уведомления о новом запросе документа"""
    try:
        # 1. Отправка в Telegram HR-ам
        hr_chat_ids = [5026101856]  
        for chat_id in hr_chat_ids:
            try:
                bot.send_message(chat_id, notification_text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка отправки уведомления в Telegram для {chat_id}: {e}")
        
    except Exception as e:
        print(f"Ошибка при отправке уведомлений: {e}")

# Добавляем команду для просмотра запросов (для HR)
@bot.message_handler(commands=['document_requests'])
def handle_view_requests(message):
    try:
        # Проверка прав HR
        cursor.execute("SELECT 1 FROM hr_rights WHERE user_id = ?", (message.from_user.id,))
        if not cursor.fetchone():
            bot.reply_to(message, "⛔ У вас нет прав для этой команды!")
            return
            
        cursor.execute("""
            SELECT dr.id, u.registered_name, dr.document_type, dr.additional_info, 
                   dr.status, dr.created_at, dr.estimated_completion
            FROM document_requests dr
            JOIN users u ON dr.user_id = u.telegram_id
            ORDER BY dr.created_at DESC
            LIMIT 10
        """)
        requests = cursor.fetchall()
        
        if not requests:
            bot.reply_to(message, "ℹ️ Нет активных запросов документов.")
            return
            
        response = "📋 <b>Последние 10 запросов документов:</b>\n\n"
        for req in requests:
            response += (
                f"🆔 <b>ID:</b> {req[0]}\n"
                f"👤 <b>Сотрудник:</b> {req[1]}\n"
                f"📄 <b>Документ:</b> {req[2]}\n"
                f"ℹ️ <b>Доп. инфо:</b> {req[3]}\n"
                f"🔄 <b>Статус:</b> {req[4]}\n"
                f"⏳ <b>Создан:</b> {req[5]}\n"
                f"⏱ <b>Примерный срок:</b> {req[6]}\n\n"
            )
            
        bot.reply_to(message, response, parse_mode="HTML")
        
    except Exception as e:
        print(f"Ошибка при просмотре запросов: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка при получении списка запросов.")

# Добавляем команду для изменения статуса запроса (для HR)
@bot.message_handler(commands=['update_request'])
def handle_update_request(message):
    try:
        # Проверка прав HR
        cursor.execute("SELECT 1 FROM hr_rights WHERE user_id = ?", (message.from_user.id,))
        if not cursor.fetchone():
            bot.reply_to(message, "⛔ У вас нет прав для этой команды!")
            return
            
        if not message.reply_to_message or not message.reply_to_message.text:
            bot.reply_to(message, "❌ Ответьте на сообщение с запросом, который нужно обновить")
            return
            
        try:
            request_id = int(message.text.split()[1])
            new_status = message.text.split()[2]
        except (IndexError, ValueError):
            bot.reply_to(message, "❌ Использование: /update_request [ID] [новый_статус]")
            return
            
        cursor.execute("""
            UPDATE document_requests
            SET status = ?
            WHERE id = ?
        """, (new_status, request_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            # Получаем информацию о запросе для уведомления пользователя
            cursor.execute("""
                SELECT user_id, document_type FROM document_requests
                WHERE id = ?
            """, (request_id,))
            req_data = cursor.fetchone()
            
            if req_data:
                user_id, doc_type = req_data
                status_text = {
                    "completed": "готов",
                    "rejected": "отклонен",
                    "in_progress": "в процессе подготовки"
                }.get(new_status, new_status)
                
                try:
                    bot.send_message(
                        user_id,
                        f"ℹ️ <b>Статус вашего запроса на {doc_type.lower()} изменен:</b> {status_text}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Не удалось уведомить пользователя {user_id}: {e}")
            
            bot.reply_to(message, f"✅ Статус запроса {request_id} обновлен на '{new_status}'")
        else:
            bot.reply_to(message, "❌ Запрос с указанным ID не найден")
            
    except Exception as e:
        print(f"Ошибка при обновлении запроса: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка при обновлении запроса")


####  В СЛУЧАЕ ОШИБОК ##################################################################################################################################
@bot.callback_query_handler(func=lambda call: call.data.startswith('faq_'))
def handle_faq_answer_callback(call):
    if not cursor or not conn:
        bot.answer_callback_query(call.id, "Бот временно недоступен, проблема с базой данных.")
        return
    try:
        question_id_str = call.data.split('_')[1] # Получение ID из 'faq_ID'
        question_id = int(question_id_str)

        cursor.execute("SELECT question, answer FROM faq WHERE id = ?", (question_id,))
        faq_data = cursor.fetchone()

        bot.answer_callback_query(call.id) # Ответ на callback, чтобы кнопка перестала "грузиться"

        if faq_data and faq_data[1]: # Если есть вопрос (faq_data[0]) и ответ (faq_data[1])
            question_text = faq_data[0]
            answer_text = faq_data[1]

            # Создаем инлайн-кнопку "Назад"
            back_button_markup = types.InlineKeyboardMarkup()
            back_button_markup.add(types.InlineKeyboardButton("⬅️ Назад к вопросам", callback_data="back_to_faq_list"))
# Редактируем исходное сообщение, чтобы показать ответ и кнопку "Назад"
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=f"❓ **{question_text}**\n\nОтвет:\n{answer_text}",
                                  reply_markup=back_button_markup,
                                  parse_mode="Markdown")
        else:
            # Если ответ не найден (маловероятно, если ID корректный, но на всякий случай)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Извините, ответ на этот вопрос не найден.",
                                  reply_markup=None) # Убираем клавиатуру

    except sqlite3.Error as e:
        print(f"Ошибка SQLite при получении ответа на FAQ: {e}")
        if call.id: bot.answer_callback_query(call.id, text="Ошибка при получении ответа.")
    except Exception as e:
        print(f"Непредвиденная ошибка в handle_faq_answer_callback: {e}")
        if call.id: bot.answer_callback_query(call.id, text="Произошла непредвиденная ошибка.")




@bot.callback_query_handler(func=lambda call: call.data == 'back_to_faq_list')
def handle_back_to_faq_list_callback(call):
    if not cursor or not conn:
        bot.answer_callback_query(call.id, "Бот временно недоступен, проблема с базой данных.")
        return

    faq_inline_markup = types.InlineKeyboardMarkup(row_width=1)
    try:
        cursor.execute("SELECT id, question FROM faq ORDER BY id LIMIT 10")
        questions = cursor.fetchall()
        bot.answer_callback_query(call.id) # Отвечаем на коллбэк

        if not questions:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Извините, список частых вопросов пока пуст.",
                                  reply_markup=None)
            return

        for q_id, q_text in questions:
            button = types.InlineKeyboardButton(text=q_text, callback_data=f"faq_{q_id}")
            faq_inline_markup.add(button)

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Выберите интересующий вас вопрос:",
                              reply_markup=faq_inline_markup)

    except sqlite3.Error as e:
        print(f"Ошибка SQLite при возврате к списку FAQ: {e}")
        bot.answer_callback_query(call.id, "Не удалось загрузить список вопросов.")
    except Exception as e:
        print(f"Непредвиденная ошибка в handle_back_to_faq_list_callback: {e}")
        bot.answer_callback_query(call.id, "Произошла непредвиденная ошибка.")

@bot.message_handler(func=lambda message: True)  # Будет ловить все сообщения
def handle_unknown_message(message):
    # Проверяем, не является ли сообщение командой или известным текстом
    if message.text.startswith('/') or message.text in [
        "Частые вопросы ❓", 
        "Вакансии 🏢",
        "Карьерный помощник 🚀",
        "Адаптация сотрудников 🛠",
        "Обратная связь 📋",
        "Что умеет этот бот? 🦾",
        "Новости HR 📢"
    ]:
        return  # Пропускаем известные команды и кнопки
    
    # Отправляем сообщение о непонимании
    bot.send_message(
        message.chat.id,
        "🤖 <b>Я не совсем понял ваш запрос.</b>\n\n"
        "Пожалуйста, выберите один из вариантов ниже:",
        parse_mode="HTML"
    )
    
    # Показываем основную клавиатуру
    bot.send_message(
        message.chat.id,
        "Выберите нужный раздел:",
        reply_markup=main_reply_markup
    )
    



#Основной блок запуска бота ---
if __name__ == '__main__':
    print("Инициализация HR-бота Rodanika...")
    try:
        init_db() # Инициализируем БД и глобальные conn, cursor

        # Заполняем таблицу FAQ примерами, если она пуста
        if cursor: # Проверяю, что курсор был инициализирован
            cursor.execute("SELECT COUNT(*) FROM faq")
            if cursor.fetchone()[0] == 0:
                print("Таблица FAQ пуста. Заполняем примерами...")
                add_faq_entry(
                    "регистрация, начало, старт",
                    "Как начать пользоваться ботом?",
                    "Чтобы начать взаимодействие с ботом, просто отправьте команду /start. После этого я попрошу вас представиться, " \
                    "чтобы иметь возможность обращаться к вам по имени. Следуйте инструкциям, и вскоре вы сможете воспользоваться всеми" \
                    "функциями нашего сервиса.")
                add_faq_entry(
                    "вакансии, работа, карьера",
                    "Где посмотреть актуальные вакансии?",
                    "Актуальные вакансии вы можете найти, нажав кнопку 'Вакансии 🏢'")
                add_faq_entry(
                    "отзыв, обратная связь, связь",
                    "Как оставить отзыв о работе бота?",
                    "Для того, чтобы оставить отзыв о работе нашего бота нужер перейти  в раздел Обратная связь 📋" \
                    "Поставить оценку и написать отзыв.")
                add_faq_entry(
                    "сайт, компания, о нас",
                    "Что такое Роданика?",
                    "«Роданика» — компания, которая занимается производством натуральных и полезных напитков. " \
                    "Производит квас, пунши и глинтвейны, компоты, морсы, соки и чай. Чтобы узнать больше о нашей компании Rodanika и ее деятельности, вы можете посетить наш официальный сайт по адресу: https://rodanika.ru/. \
                    Там вы найдете всю необходимую информацию о наших услугах, команде и многом другом.")
                add_faq_entry(
                    "проблемы, ошибка, не работает",
                    "Что делать, если бот не отвечает или работает некорректно?",
                    "Если бот перестал отвечать или вы столкнулись с какой-либо ошибкой, пожалуйста, попробуйте использовать его снова через некоторое время. " \
                    "В случае, если проблема сохраняется, рекомендуем обратиться к администратору @devlifee. Мы ценим ваше " \
                    "терпение и стремимся обеспечить бесперебойную работу нашего сервиса.")                                                            
                add_faq_entry(
                    "цель бота, зачем, функции",
                    "Зачем нужен данный бот?",
                    "Этот бот создан с целью оказания помощи как сотрудникам, так и кандидатам компании Rodanika. Он предоставляет быстрый доступ к информации, отвечает на часто задаваемые вопросы и информирует о новостях компании. Мы надеемся, что взаимодействие с ботом сделает вашу жизнь проще и удобнее!")
                add_faq_entry(
                    "Оформление отпуска",
                    "Как оформить отпуск и что для этого нужно?",
                    "Для оформления отпуска необходимо:\n1. Заполнить заявление на отпуск (образец можно найти здесь: "
                    "[ссылка на образец заявления]).\n2. Согласовать даты отпуска с вашим непосредственным руководителем.\n3." \
                    "Предоставить заполненное заявление в отдел кадров за [количество дней] до начала отпуска.\n4. "
                    "Для получения более подробной информации, пожалуйста, обратитесь в отдел кадров.")

                add_faq_entry(
                    "Оформление больничного",
                    "Как оформить больничный лист и что необходимо сделать?",
                    "В случае болезни вам необходимо:\n1. Обратиться к врачу для получения больничного листа.\n2." \
                    "Предоставить больничный лист в отдел кадров в течение [количество дней] со дня выдачи больничного листа.\n3. "
                    "Для получения более подробной информации, пожалуйста, свяжитесь с отделом кадров или обратитесь к [контактное лицо/номер телефона].")

                print("Примеры FAQ добавлены.")
            else:
                print("Таблица FAQ уже содержит данные.")
        else:
            print("Ошибка: Не удалось инициализировать курсор БД, пропуск заполнения FAQ.")
        print("HR-бот Rodanika запускается...")
        bot.infinity_polling(skip_pending=True, timeout=90, long_polling_timeout = 60) 
    except sqlite3.Error as db_err:
        print(f"Критическая ошибка базы данных при запуске: {db_err}")
    except Exception as e:
        print(f"Критическая ошибка при запуске или во время работы бота: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с БД закрыто.")
        print("HR-бот Rodanika остановлен.")