from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb_admin = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2
)

btn_broadcast = KeyboardButton('📢 Рассылка')
btn_quests = KeyboardButton('🎯 Управление квестами')
btn_shop = KeyboardButton('🛒 Управление магазином')
btn_support = KeyboardButton('📭 Управление поддержкой')
btn_student_mode = KeyboardButton('🎓 Режим ученика')

kb_admin.add(  btn_broadcast)
kb_admin.add(btn_quests, btn_shop, btn_support)
kb_admin.add(btn_student_mode)