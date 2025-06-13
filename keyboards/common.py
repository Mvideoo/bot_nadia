from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_timezone_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
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
        InlineKeyboardButton("UTC+12", callback_data="12")

    ]
    keyboard.add(*buttons)
    return keyboard

def get_cancel_kb():
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('❌ Отмена'))

def get_age_group_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("14-17 лет", callback_data="age_14-17"),
        InlineKeyboardButton("18-25 лет", callback_data="age_18-25")
    )
    return keyboard

def course_selection_keyboard(courses):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for course_id, course in courses.items():
        keyboard.add(InlineKeyboardButton(
            course['title'],
            callback_data=f"course_{course_id}"
        ))
    return keyboard


def lesson_selection_keyboard(course_id, lessons, progress):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for lesson_id, lesson in lessons.items():
        status = ""
        if progress and lesson_id in progress:
            if progress[lesson_id]['quiz_passed']:
                status = "✅✅ "
            elif progress[lesson_id]['read']:
                status = "✅ "

        keyboard.add(InlineKeyboardButton(
            f"{status}Урок {lesson_id}: {lesson['title']}",
            callback_data=f"lesson_{course_id}_{lesson_id}"
        ))
    return keyboard


def mark_as_read_keyboard(course_id, lesson_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        "Прочитал",
        callback_data=f"read_{course_id}_{lesson_id}"
    ))
    return keyboard


def start_quiz_keyboard(course_id, lesson_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        "Пройти тест",
        callback_data=f"quiz_{course_id}_{lesson_id}"
    ))
    return keyboard


def quiz_options_keyboard(options):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for idx, option in enumerate(options):
        keyboard.add(InlineKeyboardButton(
            option,
            callback_data=f"answer_{idx}"
        ))
    return keyboard


def after_quiz_keyboard(course_id, lesson_id, show_next=True):
    keyboard = InlineKeyboardMarkup(row_width=1)

    if show_next:
        keyboard.add(InlineKeyboardButton(
            "➡️ Следующий урок",
            callback_data=f"next_lesson_{course_id}_{lesson_id}"
        ))

    keyboard.add(InlineKeyboardButton(
        "🔄 Пройти тест еще раз",
        callback_data=f"retry_quiz_{course_id}_{lesson_id}"
    ))

    keyboard.add(InlineKeyboardButton(
        "📚 Вернуться к списку уроков",
        callback_data=f"course_{course_id}"
    ))

    return keyboard
