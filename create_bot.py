from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import BoundFilter
from data_base import db
from utils.storage import admin_modes
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7736918579:AAERfjJpxbgwu8yfRj3G0BbvxRJkDqghujk'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class RoleFilter(BoundFilter):
    key = 'active_role'

    def __init__(self, active_role):
        self.role = active_role

    async def check(self, message):
        user_id = message.from_user.id
        user_role = await db.get_user_role(user_id)

        logger.info(f"Role check: user_id={user_id}, role={user_role}, required={self.role}")

        return True


class ActiveRoleFilter(BoundFilter):
    key = 'active_role'

    def __init__(self, role):
        self.role = role

    async def check(self, message):
        user_id = message.from_user.id
        user_role = await db.get_user_role(user_id)

        logger.info(f"Active role check: user_id={user_id}, role={user_role}, required={self.role}")

        if user_role == 'admin' and user_id in admin_modes:
            return admin_modes[user_id] == self.role

        return True


dp.filters_factory.bind(RoleFilter)
dp.filters_factory.bind(ActiveRoleFilter)


async def on_startup(_):
    await db.init_db()
    logger.info("Database initialized")
