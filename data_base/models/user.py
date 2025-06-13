import aiosqlite
from data_base.courses_data import COURSES
import logging
import datetime

logger = logging.getLogger(__name__)


class User:
    @staticmethod
    async def create_table():
        async with aiosqlite.connect('finance_bot.db') as db:
            # Таблица пользователей
            await db.execute('''CREATE TABLE IF NOT EXISTS users
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY,
                                    username
                                    TEXT,
                                    full_name
                                    TEXT,
                                    role
                                    TEXT
                                    NOT
                                    NULL,
                                    timezone
                                    TEXT
                                    DEFAULT
                                    'UTC+3',
                                    coins
                                    INTEGER
                                    DEFAULT
                                    0,
                                    age_group
                                    TEXT -- '14-17' или '18-25'
                                )''')

            # Таблица прогресса
            await db.execute('''CREATE TABLE IF NOT EXISTS user_progress
            (
                user_id
                INTEGER,
                course_id
                INTEGER,
                lesson_id
                INTEGER,
                read
                BOOLEAN
                DEFAULT
                0,
                quiz_passed
                BOOLEAN
                DEFAULT
                0,
                coins_earned
                INTEGER
                DEFAULT
                0,
                PRIMARY
                KEY
                                (
                user_id,
                course_id,
                lesson_id
                                ),
                FOREIGN KEY
                                (
                                    user_id
                                ) REFERENCES users
                                (
                                    id
                                )
                )''')
            # Таблица квестов
            await db.execute('''CREATE TABLE IF NOT EXISTS quests
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    title
                                    TEXT
                                    NOT
                                    NULL,
                                    description
                                    TEXT
                                    NOT
                                    NULL,
                                    time_utc3
                                    TEXT
                                    NOT
                                    NULL, -- Время отправки по МСК (HH:MM)
                                    active
                                    BOOLEAN
                                    DEFAULT
                                    1
                                )''')

            # Таблица прогресса квестов
            await db.execute('''CREATE TABLE IF NOT EXISTS user_quests
            (
                user_id
                INTEGER,
                quest_id
                INTEGER,
                date
                TEXT
                NOT
                NULL,
                completed
                BOOLEAN
                DEFAULT
                0,
                completion_date
                TEXT,
                PRIMARY
                KEY
                                (
                user_id,
                quest_id,
                date
                                ),
                FOREIGN KEY
                                (
                                    user_id
                                ) REFERENCES users
                                (
                                    id
                                ),
                FOREIGN KEY
                                (
                                    quest_id
                                ) REFERENCES quests
                                (
                                    id
                                ))''')

            await db.execute('''CREATE TABLE IF NOT EXISTS shop_items
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    name
                                    TEXT
                                    NOT
                                    NULL,
                                    description
                                    TEXT
                                    NOT
                                    NULL,
                                    price
                                    INTEGER
                                    NOT
                                    NULL,
                                    category
                                    TEXT
                                    NOT
                                    NULL
                                )''')

            # Таблица покупок
            await db.execute('''CREATE TABLE IF NOT EXISTS purchases
            (
                user_id
                INTEGER,
                item_id
                INTEGER,
                purchase_date
                TEXT
                NOT
                NULL,
                PRIMARY
                KEY
                                (
                user_id,
                item_id
                                ),
                FOREIGN KEY
                                (
                                    user_id
                                ) REFERENCES users
                                (
                                    id
                                ),
                FOREIGN KEY
                                (
                                    item_id
                                ) REFERENCES shop_items
                                (
                                    id
                                ))''')

            await db.execute('''CREATE TABLE IF NOT EXISTS support_tickets
            (
                id
                INTEGER
                PRIMARY
                KEY
                AUTOINCREMENT,
                user_id
                INTEGER
                NOT
                NULL,
                username
                TEXT,
                full_name
                TEXT,
                role
                TEXT,
                message
                TEXT
                NOT
                NULL,
                created_at
                TIMESTAMP
                DEFAULT
                CURRENT_TIMESTAMP,
                status
                TEXT
                DEFAULT
                'open',
                admin_id
                INTEGER,
                admin_response
                TEXT,
                response_at
                TIMESTAMP,
                FOREIGN
                KEY
                                (
                user_id
                                ) REFERENCES users
                                (
                                    id
                                ))''')
            await db.commit()
            logger.info("Support tickets table created")
            logger.info("Shop tables created")
            logger.info("Quest tables created")
            logger.info("Tables created")

    @staticmethod
    async def create_support_ticket(user_id: int, username: str, full_name: str, role: str, message: str):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Экранируем кавычки в сообщении
            safe_message = message.replace('"', '""').replace("'", "''")

            await db.execute(
                "INSERT INTO support_tickets (user_id, username, full_name, role, message) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, full_name, role, safe_message)
            )
            await db.commit()
            logger.info(f"Support ticket created by {user_id}")

    @staticmethod
    async def get_open_tickets():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM support_tickets WHERE status = 'open'")
            return await cursor.fetchall()

    @staticmethod
    async def get_ticket(ticket_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,))
            return await cursor.fetchone()

    @staticmethod
    async def answer_ticket(ticket_id: int, admin_id: int, response: str):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Экранируем кавычки в ответе
            safe_response = response.replace('"', '""').replace("'", "''")

            await db.execute(
                "UPDATE support_tickets SET status = 'answered', admin_id = ?, admin_response = ?, response_at = CURRENT_TIMESTAMP WHERE id = ?",
                (admin_id, safe_response, ticket_id)
            )
            await db.commit()
            logger.info(f"Ticket {ticket_id} answered by admin {admin_id}")

    @staticmethod
    async def get_user_tickets(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC",
                                      (user_id,))
            return await cursor.fetchall()

    @staticmethod
    async def add_shop_item(name: str, description: str, price: int, category: str):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                "INSERT INTO shop_items (name, description, price, category) VALUES (?, ?, ?, ?)",
                (name, description, price, category)
            )
            await db.commit()
            logger.info(f"Shop item added: {name}")

    @staticmethod
    async def get_shop_items(category: str = None):
        async with aiosqlite.connect('finance_bot.db') as db:
            if category:
                cursor = await db.execute("SELECT * FROM shop_items WHERE category = ?", (category,))
            else:
                cursor = await db.execute("SELECT * FROM shop_items")
            return await cursor.fetchall()

    @staticmethod
    async def get_shop_item(item_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM shop_items WHERE id = ?", (item_id,))
            return await cursor.fetchone()

    @staticmethod
    async def purchase_item(user_id: int, item_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Получаем информацию о товаре
            item = await db.get_shop_item(item_id)
            if not item:
                return False, "Товар не найден"

            # Проверяем баланс пользователя
            user_coins = await db.get_coins(user_id)
            if user_coins < item[3]:  # price
                return False, "Недостаточно монет"

            # Проверяем, не покупал ли уже этот товар
            cursor = await db.execute("SELECT 1 FROM purchases WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            if await cursor.fetchone():
                return False, "Вы уже купили этот товар"

            # Совершаем покупку
            purchase_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "INSERT INTO purchases (user_id, item_id, purchase_date) VALUES (?, ?, ?)",
                (user_id, item_id, purchase_date)
            )

            # Списание средств
            await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (item[3], user_id))

            await db.commit()
            logger.info(f"User {user_id} purchased item {item_id}")
            return True, f"✅ Успешная покупка! Вы приобрели: {item[1]}"

    @staticmethod
    async def get_user_purchases(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute('''SELECT s.id, s.name, s.description, p.purchase_date
                                         FROM purchases p
                                                  JOIN shop_items s ON p.item_id = s.id
                                         WHERE p.user_id = ?''', (user_id,))
            return await cursor.fetchall()

    @staticmethod
    async def add_user(user_id: int, username: str, full_name: str, role: str, age_group: str):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (id, username, full_name, role, age_group) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, full_name, role, age_group)
            )
            await db.commit()
            logger.info(f"User added: {user_id}, {username}, {full_name}, {role}, {age_group}")

    @staticmethod
    async def get_all_students():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT id, username, full_name, age_group FROM users WHERE role != 'admin'")
            return await cursor.fetchall()

    @staticmethod
    async def add_broadcast(message: str, scheduled_time: str):
        # В этой реализации не храним рассылки в БД, но можно добавить при необходимости
        logger.info(f"Broadcast scheduled at {scheduled_time} MSK: {message}")

    @staticmethod
    async def get_top_students(limit: int = 5):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Получаем топ учеников (кроме админов) по количеству монет
            cursor = await db.execute(
                "SELECT id, username, full_name, coins FROM users "
                "WHERE coins > 0 "
                "ORDER BY coins DESC LIMIT ?",
                (limit,)
            )
            return await cursor.fetchall()

    @staticmethod
    async def get_user_position(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Получаем позицию пользователя в общем рейтинге
            cursor = await db.execute('''
                                      SELECT position
                                      FROM (SELECT id, ROW_NUMBER() OVER (ORDER BY coins DESC) AS position
                                            FROM users
                                            WHERE role != 'admin' AND coins > 0)
                                      WHERE id = ?
                                      ''', (user_id,))

            result = await cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    async def get_all_users():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT id FROM users")
            return await cursor.fetchall()

    @staticmethod
    async def get_closed_tickets():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM support_tickets WHERE status IN ('answered', 'closed')")
            return await cursor.fetchall()

    @staticmethod
    async def update_user(user_id: int, full_name: str = None, timezone: str = None, age_group: str = None):
        async with aiosqlite.connect('finance_bot.db') as db:
            try:
                # Собираем параметры для обновления
                updates = []
                params = []

                if full_name:
                    updates.append("full_name = ?")
                    params.append(full_name)
                if timezone:
                    updates.append("timezone = ?")
                    params.append(timezone)
                if age_group:
                    updates.append("age_group = ?")
                    params.append(age_group)

                if not updates:
                    logger.warning("No fields to update")
                    return False

                # Формируем SQL-запрос
                sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                params.append(user_id)

                await db.execute(sql, tuple(params))
                await db.commit()

                logger.info(f"User updated: ID={user_id}, updates={updates}")
                return True
            except Exception as e:
                logger.error(f"Error updating user: {str(e)}")
                return False

    @staticmethod
    async def get_user_age_group(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT age_group FROM users WHERE id = ?", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    @staticmethod
    async def get_user(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return await cursor.fetchone()

    @staticmethod
    async def get_role(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            role = await cursor.fetchone()
            return role[0] if role else None

    @staticmethod
    async def add_coins(user_id: int, amount: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, user_id))
            await db.commit()
            logger.info(f"Coins added to user {user_id}: +{amount}")

    @staticmethod
    async def get_coins(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else 0

    @staticmethod
    async def mark_lesson_read(user_id: int, course_id: int, lesson_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                '''INSERT OR REPLACE INTO user_progress (user_id, course_id, lesson_id, read)
                VALUES (?, ?, ?, ?)''',
                (user_id, course_id, lesson_id, 1)
            )
            await db.commit()
            logger.info(f"Lesson marked as read: user={user_id}, course={course_id}, lesson={lesson_id}")

    @staticmethod
    async def mark_quiz_passed(user_id: int, course_id: int, lesson_id: int, coins_earned: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                '''INSERT OR REPLACE INTO user_progress 
                (user_id, course_id, lesson_id, read, quiz_passed, coins_earned)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, course_id, lesson_id, 1, 1, coins_earned)
            )
            await db.commit()
            logger.info(f"Quiz passed: user={user_id}, course={course_id}, lesson={lesson_id}, coins={coins_earned}")

    @staticmethod
    async def get_lesson_progress(user_id: int, course_id: int, lesson_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute(
                "SELECT * FROM user_progress WHERE user_id = ? AND course_id = ? AND lesson_id = ?",
                (user_id, course_id, lesson_id)
            )
            return await cursor.fetchone()

    @staticmethod
    async def is_course_completed(user_id: int, course_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            # Получаем общее количество уроков в курсе
            if course_id not in COURSES:
                return False

            total_lessons = len(COURSES[course_id]['lessons'])

            # Получаем количество пройденных уроков
            cursor = await db.execute(
                "SELECT COUNT(DISTINCT lesson_id) FROM user_progress WHERE user_id = ? AND course_id = ? AND read = 1",
                (user_id, course_id)
            )
            completed_lessons = (await cursor.fetchone())[0]

            return completed_lessons >= total_lessons

    @staticmethod
    async def user_exists(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return await cursor.fetchone() is not None

    @staticmethod
    async def add_quest(title: str, description: str, time_utc3: str):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                "INSERT INTO quests (title, description, time_utc3) VALUES (?, ?, ?)",
                (title, description, time_utc3)
            )
            await db.commit()
            logger.info(f"Quest added: {title} at {time_utc3}")

    @staticmethod
    async def toggle_quest(quest_id: int, active: bool):
        async with aiosqlite.connect('finance_bot.db') as db:
            await db.execute(
                "UPDATE quests SET active = ? WHERE id = ?",
                (1 if active else 0, quest_id)
            )
            await db.commit()
            logger.info(f"Quest {quest_id} toggled to {active}")

    @staticmethod
    async def get_all_quests():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM quests")
            return await cursor.fetchall()

    @staticmethod
    async def get_active_quests():
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT * FROM quests WHERE active = 1")
            return await cursor.fetchall()

    @staticmethod
    async def get_today_quests_for_user(user_id: int):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute('''SELECT q.id, q.title, q.description, uq.completed
                                         FROM quests q
                                                  LEFT JOIN user_quests uq
                                                            ON q.id = uq.quest_id
                                                                AND uq.user_id = ?
                                                                AND uq.date = ?
                                         WHERE q.active = 1''',
                                      (user_id, today))
            return await cursor.fetchall()

    @staticmethod
    async def mark_quest_completed(user_id: int, quest_id: int):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect('finance_bot.db') as db:
            # Проверяем, не выполнен ли уже квест сегодня
            cursor = await db.execute('''SELECT 1
                                         FROM user_quests
                                         WHERE user_id = ?
                                           AND quest_id = ?
                                           AND date = ?''',
                                      (user_id, quest_id, today))
            exists = await cursor.fetchone()

            if exists:
                await db.execute('''UPDATE user_quests
                                    SET completed       = 1,
                                        completion_date = ?
                                    WHERE user_id = ?
                                      AND quest_id = ?
                                      AND date = ?''',
                                 (now, user_id, quest_id, today))
            else:
                await db.execute('''INSERT INTO user_quests
                                        (user_id, quest_id, date, completed, completion_date)
                                    VALUES (?, ?, ?, ?, ?)''',
                                 (user_id, quest_id, today, 1, now))

            # Начисляем монеты за выполнение
            await db.execute("UPDATE users SET coins = coins + 10 WHERE id = ?", (user_id,))

            await db.commit()
            logger.info(f"User {user_id} completed quest {quest_id}")

    @staticmethod
    async def get_user_timezone(user_id: int):
        async with aiosqlite.connect('finance_bot.db') as db:
            cursor = await db.execute("SELECT timezone FROM users WHERE id = ?", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else "UTC+3"
