from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_quest_management = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2
)

btn_list_quests = KeyboardButton('📋 Список товаров')
btn_add_quest = KeyboardButton('➕ Добавить товар')
btn_open_tickets = KeyboardButton('📬 Открытые обращения')
btn_closed_tickets = KeyboardButton('📭 Закрытые обращения')
btn_back = KeyboardButton('🔙 В админ-панель')

kb_quest_management.add(btn_list_quests, btn_add_quest)
kb_quest_management.add(btn_open_tickets, btn_closed_tickets)
kb_quest_management.add(btn_back)