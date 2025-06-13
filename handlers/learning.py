import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from PIL import Image, ImageDraw, ImageFont
from create_bot import dp, bot
from data_base import db
from data_base.courses_data import COURSES
from data_base.models.user import User
from keyboards.common import (
    course_selection_keyboard,
    lesson_selection_keyboard,
    mark_as_read_keyboard,
    start_quiz_keyboard,
    quiz_options_keyboard,
    after_quiz_keyboard
)

import io
import logging
import textwrap

logger = logging.getLogger(__name__)


# Состояния для прохождения теста
class QuizState(StatesGroup):
    waiting_for_answer = State()
    quiz_data = State()  # Состояние для хранения данных викторины


# Состояния для FSM викторины
class QuizFSM(StatesGroup):
    in_progress = State()


@dp.message_handler(lambda message: message.text == '📚 Обучение', active_role=None)
async def show_courses(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} accessed learning section")

    # Получаем возрастную группу пользователя
    age_group = await User.get_user_age_group(user_id)
    if not age_group:
        await message.answer("❌ Ваша возрастная группа не определена. Пожалуйста, обновите профиль.")
        return

    # Фильтруем курсы по возрастной группе
    available_courses = {}
    for course_id, course in COURSES.items():
        if course['age_group'] == 'all' or course['age_group'] == age_group:
            available_courses[course_id] = course

    if not available_courses:
        await message.answer("😢 Для вашей возрастной группы пока нет доступных курсов")
        return

    await message.answer("Выберите курс для изучения:",
                         reply_markup=course_selection_keyboard(available_courses))


@dp.callback_query_handler(lambda c: c.data.startswith('course_'), active_role='student')
async def select_course(callback: types.CallbackQuery):
    course_id = int(callback.data.split('_')[1])
    course = COURSES.get(course_id)

    if not course:
        await callback.answer("Курс не найден!")
        return

    # Проверяем прогресс пользователя
    user_id = callback.from_user.id
    lessons_progress = {}
    for lesson_id in course['lessons']:
        progress = await db.get_lesson_progress(user_id, course_id, lesson_id)
        if progress:
            lessons_progress[lesson_id] = {
                'read': bool(progress[3]),
                'quiz_passed': bool(progress[4])
            }

    await callback.message.answer(
        f"<b>{course['title']}</b>\n\n"
        f"{course['description']}\n\n"
        "Выберите урок:",
        parse_mode="HTML",
        reply_markup=lesson_selection_keyboard(course_id, course['lessons'], lessons_progress)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('lesson_'), active_role='student')
async def show_lesson(callback: types.CallbackQuery):
    data = callback.data.split('_')
    course_id = int(data[1])
    lesson_id = int(data[2])
    course = COURSES.get(course_id)

    if not course:
        await callback.answer("Курс не найден!")
        return

    lesson = course['lessons'].get(lesson_id)
    if not lesson:
        await callback.answer("Урок не найден!")
        return

    # Отправляем содержание урока
    content = f"<b>Урок {lesson_id}: {lesson['title']}</b>\n\n{lesson['content']}"
    await callback.message.answer(content, parse_mode="HTML")

    # Проверяем, прочитан ли уже урок
    progress = await db.get_lesson_progress(callback.from_user.id, course_id, lesson_id)
    if progress and progress[3]:  # read
        # Если урок уже прочитан, сразу предлагаем тест
        await callback.message.answer(
            "Вы уже прочитали этот урок. Хотите пройти тест?",
            reply_markup=start_quiz_keyboard(course_id, lesson_id)
        )
    else:
        # Иначе предлагаем отметить как прочитанный
        await callback.message.answer(
            "Прочитайте материал и нажмите кнопку, когда будете готовы:",
            reply_markup=mark_as_read_keyboard(course_id, lesson_id)
        )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('read_'), active_role='student')
async def mark_lesson_read(callback: types.CallbackQuery):
    data = callback.data.split('_')
    course_id = int(data[1])
    lesson_id = int(data[2])
    user_id = callback.from_user.id

    # Помечаем урок как прочитанный
    await db.mark_lesson_read(user_id, course_id, lesson_id)

    # Обновляем сообщение
    await callback.message.edit_text("✅ Урок отмечен как прочитанный")

    # Предлагаем пройти тест
    await callback.message.answer(
        "Теперь вы можете пройти тест по уроку:",
        reply_markup=start_quiz_keyboard(course_id, lesson_id)
    )
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('quiz_'), active_role='student')
async def start_quiz(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    course_id = int(data[1])
    lesson_id = int(data[2])
    user_id = callback.from_user.id

    # Получаем данные урока
    course = COURSES.get(course_id)
    if not course:
        await callback.answer("Курс не найден!")
        return

    lesson = course['lessons'].get(lesson_id)
    if not lesson:
        await callback.answer("Урок не найден!")
        return

    quiz = lesson.get('quiz', {})

    # Инициализируем прогресс теста в FSM
    quiz_data = {
        'course_id': course_id,
        'lesson_id': lesson_id,
        'current_question': 0,
        'correct_answers': 0,
        'questions': quiz.get('questions', [])
    }

    # Сохраняем данные в FSM
    await state.update_data(quiz_data=quiz_data)
    await QuizFSM.in_progress.set()

    # Проверяем наличие вопросов
    if not quiz_data['questions']:
        await callback.answer("Для этого урока тест еще не готов!")
        await state.finish()
        return

    # Задаем первый вопрос
    await ask_question(callback.message, state)
    await callback.answer()


async def ask_question(message: types.Message, state: FSMContext):
    # Получаем данные из FSM
    data = await state.get_data()
    quiz_data = data.get('quiz_data', {})

    if not quiz_data or quiz_data['current_question'] >= len(quiz_data['questions']):
        return

    question_index = quiz_data['current_question']
    question = quiz_data['questions'][question_index]

    # Формируем текст вопроса
    question_text = f"❓ Вопрос {question_index + 1}/{len(quiz_data['questions'])}:\n{question['question']}"

    # Отправляем вопрос с вариантами ответов
    await message.answer(
        question_text,
        reply_markup=quiz_options_keyboard(question['options'])
    )


@dp.callback_query_handler(lambda c: c.data.startswith('answer_'), state=QuizFSM.in_progress,
                           active_role='student')
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
    # Получаем данные из FSM
    data = await state.get_data()
    quiz_data = data.get('quiz_data', {})

    if not quiz_data:
        await callback.answer("Ошибка: прогресс теста не найден")
        await state.finish()
        return

    # Получаем данные ответа
    answer_index = int(callback.data.split('_')[1])
    question_index = quiz_data['current_question']

    if question_index >= len(quiz_data['questions']):
        await callback.answer("Ошибка: вопрос не найден")
        return

    question = quiz_data['questions'][question_index]

    # Проверяем ответ
    is_correct = (answer_index == question['correct'])

    if is_correct:
        quiz_data['correct_answers'] += 1
        feedback = "✅ Правильно!"
    else:
        feedback = f"❌ Неверно."

    await callback.message.answer(feedback)

    # Обновляем текущий вопрос
    quiz_data['current_question'] += 1
    await state.update_data(quiz_data=quiz_data)

    # Если вопросы закончились
    if quiz_data['current_question'] >= len(quiz_data['questions']):
        # Завершаем тест
        await finish_quiz(callback.message, quiz_data, callback.from_user.id)
        await state.finish()
    else:
        # Задаем следующий вопрос
        await ask_question(callback.message, state)

    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('next_lesson_'), active_role='student')
async def go_to_next_lesson(callback: types.CallbackQuery):
    data = callback.data.split('_')
    course_id = int(data[2])
    lesson_id = int(data[3])

    # Создаем искусственный callback для эмуляции нажатия на урок
    class FakeCallback:
        def __init__(self, data, message):
            self.data = data
            self.message = message
            self.from_user = message.from_user

    fake_cb = FakeCallback(f"lesson_{course_id}_{lesson_id}", callback.message)

    # Вызываем обработчик урока
    await show_lesson(fake_cb)
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data.startswith('retry_quiz_'), active_role='student')
async def retry_quiz(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split('_')
    course_id = int(data[2])
    lesson_id = int(data[3])

    # Создаем искусственный callback для эмуляции нажатия на тест
    class FakeCallback:
        def __init__(self, data, message):
            self.data = data
            self.message = message
            self.from_user = message.from_user

    fake_cb = FakeCallback(f"quiz_{course_id}_{lesson_id}", callback.message)

    # Вызываем обработчик теста
    await start_quiz(fake_cb, state)
    await callback.answer()


async def generate_and_send_certificate(message: types.Message, user_id: int, course_title: str):
    # Получаем данные пользователя
    user_data = await User.get_user(user_id)
    full_name = user_data[2] if user_data else "Пользователь"

    try:
        # Размеры изображения
        width, height = 1000, 700

        # Создаем изображение сертификата
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        d = ImageDraw.Draw(img)

        try:
            # Пытаемся использовать шрифт, поддерживающий кириллицу
            try:
                # Для Windows
                font_title = ImageFont.truetype("arialbd.ttf", 40)
                font_name = ImageFont.truetype("arialbd.ttf", 36)
                font_course = ImageFont.truetype("arial.ttf", 30)
            except:
                # Для Linux/Mac
                font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
                font_name = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
                font_course = ImageFont.truetype("DejaVuSans.ttf", 30)
        except:
            # Используем стандартный шрифт, если не найден
            font_title = ImageFont.load_default()
            font_name = ImageFont.load_default()
            font_course = ImageFont.load_default()
            logger.warning("Using default font for certificate generation")

        # Рисуем заголовок
        title = "СЕРТИФИКАТ"
        d.text((width // 2, 150), title, fill=(0, 0, 0), font=font_title, anchor="mm")

        # Рисуем основной текст
        text = "Настоящим удостоверяется, что"
        d.text((width // 2, 230), text, fill=(0, 0, 0), font=font_course, anchor="mm")

        # Имя студента
        d.text((width // 2, 300), full_name, fill=(0, 0, 0), font=font_name, anchor="mm")

        text = "успешно прошел(а) курс"
        d.text((width // 2, 360), text, fill=(0, 0, 0), font=font_course, anchor="mm")

        # Название курса
        course_text = f"«{course_title}»"
        d.text((width // 2, 420), course_text, fill=(0, 0, 0), font=font_course, anchor="mm")

        # Создаем буфер в памяти для изображения
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)  # Перемещаем указатель в начало буфера

        # Отправляем сертификат пользователю прямо из памяти
        await message.answer_photo(
            img_byte_arr,
            caption=f"🎓 Поздравляем с завершением курса «{course_title}»!\nВаш сертификат доступен для скачивания."
        )

    except Exception as e:
        logger.error(f"Ошибка генерации сертификата: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        await message.answer(
            f"🎓 Поздравляем с завершением курса «{course_title}»!\n"
            "К сожалению, сертификат временно недоступен."
        )

async def finish_quiz(message: types.Message, quiz_data: dict, user_id: int):
    total_questions = len(quiz_data['questions'])
    correct_answers = quiz_data['correct_answers']
    percent_correct = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    course = COURSES.get(quiz_data['course_id'], {})
    lesson = course.get('lessons', {}).get(quiz_data['lesson_id'], {})
    quiz = lesson.get('quiz', {})
    required_percent = quiz.get('pass_percent', 75)

    result_text = (
        f"📊 Результаты теста:\n"
        f"Правильных ответов: {correct_answers}/{total_questions}\n"
        f"Процент правильных: {percent_correct:.1f}%"
    )

    await message.answer(result_text)

    # Проверяем, пройден ли тест
    if percent_correct >= required_percent:
        # Проверяем, был ли тест уже пройден ранее
        current_progress = await db.get_lesson_progress(user_id, quiz_data['course_id'], quiz_data['lesson_id'])
        already_passed = current_progress and current_progress[4]  # quiz_passed

        coins_earned = 0
        if not already_passed:
            coins_earned = 50
            await db.add_coins(user_id, coins_earned)
            await db.mark_quiz_passed(
                user_id,
                quiz_data['course_id'],
                quiz_data['lesson_id'],
                coins_earned
            )
            success_text = f"🎉 Поздравляем! Вы успешно прошли тест!\nПолучено: {coins_earned} монет"
        else:
            success_text = "🎉 Вы успешно прошли тест повторно! Монеты начисляются только за первый проход."

        await message.answer(success_text)

        # Проверяем, является ли это последним уроком в курсе
        course_lessons = list(course.get('lessons', {}).keys())
        is_last_lesson = False
        if course_lessons:
            last_lesson_id = max(course_lessons)
            is_last_lesson = (quiz_data['lesson_id'] == last_lesson_id)

        course_completed = await db.is_course_completed(user_id, quiz_data['course_id'])

        if course_completed:
            # Генерируем и отправляем сертификат
            await generate_and_send_certificate(message, user_id, course.get('title', 'Неизвестный курс'))
        else:
            # Находим следующий урок
            next_lesson_id = quiz_data['lesson_id'] + 1
            if next_lesson_id in course['lessons']:
                await message.answer(
                    "Перейти к следующему уроку?",
                    reply_markup=after_quiz_keyboard(
                        quiz_data['course_id'],
                        next_lesson_id,
                        show_next=True
                    )
                )
            else:
                # Это не должно случиться, но на всякий случай
                await message.answer("Вы прошли все уроки этого курса! Возвращайтесь в главное меню.")
    else:
        fail_text = (
            f"😞 К сожалению, вы не прошли тест.\n"
            f"Требуется минимум {required_percent}% правильных ответов."
        )
        await message.answer(fail_text)

        # Предлагаем попробовать еще раз или перейти к следующему уроку
        await message.answer(
            "Что вы хотите сделать?",
            reply_markup=after_quiz_keyboard(
                quiz_data['course_id'],
                quiz_data['lesson_id'],
                show_next=False
            )
        )


def register_handlers_learning(dp):
    # Все обработчики уже зарегистрированы через декораторы
    pass
