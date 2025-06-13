import asyncio
import datetime
from create_bot import bot
from data_base import db
import logging
import pytz

from data_base.models.user import User
logger = logging.getLogger(__name__)


async def send_quests():
    logger.info("Starting quests delivery...")

    # Текущее время по МСК
    msk_tz = pytz.timezone('Europe/Moscow')
    now = datetime.datetime.now(msk_tz)
    current_time = now.strftime("%H:%M")

    # Получаем активные квесты для текущего времени
    active_quests = await User.get_active_quests()
    quests_to_send = [q for q in active_quests if q[3] == current_time]

    if not quests_to_send:
        logger.info(f"No quests scheduled for {current_time} MSK")
        return

    # Получаем всех учеников
    students = await User.get_all_students()

    for student in students:
        user_id = student[0]
        age_group = student[3]  # возрастная группа
        timezone = await User.get_user_timezone(user_id)

        try:
            # Рассчитываем смещение
            offset = int(timezone.replace('UTC', '').strip())
            user_time = (now + datetime.timedelta(hours=offset - 3)).strftime("%H:%M")

            # Отправляем каждый квест
            for quest in quests_to_send:
                _, title, description, _, _ = quest

                # Форматируем сообщение
                message = (
                    f"🎯 <b>Ежедневный квест!</b>\n\n"
                    f"<b>{title}</b>\n"
                    f"{description}\n\n"
                    f"⏰ Ваше локальное время: {user_time}"
                )

                await bot.send_message(user_id, message, parse_mode="HTML")
                logger.info(f"Quest '{title}' sent to user {user_id} at {user_time}")

        except Exception as e:
            logger.error(f"Error sending quest to user {user_id}: {str(e)}")


async def schedule_quests():
    while True:
        await send_quests()
        # Проверяем каждую минуту
        await asyncio.sleep(60)