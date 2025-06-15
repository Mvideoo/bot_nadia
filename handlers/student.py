from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from create_bot import dp
from data_base.models.user import User
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from data_base import db
import logging
from keyboards import admin_kb
from keyboards.common import get_timezone_keyboard, get_age_group_keyboard

logger = logging.getLogger(__name__)

# Информация об олимпиадах и подготовке
OLYMPIADS_INFO = {
    "overview": {
        "title": "🏅 Олимпиады по экономике",
        "description": (
            "Участие в олимпиадах по экономике - отличный способ проверить свои знания, "
            "получить льготы при поступлении в вузы и расширить кругозор. Вот основные олимпиады:"
        ),
        "olympiads": [
            "• Всероссийская олимпиада школьников (ВсОШ)",
            "• Московская олимпиада школьников",
            "• Олимпиада «Высшая проба» (НИУ ВШЭ)",
            "• Олимпиада «Ломоносов» (МГУ)",
            "• Олимпиада СПбГУ по экономике",
            "• Олимпиада «Финатлон» для старшеклассников"
        ]
    },
    "vos": {
        "title": "Всероссийская олимпиада школьников (ВсОШ)",
        "description": (
            "🔹 <b>Самый престижный конкурс</b> для школьников России\n"
            "🔹 Проводится в 4 этапа: школьный, муниципальный, региональный, заключительный\n"
            "🔹 Победители и призеры получают льготы при поступлении в вузы\n"
            "🔹 <b>Сроки проведения:</b> октябрь-апрель\n\n"
            "<b>Ресурсы для подготовки:</b>\n"
            "• Официальный сайт: <a href='https://olimpiada.ru/activity/43'>olimpiada.ru</a>\n"
            "• Задачи прошлых лет с решениями\n"
            "• Онлайн-курсы на Stepik и Лекториуме"
        )
    },
    "mos": {
        "title": "Московская олимпиада школьников",
        "description": (
            "🔹 <b>Крупная региональная олимпиада</b> с участием школьников со всей России\n"
            "🔹 Входит в Перечень олимпиад Минобрнауки России\n"
            "🔹 <b>Сроки проведения:</b> декабрь-март\n\n"
            "<b>Ресурсы для подготовки:</b>\n"
            "• Официальный сайт: <a href='https://mos.olimpiada.ru/'>mos.olimpiada.ru</a>\n"
            "• Архив задач прошлых лет\n"
            "• Подготовительные курсы в ЦПМ"
        )
    },
    "vysshaya_proba": {
        "title": "Олимпиада «Высшая проба»",
        "description": (
            "🔹 <b>Олимпиада от НИУ ВШЭ</b> с международным участием\n"
            "🔹 Проводится для 7-11 классов\n"
            "🔹 <b>Сроки проведения:</b> ноябрь-апрель\n\n"
            "<b>Ресурсы для подготовки:</b>\n"
            "• Официальный сайт: <a href='https://olymp.hse.ru/mmo/'>olymp.hse.ru/mmo</a>\n"
            "• Пробные туры и тренировочные задания\n"
            "• Вебинары от преподавателей ВШЭ"
        )
    },
    "lomonosov": {
        "title": "Олимпиада «Ломоносов»",
        "description": (
            "🔹 <b>Олимпиада МГУ им. М.В. Ломоносова</b>\n"
            "🔹 Включает экономическое направление\n"
            "🔹 <b>Сроки проведения:</b> октябрь-март\n\n"
            "<b>Ресурсы для подготовки:</b>\n"
            "• Официальный сайт: <a href='https://olymp.msu.ru/'>olymp.msu.ru</a>\n"
            "• Задачи прошлых лет с решениями\n"
            "• Подготовительные курсы Экономического факультета МГУ"
        )
    },
    "sirius": {
        "title": "Центр «Сириус»",
        "description": (
            "🔹 <b>Образовательный центр для одаренных детей</b>\n"
            "🔹 Проводит интенсивные программы подготовки к олимпиадам\n"
            "🔹 <b>Как попасть:</b> через конкурсный отбор\n\n"
            "<b>Ресурсы:</b>\n"
            "• Официальный сайт: <a href='https://sochisirius.ru/'>sochisirius.ru</a>\n"
            "• Онлайн-курсы по экономике\n"
            "• Вебинары с победителями олимпиад"
        )
    },
    "vzlet": {
        "title": "Платформа «Взлёт»",
        "description": (
            "🔹 <b>Региональный центр поддержки одаренных детей</b> в Московской области\n"
            "🔹 Проводит олимпиадные сборы и подготовительные программы\n"
            "🔹 <b>Направления:</b> экономика, финансовая грамотность\n\n"
            "<b>Ресурсы:</b>\n"
            "• Официальный сайт: <a href='https://olympmo.ru/'>olympmo.ru</a>\n"
            "• Дистанционные курсы\n"
            "• Очные смены в Подмосковье"
        )
    }
}


class EditProfile(StatesGroup):
    waiting_edit_choice = State()
    waiting_new_fio = State()
    waiting_new_timezone = State()
    waiting_new_age_group = State()


async def show_profile(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Profile accessed by {user_id}")
    user_data = await User.get_user(user_id)

    if user_data:
        full_name = user_data[2]  # full_name
        coins = user_data[5]  # coins
        timezone = user_data[4]  # timezone
        age_group = user_data[6]  # age_group

        profile_text = (
            f"👤 <b>Ваш профиль</b>\n\n"
            f"📛 <b>ФИО:</b> {full_name}\n"
            f"🎂 <b>Возрастная группа:</b> {age_group}\n"
            f"💰 <b>Финкоины:</b> {coins}\n"
            f"⏰ <b>Часовой пояс:</b> {timezone}\n\n"
            "Финкоины можно заработать, выполняя задания и проходя уроки!"
        )

        # Добавляем кнопку редактирования
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("✏️ Редактировать профиль", callback_data="edit_profile"))

        await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'edit_profile')
async def edit_profile_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Изменить ФИО", callback_data="edit_fio"),
        InlineKeyboardButton("Изменить часовой пояс", callback_data="edit_timezone"),
        InlineKeyboardButton("Изменить возрастную группу", callback_data="edit_age_group")
    )
    await callback.message.answer("Что вы хотите изменить?", reply_markup=keyboard)
    await EditProfile.waiting_edit_choice.set()
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('edit_'), state=EditProfile.waiting_edit_choice)
async def process_edit_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data
    if choice == 'edit_fio':
        await callback.message.answer("Введите новое ФИО:")
        await EditProfile.waiting_new_fio.set()
    elif choice == 'edit_timezone':
        await callback.message.answer("Выберите новый часовой пояс:", reply_markup=get_timezone_keyboard())
        await EditProfile.waiting_new_timezone.set()
    elif choice == 'edit_age_group':
        await callback.message.answer("Выберите новую возрастную группу:", reply_markup=get_age_group_keyboard())
        await EditProfile.waiting_new_age_group.set()
    await callback.answer()


@dp.message_handler(state=EditProfile.waiting_new_fio)
async def process_new_fio(message: types.Message, state: FSMContext):
    new_fio = message.text
    user_id = message.from_user.id

    # Обновляем ФИО в базе данных
    await User.update_user(user_id, full_name=new_fio)

    await message.answer("✅ ФИО успешно изменено!")
    await state.finish()

    # Показываем обновленный профиль
    await show_profile(message)


async def process_new_timezone(callback: types.CallbackQuery, state: FSMContext):
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
    user_id = callback.from_user.id

    # Обновляем часовой пояс
    await User.update_user(user_id, timezone=timezone)

    await callback.message.answer(f"✅ Часовой пояс изменен на {timezone}")
    await state.finish()

    # Показываем обновленный профиль
    await show_profile(callback.message)


@dp.callback_query_handler(lambda c: c.data in ["age_14-17", "age_18-25"], state=EditProfile.waiting_new_age_group)
async def process_new_age_group(callback: types.CallbackQuery, state: FSMContext):
    age_group = callback.data.split('_')[1]  # "14-17" или "18-25"
    user_id = callback.from_user.id

    # Обновляем возрастную группу
    await User.update_user(user_id, age_group=age_group)

    await callback.message.answer(f"✅ Возрастная группа изменена на {age_group}")
    await state.finish()

    # Показываем обновленный профиль
    await show_profile(callback.message)


# ... остальные функции student.py ...

async def show_quests(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Quests accessed by {user_id}")

    try:
        # Удаляем предыдущее сообщение с квестами, если оно есть
        # (чтобы избежать накопления сообщений при многократном нажатии)
        await message.delete()
    except:
        pass

    try:
        quests = await User.get_today_quests_for_user(user_id)

        if not quests:
            await message.answer("🎯 На сегодня квестов нет! Загляните завтра.")
            return

        response = "🎯 <b>Ваши квесты на сегодня:</b>\n\n"
        keyboard = InlineKeyboardMarkup()

        for quest in quests:
            quest_id, title, description, completed = quest
            status = "✅ Выполнен" if completed else "❌ Не выполнен"
            response += f"<b>{title}</b>\n{description}\nСтатус: {status}\n\n"

            if not completed:
                keyboard.add(InlineKeyboardButton(
                    f"Отметить выполнение: {title}",
                    callback_data=f"complete_quest_{quest_id}"
                ))

        # Отправляем новое сообщение с квестами
        await message.answer(response, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error showing quests: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при загрузке квестов. Попробуйте позже.")


@dp.callback_query_handler(lambda c: c.data.startswith('complete_quest_'), active_role='student')
async def complete_quest(callback: types.CallbackQuery):
    try:
        quest_id = int(callback.data.split('_')[2])
        user_id = callback.from_user.id

        # Отмечаем квест выполненным
        await User.mark_quest_completed(user_id, quest_id)

        # Получаем обновленный список квестов
        quests = await User.get_today_quests_for_user(user_id)

        if not quests:
            # Если квестов нет, редактируем сообщение
            await callback.message.edit_text(
                "🎯 Все квесты на сегодня выполнены! Загляните завтра.",
                reply_markup=None
            )
            await callback.answer("✅ Квест выполнен! +10 монет")
            return

        # Формируем обновленный текст и клавиатуру
        response = "🎯 <b>Ваши квесты на сегодня:</b>\n\n"
        keyboard = InlineKeyboardMarkup()

        for quest in quests:
            q_id, title, description, completed = quest
            status = "✅ Выполнен" if completed else "❌ Не выполнен"
            response += f"<b>{title}</b>\n{description}\nСтатус: {status}\n\n"

            if not completed:
                keyboard.add(InlineKeyboardButton(
                    f"Отметить выполнение: {title}",
                    callback_data=f"complete_quest_{q_id}"
                ))

        # Редактируем исходное сообщение
        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await callback.answer("✅ Квест выполнен! +10 монет")

    except Exception as e:
        logger.error(f"Error completing quest: {str(e)}")
        await callback.answer("⚠️ Ошибка при выполнении квеста")


async def show_achievements(message: types.Message):
    logger.info(f"Achievements accessed by {message.from_user.id}")
    await message.answer("Ваши достижения")


async def show_tasks(message: types.Message):
    logger.info(f"Tasks accessed by {message.from_user.id}")
    await message.answer("Ваши задания")


async def show_olympiads(message: types.Message):
    logger.info(f"Olympiads info accessed by {message.from_user.id}")

    try:
        # Удаляем предыдущее сообщение об олимпиадах, если оно есть
        await message.delete()
    except:
        pass

    # Создаем клавиатуру с кнопками олимпиад
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("ВсОШ", callback_data="olympiad_vos"),
        InlineKeyboardButton("Московская", callback_data="olympiad_mos"),
        InlineKeyboardButton("Высшая проба", callback_data="olympiad_vysshaya_proba"),
        InlineKeyboardButton("Ломоносов", callback_data="olympiad_lomonosov"),
        InlineKeyboardButton("Центр «Сириус»", callback_data="olympiad_sirius"),
        InlineKeyboardButton("Платформа «Взлёт»", callback_data="olympiad_vzlet"),
    )

    # Отправляем новое сообщение
    await message.answer(
        "🏅 <b>Подготовка к олимпиадам по экономике</b>\n\n"
        "Выберите олимпиаду или ресурс для подготовки, чтобы узнать подробности:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ... предыдущий код ...

@dp.callback_query_handler(lambda c: c.data == 'olympiad_overview', active_role='student')
async def show_olympiads_overview(callback: types.CallbackQuery):
    """Показывает общий список олимпиад (главное меню)"""
    # Создаем клавиатуру с кнопками олимпиад
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("ВсОШ", callback_data="olympiad_vos"),
        InlineKeyboardButton("Московская", callback_data="olympiad_mos"),
        InlineKeyboardButton("Высшая проба", callback_data="olympiad_vysshaya_proba"),
        InlineKeyboardButton("Ломоносов", callback_data="olympiad_lomonosov"),
        InlineKeyboardButton("Центр «Сириус»", callback_data="olympiad_sirius"),
        InlineKeyboardButton("Платформа «Взлёт»", callback_data="olympiad_vzlet"),
    )

    # Редактируем текущее сообщение, чтобы вернуться к списку
    await callback.message.edit_text(
        "🏅 <b>Подготовка к олимпиадам по экономике</b>\n\n"
        "Выберите олимпиаду или ресурс для подготовки, чтобы узнать подробности:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('olympiad_') and c.data != 'olympiad_overview',
                           active_role='student')
async def show_olympiad_details(callback: types.CallbackQuery):
    olympiad_key = callback.data.split('_', 1)[1]
    olympiad_info = OLYMPIADS_INFO.get(olympiad_key)

    if not olympiad_info:
        await callback.answer("Информация не найдена")
        return

    # Создаем кнопку для возврата к списку олимпиад
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("← Назад к списку олимпиад", callback_data="olympiad_overview"))

    # Отправляем информацию об олимпиаде
    await callback.message.edit_text(
        f"<b>{olympiad_info['title']}</b>\n\n"
        f"{olympiad_info.get('description', '')}",
        parse_mode="HTML",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
    await callback.answer()


# ... остальной код ...
async def show_shop(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Shop accessed by {user_id}")

    # Создаем клавиатуру категорий
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎁 Мерч", callback_data="shop_category_merch"),
        InlineKeyboardButton("💼 Помощь экспертов", callback_data="shop_category_expert"),
        InlineKeyboardButton("📦 Мои покупки", callback_data="shop_my_purchases")
    )

    user_coins = await User.get_coins(user_id)
    await message.answer(
        f"🛒 <b>Магазин финкоинов</b>\n\n"
        f"💰 Ваш баланс: {user_coins} монет\n\n"
        "Выберите категорию товаров:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith('shop_category_'), active_role='student')
async def show_shop_category(callback: types.CallbackQuery):
    category = callback.data.split('_')[2]
    user_id = callback.from_user.id
    user_coins = await User.get_coins(user_id)

    items = await User.get_shop_items(category)

    if not items:
        await callback.answer("😢 В этой категории пока нет товаров")
        return

    response = f"🛒 <b>Товары в категории {'мерч' if category == 'merch' else 'помощь экспертов'}:</b>\n\n"
    keyboard = InlineKeyboardMarkup(row_width=1)

    for item in items:
        item_id, name, description, price, _ = item
        response += f"<b>{name}</b>\n{description}\n💰 Цена: {price} монет\n\n"
        keyboard.add(InlineKeyboardButton(
            f"Купить {name} - {price} монет",
            callback_data=f"buy_item_{item_id}"
        ))

    keyboard.add(InlineKeyboardButton("← Назад в магазин", callback_data="shop_back"))

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('buy_item_'), active_role='student')
async def buy_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id

    success, message = await User.purchase_item(user_id, item_id)

    if success:
        # Обновляем баланс в сообщении
        user_coins = await User.get_coins(user_id)
        await callback.message.edit_text(
            f"{message}\n\n💰 Ваш новый баланс: {user_coins} монет",
            reply_markup=callback.message.reply_markup
        )
    else:
        await callback.answer(message)


@dp.callback_query_handler(lambda c: c.data == 'shop_my_purchases', active_role='student')
async def show_my_purchases(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    purchases = await User.get_user_purchases(user_id)

    if not purchases:
        response = "📭 У вас пока нет покупок"
    else:
        response = "📦 <b>Ваши покупки:</b>\n\n"
        for purchase in purchases:
            _, name, description, date = purchase
            response += f"<b>{name}</b>\n{description}\n🕒 Дата: {date}\n\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("← Назад в магазин", callback_data="shop_back"))

    await callback.message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == 'shop_back', active_role='student')
async def back_to_shop(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_coins = await User.get_coins(user_id)

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎁 Мерч", callback_data="shop_category_merch"),
        InlineKeyboardButton("💼 Помощь экспертов", callback_data="shop_category_expert"),
        InlineKeyboardButton("📦 Мои покупки", callback_data="shop_my_purchases")
    )

    await callback.message.edit_text(
        f"🛒 <b>Магазин финкоинов</b>\n\n"
        f"💰 Ваш баланс: {user_coins} монет\n\n"
        "Выберите категорию товаров:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


async def back_to_admin_panel(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Student {user_id} returning to admin panel")
    await message.answer("Возврат в админ-панель", reply_markup=admin_kb.kb_admin)


async def show_support_history(message: types.Message):
    user_id = message.from_user.id
    tickets = await User.get_user_tickets(user_id)

    if not tickets:
        await message.answer("📭 У вас пока нет обращений в поддержку")
        return

    response = "📬 <b>История ваших обращений:</b>\n\n"

    for ticket in tickets:
        ticket_id = ticket[0]
        message_text = ticket[5] or ""
        created_at = ticket[6] or ""
        status = ticket[7] or "open"
        admin_response = ticket[9] or ""
        response_at = ticket[10] or ""

        status_icon = "🟢" if status == 'open' else "🔵" if status == 'answered' else "⚫"

        # Ограничиваем длину сообщения для вывода
        short_message = message_text[:100] + "..." if len(message_text) > 100 else message_text

        response += f"{status_icon} <b>ID:{ticket_id}</b> [{created_at.split()[0]}]\n"
        response += f"💬 Ваш вопрос: {short_message}\n"

        if admin_response:
            # Ограничиваем длину ответа для вывода
            short_response = admin_response[:100] + "..." if len(admin_response) > 100 else admin_response
            response += f"📩 Ответ поддержки: {short_response}\n"
            response += f"🕒 Дата ответа: {response_at.split()[0]}\n"
        else:
            response += "⏳ Ожидает ответа...\n"

        response += "\n"

    await message.answer(response, parse_mode="HTML")


async def show_rating(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"Rating accessed by {user_id}")

    # Получаем топ-5 учеников по монетам
    top_users = await User.get_top_students(5)
    print(top_users)

    if not top_users:
        await message.answer("🏆 Рейтинг пока пуст. Будьте первым!")
        return

    response = "🏆 <b>Топ-5 учеников по монетам:</b>\n\n"

    # Формируем рейтинг
    for i, user in enumerate(top_users):
        user_id, username, full_name, coins = user
        place = i + 1
        medal = "🥇" if place == 1 else "🥈" if place == 2 else "🥉" if place == 3 else "🔸"

        # Обрезаем длинные имена
        display_name = full_name[:20] + "..." if len(full_name) > 20 else full_name

        response += f"{medal} {place}. {display_name} - {coins} монет\n"
        if username:
            response += f"   👤 @{username}\n"
        response += "\n"

    # Добавляем текущее место пользователя
    user_position = await User.get_user_position(user_id)
    user_coins = await db.get_coins(user_id)

    if user_position:
        response += f"\nВаше место в рейтинге: #{user_position}\n"
        response += f"Ваши монеты: {user_coins}"
    else:
        response += f"\nВаши монеты: {user_coins}"

    await message.answer(response, parse_mode="HTML")


def register_handlers_student(dp):
    dp.register_message_handler(show_support_history, text='📬 Мои обращения', active_role='student')
    dp.register_message_handler(show_profile, text='👤 Профиль', active_role='student')
    dp.register_message_handler(show_rating, text='🏆 Рейтинг', active_role=None)
    dp.register_message_handler(show_quests, text='🎯 Квесты', active_role='student')
    dp.register_message_handler(show_olympiads, text='🏅 Олимпиады по экономике', active_role='student')
    dp.register_message_handler(show_shop, text='🛒 Магазин', active_role='student')
    dp.register_message_handler(back_to_admin_panel, text='🔙 В админ-панель', active_role='student')
    dp.register_callback_query_handler(complete_quest, lambda c: c.data.startswith('complete_quest_'))
    dp.register_callback_query_handler(show_olympiads_overview, lambda c: c.data == 'olympiad_overview')
    dp.register_callback_query_handler(show_olympiad_details,
                                       lambda c: c.data.startswith('olympiad_') and c.data != 'olympiad_overview')
    # Регистрация обработчиков редактирования профиля
    dp.register_callback_query_handler(edit_profile_callback, lambda c: c.data == 'edit_profile')
    dp.register_callback_query_handler(process_edit_choice, lambda c: c.data.startswith('edit_'),
                                       state=EditProfile.waiting_edit_choice)
    dp.register_message_handler(process_new_fio, state=EditProfile.waiting_new_fio)
    dp.register_callback_query_handler(process_new_timezone, state=EditProfile.waiting_new_timezone)
    dp.register_callback_query_handler(process_new_age_group, state=EditProfile.waiting_new_age_group)

    # Обработчики состояний
    dp.register_message_handler(process_new_fio, state=EditProfile.waiting_new_fio)
