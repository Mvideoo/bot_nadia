import asyncio
from datetime import datetime, timedelta

import pytz

from keyboards import admin_kb, student_kb
from utils.storage import admin_modes
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from data_base.models.user import User
from keyboards import quest_management_kb
import logging
import re
from keyboards.common import get_cancel_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logger = logging.getLogger(__name__)

class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_time = State()

async def admin_broadcast(message: types.Message):
    await BroadcastState.waiting_for_message.set()
    await message.answer("📝 Введите сообщение для рассылки:")

async def process_broadcast_message(message: types.Message, state: FSMContext):
    await state.update_data(message=message.text)
    await BroadcastState.next()
    await message.answer("⏰ Введите время отправки по Москве (в формате ЧЧ:ММ, например 12:00):")


async def process_broadcast_time(message: types.Message, state: FSMContext):
    time_pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
    if not re.match(time_pattern, message.text):
        await message.answer("❌ Неверный формат времени. Введите время в формате ЧЧ:ММ (например, 12:00):")
        return

    data = await state.get_data()
    message_text = data['message']
    scheduled_time = message.text  # время по Москве (UTC+3)

    # Сохраняем рассылку
    await User.add_broadcast(message_text, scheduled_time)

    # Запускаем отложенную рассылку
    asyncio.create_task(schedule_broadcast(message_text, scheduled_time))

    await message.answer(f"✅ Рассылка запланирована на {scheduled_time} по Москве!")
    await state.finish()


async def schedule_broadcast(message_text: str, scheduled_time: str):
    try:
        # Текущее время по Москве
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)

        # Парсим время отправки
        hour, minute = map(int, scheduled_time.split(':'))
        send_time = now_msk.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Если время уже прошло сегодня, переносим на завтра
        if send_time < now_msk:
            send_time += timedelta(days=1)

        # Вычисляем задержку в секундах
        delay = (send_time - now_msk).total_seconds()

        # Ждем до времени отправки
        logger.info(f"Ожидание {delay} секунд до рассылки в {scheduled_time} МСК")
        await asyncio.sleep(delay)

        # Получаем всех пользователей
        users = await User.get_all_users()

        # Отправляем сообщение каждому пользователю
        for user in users:
            user_id = user[0]
            try:
                await bot.send_message(user_id, f"📢 Рассылка от администратора:\n\n{message_text}")
                logger.info(f"Сообщение рассылки отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки рассылки пользователю {user_id}: {str(e)}")

        logger.info(f"Рассылка успешно завершена!")

    except Exception as e:
        logger.error(f"Ошибка в процессе рассылки: {str(e)}")

class SupportAnswerState(StatesGroup):
    waiting_for_answer = State()


async def admin_manage_support(message: types.Message):
    logger.info(f"Admin {message.from_user.id} accessed support management")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('📬 Открытые обращения'),
        KeyboardButton('📭 Закрытые обращения'),
        KeyboardButton('🔙 В админ-панель')
    )
    await message.answer("Управление обращениями в поддержку:", reply_markup=keyboard)


async def admin_closed_tickets(message: types.Message):
    # Получаем закрытые обращения (статус 'answered' или 'closed')
    tickets = await User.get_closed_tickets()

    if not tickets:
        await message.answer("📭 Нет закрытых обращений")
        return

    response = "📭 <b>Закрытые обращения:</b>\n\n"

    for ticket in tickets:
        ticket_id = ticket[0]
        username = ticket[2] or ""
        full_name = ticket[3] or ""
        role = ticket[4] or ""
        message_text = ticket[5] or ""
        created_at = ticket[6] or ""
        status = ticket[7] or ""
        admin_response = ticket[9] or ""
        response_at = ticket[10] or ""

        # Ограничиваем длину сообщения для вывода
        short_message = message_text[:100] + "..." if len(message_text) > 100 else message_text
        short_response = admin_response[:100] + "..." if len(admin_response) > 100 else admin_response

        response += (
            f"<b>ID:{ticket_id}</b> [{created_at.split()[0]}]\n"
            f"👤 {full_name} (@{username}) [{role}]\n"
            f"💬 {short_message}\n"
            f"📩 Ответ: {short_response}\n"
            f"🕒 Ответ дан: {response_at.split()[0]}\n\n"
        )

    await message.answer(response, parse_mode="HTML")


async def admin_open_tickets(message: types.Message):
    tickets = await User.get_open_tickets()

    if not tickets:
        await message.answer("📭 Нет открытых обращений")
        return

    response = "📬 <b>Открытые обращения:</b>\n\n"
    keyboard = InlineKeyboardMarkup(row_width=1)

    for ticket in tickets:
        ticket_id = ticket[0]
        user_id = ticket[1]
        username = ticket[2] or ""
        full_name = ticket[3] or ""
        role = ticket[4] or ""
        message_text = ticket[5] or ""
        created_at = ticket[6] or ""

        # Ограничиваем длину сообщения для вывода
        short_message = message_text[:100] + "..." if len(message_text) > 100 else message_text

        response += f"<b>ID:{ticket_id}</b> [{created_at.split()[0]}]\n👤 {full_name} (@{username}) [{role}]\n💬 {short_message}\n\n"
        keyboard.add(InlineKeyboardButton(
            f"Ответить на обращение ID:{ticket_id}",
            callback_data=f"answer_ticket_{ticket_id}"
        ))

    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('answer_ticket_'), active_role='admin')
async def start_answer_ticket(callback: types.CallbackQuery, state: FSMContext):
    ticket_id = int(callback.data.split('_')[2])
    await state.update_data(ticket_id=ticket_id)
    await callback.message.answer(
        f"✍️ Введите ответ на обращение #{ticket_id}:",
        reply_markup=get_cancel_kb()
    )
    await SupportAnswerState.waiting_for_answer.set()
    await callback.answer()


@dp.message_handler(state=SupportAnswerState.waiting_for_answer, active_role='admin')
async def process_support_answer(message: types.Message, state: FSMContext):
    if message.text == '❌ Отмена':
        await cancel_any_action(message, state)
        return

    data = await state.get_data()
    ticket_id = data['ticket_id']
    admin_id = message.from_user.id

    # Сохраняем ответ
    await User.answer_ticket(ticket_id, admin_id, message.text)

    # Отправляем ответ пользователю
    ticket = await User.get_ticket(ticket_id)
    if ticket:
        user_id = ticket[1]
        try:
            await bot.send_message(
                user_id,
                f"📩 <b>Ответ на ваше обращение #{ticket_id}:</b>\n\n{message.text}\n\n"
                "Если ваш вопрос решен, больше ничего не требуется. Если нет - напишите снова!",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending response to user {user_id}: {str(e)}")

    await message.answer(f"✅ Ответ на обращение #{ticket_id} отправлен пользователю!")
    await state.finish()

class AddQuestState(StatesGroup):
    title = State()
    description = State()
    time = State()
    confirm = State()  # Новое состояние для подтверждения



async def admin_manage_quests(message: types.Message):
    logger.info(f"Admin {message.from_user.id} accessed quest management")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('📋 Список квестов'),
        KeyboardButton('➕ Добавить квест'),
        KeyboardButton('🔙 В админ-панель')
    )
    await message.answer("Управление квестами:", reply_markup=keyboard)


async def admin_list_quests(message: types.Message):
    quests = await User.get_all_quests()

    if not quests:
        await message.answer("Нет активных квестов")
        return

    response = "📋 <b>Список квестов:</b>\n\n"
    keyboard = InlineKeyboardMarkup(row_width=2)

    for quest in quests:
        quest_id, title, description, time_utc3, active = quest
        status = "✅ Активен" if active else "❌ Неактивен"
        response += f"<b>ID {quest_id}: {title}</b>\n{description}\n⏰ Время: {time_utc3} МСК\nСтатус: {status}\n\n"

        keyboard.add(InlineKeyboardButton(
            f"{'❌ Деактивировать' if active else '✅ Активировать'} {quest_id}",
            callback_data=f"toggle_quest_{quest_id}_{1 if not active else 0}"
        ))

    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)


async def process_quest_confirm(message: types.Message, state: FSMContext):
    if message.text == '❌ Отмена':
        await cancel_quest_creation(message, state)
        return

    if message.text == '✅ Подтвердить':
        data = await state.get_data()
        await User.add_quest(data['title'], data['description'], data['time'])
        await message.answer(f"✅ Квест '{data['title']}' добавлен!", reply_markup=admin_kb.kb_admin)
    else:
        await message.answer("Используйте кнопки для подтверждения или отмены")
        return

    await state.finish()

async def cancel_quest_creation(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Создание квеста отменено", reply_markup=admin_kb.kb_admin)

async def admin_add_quest(message: types.Message):
    await AddQuestState.name.set()
    await message.answer("Введите название квеста:", reply_markup=get_cancel_kb())


async def process_quest_title(message: types.Message, state: FSMContext):
    if message.text == '❌ Отмена':
        await cancel_quest_creation(message, state)
        return

    await state.update_data(title=message.text)
    await AddQuestState.next()
    await message.answer("Введите описание квеста:", reply_markup=get_cancel_kb())


async def process_quest_description(message: types.Message, state: FSMContext):
    if message.text == '❌ Отмена':
        await cancel_quest_creation(message, state)
        return

    await state.update_data(description=message.text)
    await AddQuestState.next()
    await message.answer("Введите время отправки по МСК (например, 10:00):", reply_markup=get_cancel_kb())


async def process_quest_time(message: types.Message, state: FSMContext):
    if message.text == '❌ Отмена':
        await cancel_quest_creation(message, state)
        return

    time_str = message.text.strip()

    # Проверка формата времени
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ (например, 09:30)\nПопробуйте снова:")
        return

    await state.update_data(time=time_str)

    # Показываем подтверждение
    data = await state.get_data()
    confirm_text = (
        "✅ Подтвердите создание квеста:\n\n"
        f"<b>Название:</b> {data['title']}\n"
        f"<b>Описание:</b> {data['description']}\n"
        f"<b>Время отправки:</b> {data['time']} МСК"
    )

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton('✅ Подтвердить'), KeyboardButton('❌ Отмена'))

    await AddQuestState.next()
    await message.answer(confirm_text, parse_mode="HTML", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == '❌ Отмена', state='*')
async def cancel_any_action(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    # Определяем, какое действие отменяем
    if 'AddQuestState' in current_state:
        action_name = "создание квеста"
    elif 'SupportAnswerState' in current_state:
        action_name = "ответ на обращение"
    else:
        action_name = "действие"

    await state.finish()
    await message.answer(f"❌ {action_name.capitalize()} отменено", reply_markup=admin_kb.kb_admin)

@dp.callback_query_handler(lambda c: c.data.startswith('toggle_quest_'))
async def toggle_quest(callback: types.CallbackQuery):
    data = callback.data.split('_')
    quest_id = int(data[2])
    activate = bool(int(data[3]))

    await User.toggle_quest(quest_id, activate)
    action = "активирован" if activate else "деактивирован"
    await callback.answer(f"Квест {action}")

    # Обновляем список квестов
    await admin_list_quests(callback.message)

async def admin_start(message: types.Message):
    user_id = message.from_user.id
    admin_modes[user_id] = 'admin'
    logger.info(f"Admin panel opened by {user_id}")
    await message.answer("Панель администратора", reply_markup=admin_kb.kb_admin)

async def admin_manage_users(message: types.Message):
    logger.info(f"Admin {message.from_user.id} accessed user management")
    await message.answer("Раздел управления пользователями")

async def admin_finance_stats(message: types.Message):
    logger.info(f"Admin {message.from_user.id} accessed finance stats")
    await message.answer("Финансовая статистика")

async def admin_student_mode(message: types.Message):
    user_id = message.from_user.id
    admin_modes[user_id] = 'student'
    logger.info(f"Admin {user_id} switched to student mode")
    await message.answer("Режим ученика активирован", reply_markup=student_kb.kb_student)


async def back_to_admin_panel(message: types.Message):
    user_id = message.from_user.id
    admin_modes[user_id] = 'admin'
    logger.info(f"Admin {user_id} returned to admin panel")
    await message.answer("Возврат в админ-панель", reply_markup=admin_kb.kb_admin)



class AddShopItem(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()


async def admin_manage_shop(message: types.Message):
    logger.info(f"Admin {message.from_user.id} accessed shop management")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('📋 Список товаров'),
        KeyboardButton('➕ Добавить товар'),
        KeyboardButton('🔙 В админ-панель')
    )
    await message.answer("Управление магазином:", reply_markup=keyboard)


async def admin_list_shop_items(message: types.Message):
    items = await User.get_shop_items()

    if not items:
        await message.answer("🛒 В магазине пока нет товаров")
        return

    response = "🛒 <b>Товары в магазине:</b>\n\n"
    for item in items:
        _, name, description, price, category = item
        response += f"<b>{name}</b>\n{description}\n💰 Цена: {price} монет\n🏷️ Категория: {category}\n\n"

    await message.answer(response, parse_mode="HTML")


async def admin_add_shop_item(message: types.Message):
    await AddShopItem.name.set()
    await message.answer("Введите название товара:")


async def process_shop_item_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await AddShopItem.next()
    await message.answer("Введите описание товара:")


async def process_shop_item_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await AddShopItem.next()
    await message.answer("Введите цену товара (в монетах):")


async def process_shop_item_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        if price <= 0:
            raise ValueError
    except:
        await message.answer("❌ Неверная цена. Введите целое положительное число")
        return

    await state.update_data(price=price)
    await AddShopItem.next()

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('Мерч'),
        KeyboardButton('Помощь экспертов')
    )
    await message.answer("Выберите категорию товара:", reply_markup=keyboard)


async def process_shop_item_category(message: types.Message, state: FSMContext):
    category = message.text
    if category not in ['Мерч', 'Помощь экспертов']:
        await message.answer("❌ Неверная категория. Выберите из предложенных")
        return

    data = await state.get_data()
    await User.add_shop_item(data['name'], data['description'], data['price'], category)
    await state.finish()

    # Возвращаем стандартную клавиатуру
    await admin_manage_shop(message)
    await message.answer(f"✅ Товар '{data['name']}' успешно добавлен в магазин")


def register_handlers_admin(dp):
    dp.register_message_handler(admin_manage_quests, text='🎯 Управление квестами', active_role='admin')
    dp.register_message_handler(admin_list_quests, text='📋 Список квестов', active_role='admin')
    dp.register_message_handler(admin_add_quest, text='➕ Добавить квест', active_role='admin')

    dp.register_message_handler(admin_start, commands=['start'], active_role='admin')
    dp.register_message_handler(process_quest_title, state=AddQuestState.title)
    dp.register_message_handler(process_quest_description, state=AddQuestState.description)
    dp.register_message_handler(process_quest_time, state=AddQuestState.time)
    dp.register_message_handler(admin_broadcast, text='📢 Рассылка', active_role='admin')
    dp.register_message_handler(process_broadcast_message, state=BroadcastState.waiting_for_message)
    dp.register_message_handler(process_broadcast_time, state=BroadcastState.waiting_for_time)
    dp.register_message_handler(admin_manage_shop, text='🛒 Управление магазином', active_role='admin')
    dp.register_message_handler(admin_list_shop_items, text='📋 Список товаров', active_role='admin')
    dp.register_message_handler(admin_add_shop_item, text='➕ Добавить товар', active_role='admin')
    dp.register_message_handler(admin_manage_support, text='📭 Управление поддержкой', active_role='admin')
    dp.register_message_handler(admin_open_tickets, text='📬 Открытые обращения', active_role='admin')
    dp.register_message_handler(admin_closed_tickets, text='📭 Закрытые обращения', active_role='admin')
    dp.register_message_handler(process_support_answer, state=SupportAnswerState.waiting_for_answer, active_role='admin')
    dp.register_message_handler(process_shop_item_name, state=AddShopItem.name)
    dp.register_message_handler(process_shop_item_description, state=AddShopItem.description)
    dp.register_message_handler(process_shop_item_price, state=AddShopItem.price)
    dp.register_message_handler(process_shop_item_category, state=AddShopItem.category)
    dp.register_message_handler(admin_finance_stats, text='📊 Финансовая статистика', active_role='admin')
    dp.register_message_handler(admin_broadcast, text='📢 Рассылка', active_role='admin')
    dp.register_message_handler(admin_student_mode, text='🎓 Режим ученика', active_role='admin')
    dp.register_message_handler(back_to_admin_panel, text='🔙 В админ-панель', active_role='admin')
    dp.register_message_handler(cancel_any_action, lambda message: message.text == '❌ Отмена', state='*')
