from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from data_base import db
from data_base.models.user import User
from keyboards.common import get_timezone_keyboard, get_age_group_keyboard
from keyboards import admin_kb, student_kb
from utils.storage import admin_modes
import logging

logger = logging.getLogger(__name__)


class Registration(StatesGroup):
    full_name = State()
    timezone = State()
    age_group = State()


class SupportState(StatesGroup):
    waiting_for_question = State()


async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"Start command from user: {user_id}")

    # Проверяем, зарегистрирован ли пользователь
    user = await User.get_user(user_id)
    if user:
        role = await db.get_user_role(user_id)
        if role == "admin":
            admin_modes[user_id] = 'admin'
            await message.answer("Добро пожаловать!", reply_markup=admin_kb.kb_admin)
        else:
            await message.answer("Добро пожаловать!", reply_markup=student_kb.kb_student)
        return

    # Приветственное сообщение для новых пользователей
    welcome_text = (
        "🌟 Добро пожаловать в Финансовый Университет Бот! 🌟\n\n"
        "Здесь ты научишься:\n"
        "• Управлять личным бюджетом 💰\n"
        "• Инвестировать с умом 📈\n"
        "• Понимать финансовые рынки 🌐\n"
        "• Планировать свое финансовое будущее 🚀\n\n"
        "Для начала давай познакомимся! Пожалуйста, напиши свое ФИО:"
    )

    await message.answer(welcome_text)
    await Registration.full_name.set()


async def process_full_name(message: types.Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)
    logger.info(f"User {message.from_user.id} entered full name: {full_name}")

    # Запрос часового пояса
    timezone_text = (
        "⏰ Отлично! Теперь выбери свой часовой пояс, "
        "чтобы мы не беспокоили тебя ночью:"
    )
    await message.answer(timezone_text, reply_markup=get_timezone_keyboard())
    await Registration.timezone.set()


async def process_timezone(callback: types.CallbackQuery, state: FSMContext):
    timezone_map = {
        "tz_utc2": "UTC+2",
        "tz_utc3": "UTC+3",
        "tz_utc4": "UTC+4",
        "tz_utc5": "UTC+5",
        "tz_utc6": "UTC+6",
        "tz_utc7": "UTC+7",
        "tz_utc8": "UTC+8",
        "tz_utc9": "UTC+9",
        "tz_utc10": "UTC+10",
        "tz_utc11": "UTC+11",
        "tz_utc12": "UTC+12",
        "tz_utc-10": "UTC-10",
        "tz_utc-11": "UTC-11",
        "tz_utc-12": "UTC-12"
    }

    timezone = timezone_map.get(callback.data, "UTC+3")
    user_data = await state.get_data()
    full_name = user_data['full_name']
    user_id = callback.from_user.id

    logger.info(f"User {user_id} selected timezone: {timezone}")

    # Убираем кнопки выбора часового пояса
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # Сохраняем часовой пояс во временные данные
    await state.update_data(timezone=timezone)

    # Запрос возрастной группы
    await callback.message.answer("📅 Выберите вашу возрастную группу:",
                                  reply_markup=get_age_group_keyboard())
    await Registration.age_group.set()
    await callback.answer()


async def process_age_group(callback: types.CallbackQuery, state: FSMContext):
    age_group = callback.data.split('_')[1]  # "14-17" или "18-25"
    user_data = await state.get_data()
    full_name = user_data['full_name']
    timezone = user_data.get('timezone', 'UTC+3')
    user_id = callback.from_user.id

    logger.info(f"User {user_id} selected age group: {age_group}")

    # Убираем кнопки выбора возрастной группы
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # По умолчанию все пользователи становятся АДМИНАМИ
    role = 'admin'

    # Сохраняем данные пользователя
    await User.add_user(user_id, callback.from_user.username, full_name, role, age_group)
    await User.update_user(user_id, full_name, timezone, age_group)

    # Приветственное сообщение о группах
    groups_text = (
        "🎉 Регистрация завершена! Теперь ты полноправный участник нашего Финансового Университета!\n\n"
        "Присоединяйся к нашим сообществам:\n"
        "• Основной чат участников: @financial_university_chat\n"
        "• Чат проекта: @financial_university_project\n\n"
        "Там ты сможешь общаться с другими участниками, задавать вопросы и получать дополнительные материалы!"
    )

    # Все пользователи - админы
    admin_modes[user_id] = 'admin'
    await callback.message.answer(groups_text, reply_markup=admin_kb.kb_admin)

    await state.finish()
    await callback.answer()


async def request_support(message: types.Message):
    await message.answer("✍️ Опишите ваш вопрос или проблему. Мы ответим как можно скорее!")
    await SupportState.waiting_for_question.set()


async def process_support_question(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await User.get_user(user_id)

    if user_data:
        username = message.from_user.username
        full_name = user_data[2]  # full_name
        role = user_data[3]  # role

        # Сохраняем обращение в базу данных
        await User.create_support_ticket(user_id, username, full_name, role, message.text)

        await message.answer("✅ Ваше обращение зарегистрировано! Мы свяжемся с вами в ближайшее время.")

    await state.finish()


def register_handlers_common(dp):
    dp.register_message_handler(cmd_start, commands=['start'], state=None)
    dp.register_message_handler(process_full_name, state=Registration.full_name)
    dp.register_callback_query_handler(process_timezone, state=Registration.timezone)
    dp.register_callback_query_handler(process_age_group, state=Registration.age_group)
    dp.register_message_handler(request_support, text='🆘 Поддержка', state=None)
    dp.register_message_handler(process_support_question, state=SupportState.waiting_for_question)