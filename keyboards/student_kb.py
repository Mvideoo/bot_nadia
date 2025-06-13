from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_student = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2
)

btn_profile = KeyboardButton('👤 Профиль')
btn_learning = KeyboardButton('📚 Обучение')
btn_quests = KeyboardButton('🎯 Квесты')
btn_rating = KeyboardButton('🏆 Рейтинг')  # Измененная кнопка
btn_olympiads = KeyboardButton('🏅 Олимпиады по экономике')
btn_shop = KeyboardButton('🛒 Магазин')
btn_support = KeyboardButton('🆘 Поддержка')
btn_support_history = KeyboardButton('📬 Мои обращения')
btn_back = KeyboardButton('🔙 В админ-панель')

kb_student.add(btn_learning, btn_quests, btn_profile)
kb_student.add(btn_olympiads, btn_rating, btn_shop)  # Используем новую кнопку
kb_student.add(btn_support, btn_support_history)
kb_student.add(btn_back)
