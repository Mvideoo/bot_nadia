import asyncio
import logging
from create_bot import dp, bot, on_startup
from handlers import common, admin, student, learning
from utils.storage import admin_modes
from utils.scheduler import schedule_quests  # Импорт планировщика

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Очищаем состояния администраторов при запуске
    admin_modes.clear()
    logger.info("Admin modes cleared")

    # Инициализация бота
    await on_startup(dp)

    # Регистрация обработчиков
    common.register_handlers_common(dp)
    admin.register_handlers_admin(dp)
    student.register_handlers_student(dp)
    learning.register_handlers_learning(dp)

    # Запуск планировщика квестов в фоне
    asyncio.create_task(schedule_quests())

    logger.info("Starting bot")
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())