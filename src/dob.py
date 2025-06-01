# Модифицированный обработчик для языковых курсов
#@bot.message_handler(func=lambda message: message.text == "Языковые курсы")
#def handle_language_courses(message):
#    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#    markup.add("Английский", "Немецкий", "Другой", "Назад")
#    
#    msg = bot.send_message(
#        message.chat.id,
#        "🌍 <b>Какой язык вы хотите изучать?</b>",
#        parse_mode="HTML",
#        reply_markup=markup
#    )
#    set_user_state(message.from_user.id, "awaiting_language")
#    bot.register_next_step_handler(msg, process_language_choice)
#
#def process_language_choice(message):
#    if message.text == "Назад":
#        handle_skills_development(message)
#        return
#    
#    language = message.text
#    msg = bot.send_message(
#        message.chat.id,
#        f"📝 <b>Какой уровень у вас сейчас?</b>\n(Начинающий/Средний/Продвинутый)",
#        parse_mode="HTML",
#        reply_markup=types.ForceReply()
#    )
#    set_user_state(message.from_user.id, f"awaiting_level_{language}")
#    bot.register_next_step_handler(msg, lambda m: process_language_plan(m, language))

#def process_language_plan(message, language):
#    if message.text == "Назад":
#        handle_skills_development(message)
#        return
#    
#    level = message.text
#    prompt = f"""Составь индивидуальную программу изучения {language} для уровня {level} с акцентом на IT-терминологию. 
#Включи ресурсы, расписание и практические задания."""
#    
#    response = ask_yandex_gpt(prompt)
#    
#    if not response:
#        response = f"""📚 <b>Программа изучения {language} ({level}):</b>
#1. IT-специализированные курсы на Coursera
#2. Ежедневная практика с приложением Duolingo
#3. Чтение технической документации
#4. Недельные спринты с конкретными целями"""
#    
#    bot.send_message(
#        message.chat.id,
#        response,
#        parse_mode="HTML",
#        reply_markup=create_back_button_keyboard()
#    )
#    set_user_state(message.from_user.id, None)

# Модифицированный обработчик для книг и ресурсов
#@bot.message_handler(func=lambda message: message.text == "Книги и ресурсы")
#def handle_books_resources(message):
#    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#    markup.add("Программирование", "Менеджмент", "Дизайн", "Другое")
#    
#    msg = bot.send_message(
#        message.chat.id,
#        "📚 <b>Какая область вас интересует?</b>",
#        parse_mode="HTML",
#        reply_markup=markup
#    )
#    set_user_state(message.from_user.id, "awaiting_topic")
#    bot.register_next_step_handler(msg, process_book_recommendations)
#
#def process_book_recommendations(message):
#    if message.text == "Назад":
#        handle_skills_development(message)
#        return
#    
#    topic = message.text
#    prompt = f"""Подбери 5 лучших ресурсов по {topic} для IT-специалиста. Включи:
#- 2 книги
#- 2 онлайн-курса
#- 1 неочевидный полезный ресурс
#Для каждого укажи краткое описание."""
    
#    response = ask_yandex_gpt(prompt)
    
#    if not response:
#        response = f"""📖 <b>Рекомендации по {topic}:</b>
#1. Книга "Совершенный код" - основы программирования
#2. Курс на Stepik - практические задания
#3. Подкаст "Developer Tea" - для ежедневного обучения"""
#    
#    bot.send_message(
#        message.chat.id,
#        response,
#        parse_mode="HTML",
#        reply_markup=create_back_button_keyboard()
#    )
#    set_user_state(message.from_user.id, None)

#Модифицированный обработчик для технических навыков (при расширении проекта можно добавить)
#@bot.message_handler(func=lambda message: message.text == "Технические навыки")
#def handle_technical_skills(message):
#    msg = bot.send_message(
#        message.chat.id,
#        "💻 <b>Давайте составим персональный план развития!\n\n"
#        "На какую специалность вы бы хотели устроиться?(Например: Наладчик отдела продаж, менеджер контроля качества, Сотрудник склада и др.)</b>",
#        parse_mode="HTML",
#        reply_markup=types.ForceReply()
#    )
#    set_user_state(message.from_user.id, "awaiting_tech_skill")
#    bot.register_next_step_handler(msg, process_technical_skills)
#
#def process_technical_skills(message):
#    if message.text == "Назад":
#        handle_skills_development(message)
#        return
#    
#    skill = message.text
#    msg = bot.send_message(
#        message.chat.id,
#        f"⏳ Генерирую персональный план по {skill}...",
#        reply_markup=types.ReplyKeyboardRemove()
#    )
#    
#    prompt = f"""Составь персональный план обучения для {skill}. Включи:
#1. Основные темы для изучения
#2. Ориентировочные сроки
#Формат: маркированный список с эмодзи"""
#    
#    response = ask_yandex_gpt(prompt)
#    
#    if not response:
#        response = f"""🚀 <b>Базовый план изучения {skill}:</b>
#1. Изучать материалы из интернета"""
#    
#    bot.send_message(
#        message.chat.id,
#        f"📚 <b>Ваш персональный план по {skill}:</b>\n\n{response}",
#        parse_mode="HTML",
#        reply_markup=create_back_button_keyboard()
#    )
#    set_user_state(message.from_user.id, None)

#@bot.message_handler(func=lambda message: message.text == "Развитие навыков")
#def handle_skills_development(message):
#    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
#    markup.add(
#        #"Технические навыки",
#        #"Требования к кандидату",
#        #"Книги и ресурсы",
#        "Назад"
#    )
#    
#    bot.send_message(
#        message.chat.id,
#        "📚 <b>Развитие навыков с бота Роданика:\n\nВыберите направление для развития:</b>",
#        reply_markup=markup,
#        parse_mode="HTML"
#    )
