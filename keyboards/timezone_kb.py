from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_timezone_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("UTC+2", callback_data="tz_utc2"),
        InlineKeyboardButton("UTC+3 - Москва", callback_data="tz_utc3"),
        InlineKeyboardButton("UTC+4", callback_data="tz_utc4"),
        InlineKeyboardButton("UTC+5", callback_data="tz_utc5"),
        InlineKeyboardButton("UTC+6", callback_data="tz_utc6"),
        InlineKeyboardButton("UTC+7", callback_data="tz_utc7"),
        InlineKeyboardButton("UTC+8", callback_data="tz_utc8"),
        InlineKeyboardButton("UTC+9", callback_data="tz_utc9"),
        InlineKeyboardButton("UTC+10", callback_data="tz_utc10"),
        InlineKeyboardButton("UTC+11", callback_data="tz_utc11"),
        InlineKeyboardButton("UTC+12", callback_data="tz_utc12"),
    ]
    keyboard.add(*buttons)
    return keyboard,