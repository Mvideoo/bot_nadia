import aiosqlite
from .models.user import User
import logging
from data_base.courses_data import COURSES


logger = logging.getLogger(__name__)

async def init_db():
    logger.info("Initializing database")
    await User.create_table()


    async with aiosqlite.connect('finance_bot.db') as db:
        cursor = await db.execute("SELECT COUNT(*) FROM shop_items")
        count = (await cursor.fetchone())[0]

        if count == 0:
            # Примеры мерча
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Футболка Financial Guru", "Стильная хлопковая футболка с логотипом", 150, "Мерч")
            )
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Крутка с формулами", "Керамическая крутка с финансовыми формулами", 200, "Мерч")
            )
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Блокнот инвестора", "Премиальный блокнот для финансовых заметок", 100, "Мерч")
            )

            # Примеры помощи экспертов
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Консультация по инвестициям", "30-минутная консультация с экспертом", 500, "Помощь экспертов")
            )
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Разбор портфеля", "Анализ вашего инвестиционного портфеля", 700, "Помощь экспертов")
            )
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                ("Персональный финансовый план", "Разработка индивидуального плана", 1000, "Помощь экспертов")
            )

            await db.commit()
            logger.info("Example shop items added")

async def get_user_role(user_id: int) -> str:
    return await User.get_role(user_id)

async def update_user_data(user_id: int, full_name: str = None, timezone: str = None):
    await User.update_user(user_id, full_name, timezone)

async def get_user_data(user_id: int):
    return await User.get_user(user_id)

async def add_coins(user_id: int, amount: int):
    await User.add_coins(user_id, amount)

async def get_coins(user_id: int):
    return await User.get_coins(user_id)

async def mark_lesson_read(user_id: int, course_id: int, lesson_id: int):
    await User.mark_lesson_read(user_id, course_id, lesson_id)

async def mark_quiz_passed(user_id: int, course_id: int, lesson_id: int, coins_earned: int):
    await User.mark_quiz_passed(user_id, course_id, lesson_id, coins_earned)

async def get_lesson_progress(user_id: int, course_id: int, lesson_id: int):
    return await User.get_lesson_progress(user_id, course_id, lesson_id)

async def is_course_completed(user_id: int, course_id: int):
    return await User.is_course_completed(user_id, course_id)


async def get_next_lesson(user_id: int, course_id: int, current_lesson_id: int):
    async with aiosqlite.connect('finance_bot.db') as db:
        # Получаем все уроки курса
        cursor = await db.execute("SELECT lesson_id FROM user_progress WHERE user_id = ? AND course_id = ?",
                                  (user_id, course_id))
        completed_lessons = [row[0] for row in await cursor.fetchall()]

        # Получаем список всех уроков в курсе
        all_lessons = sorted(COURSES[course_id]['lessons'].keys())

        # Находим следующий урок
        for lesson_id in all_lessons:
            if lesson_id > current_lesson_id and lesson_id not in completed_lessons:
                return lesson_id

        # Если не нашли следующий, возвращаем первый непройденный
        for lesson_id in all_lessons:
            if lesson_id not in completed_lessons:
                return lesson_id

        return None  # Все уроки пройдены