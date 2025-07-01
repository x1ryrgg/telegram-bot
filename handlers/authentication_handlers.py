from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, URLInputFile
from aiogram.utils import markdown
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from api import get_profile, check_user_role, get_groups_list, post_event, get_events
from config import auth_required, format_profile, format_event
from handlers.login_handlers import dp_router
from keyboards import main_keyboard, get_location_keyboard, type_keyboard, get_date_keyboard
from datetime import datetime


auth_router = Router()

class EventState(StatesGroup):
    title = State() # просто string
    location = State() # просто string
    type = State() # будет inline_keyboard с выбором типа
    group = State()  # будут выводиться все группы с id - name и нужно будет ввесть id
    event_date = State() # дата будет по типу 2025-06-19 12:30
    # photos = State()
    # videos = State()


@auth_router.message(F.text == 'Профиль')
@auth_required
async def check_profile(message: Message, access_token: str):
    profile = await get_profile(access_token)

    response = format_profile(profile)

    response = "\n".join(response)
    await message.answer(response, parse_mode="HTML", reply_markup=main_keyboard())


@auth_router.message(F.text == 'Просмотреть мероприятия')
@auth_required
async def check_profile(message: Message, access_token: str):
    events = await get_events(access_token)

    if not events:
        await message.answer("📭 Мероприятий пока что нет. ", reply_markup=main_keyboard())
        return

    for event in events:
        event_data = format_event(event)

        if event_data['photo_url']:
            # Если есть фото, отправляем его с подписью
            photo = URLInputFile(event_data['photo_url'])
            await message.answer_photo(
                photo=photo,
                caption=event_data['caption'],
                parse_mode="HTML",
                reply_markup=main_keyboard()
            )
        else:
            await message.answer(
                event_data['caption'],
                parse_mode="HTML",
                reply_markup=main_keyboard()
            )

    for part in [event_data[i:i + 4000] for i in range(0, len(event_data), 4000)]:
        await message.answer(part, parse_mode=ParseMode.HTML, reply_markup=main_keyboard())

@auth_router.message(F.text == 'Создать мероприятие')
@auth_required
async def start_create_event(message: Message, access_token: str, state: FSMContext):
    user = await check_user_role(access_token, message.from_user.id)

    if user.get('role') != 'teacher':
        await message.answer('❌ Только преподаватель может создавать мероприятие.')
        return

    await message.answer("Создание мероприятия. Введите название:")
    await state.set_state(EventState.title)


@auth_router.message(EventState.title)
@auth_required
async def process_title(message: Message, access_token: str, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        "Введите место проведения мероприятия или выберите в списке:",
        reply_markup=get_location_keyboard()
    )
    await state.set_state(EventState.location)


@auth_router.callback_query(lambda c: c.data.startswith('location_'), EventState.location)
@auth_required
async def process_location_callback(callback: CallbackQuery, access_token: str, state: FSMContext):
    address_map = {
        "location_20_oktyabrya": "ул. 20-летия Октября, 84",
        "location_plehanovskaya": "ул. Плехановская, 11",
        "location_moskovskiy": "Московский проспект, 179"
    }

    selected_address = address_map[callback.data]
    await state.update_data(location=selected_address)
    await callback.message.answer(f"Выбрано место: {selected_address}")
    await callback.answer()

    # Переход к выбору типа мероприятия
    await callback.message.answer("Выберите тип мероприятия:", reply_markup=type_keyboard())
    await state.set_state(EventState.type)


@auth_router.message(EventState.location)
@auth_required
async def process_location(message: Message, access_token: str, state: FSMContext):
    if message.text.startswith('/'):
        return

    await state.update_data(location=message.text)
    await message.answer(f"Место проведения: {message.text}")

    # Переход к выбору типа мероприятия
    await message.answer("Выберите тип мероприятия:", reply_markup=type_keyboard())
    await state.set_state(EventState.type)


@auth_router.callback_query(lambda c: c.data.startswith('type_'), EventState.type)
@auth_required
async def process_type_callback(callback: CallbackQuery, access_token: str, state: FSMContext):
    types_map = {
        "type_conference": "конференция",
        "type_contest": "конкурс",
        "type_excursion": "экскурсия",
        "type_seminar": "семинар"
    }

    selected_type = types_map[callback.data]
    await state.update_data(type=selected_type)
    await callback.message.answer(f"Выбран тип мероприятия: {selected_type}")
    await callback.answer()

    # Запрашиваем список групп
    groups = await get_groups_list(access_token)
    if not groups:
        await callback.message.answer("❌ Не удалось загрузить список групп. Попробуйте позже.")
        await state.clear()
        return

    groups_text = "\n".join([f"ID: <b>{g['id']}</b> | Название: <b>{g['name']}</b>" for g in groups])
    await callback.message.answer(f"Доступные группы:\n{groups_text}\n\nВведите ID нужной группы:", parse_mode="HTML")
    await state.set_state(EventState.group)


@auth_router.message(EventState.group)
@auth_required
async def process_group(message: Message, access_token: str, state: FSMContext):
    try:
        group_id = int(message.text)
        await state.update_data(group=group_id)

        await message.answer(
            "📅 Выберите время мероприятия или введите вручную:\n"
            "Формат: <b>ГГГГ-ММ-ДД ЧЧ:ММ</b>\n"
            "Пример: <code>2025-06-19 14:30</code>",
            reply_markup=get_date_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(EventState.event_date)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID группы (число):")


@auth_router.callback_query(lambda c: c.data.startswith('date_'), EventState.event_date)
@auth_required
async def process_date_callback(callback: CallbackQuery, access_token: str, state: FSMContext):
    date_str = callback.data[5:]  # Убираем префикс 'date_'
    try:
        await state.update_data(event_date=date_str)
        await callback.message.edit_text(f"Выбрана дата: {date_str}")
        await complete_event_creation(callback.message, access_token, state)
    except ValueError:
        await callback.answer("Ошибка в формате даты")


@auth_router.message(EventState.event_date)
@auth_required
async def process_event_date(message: Message, access_token: str, state: FSMContext):
    date_str = message.text.strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M")

        event_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        if event_date < datetime.now():
            await message.answer(
                "❌ Дата не может быть в прошлом!\n"
                "Пожалуйста, введите будущую дату:",
                reply_markup=get_date_keyboard()
            )
            return

        # Если все проверки пройдены
        await state.update_data(event_date=date_str)
        await message.answer(f"Выбрана дата: {date_str}")
        await complete_event_creation(message, access_token, state)

    except ValueError:
        # Если формат неверный или дата некорректная (например, 31 февраля)
        await message.answer(
            "❌ Неверный формат или невозможная дата!\n"
            "Пожалуйста, введите дату в формате:\n"
            "<b>ГГГГ-ММ-ДД ЧЧ:ММ</b> (например: 2025-06-19 14:30)\n\n"
            "Или выберите из предложенных вариантов:",
            reply_markup=get_date_keyboard(),
            parse_mode="HTML"
        )

async def complete_event_creation(message: Message, access_token: str, state: FSMContext):
    """Общая функция завершения создания мероприятия"""
    data = await state.get_data()

    try:
        event_data = {
            "title": data['title'],
            "location": data['location'],
            "type": data['type'],
            "group": data['group'],
            "event_date": data['event_date'],
            "creator_telegram_id": message.from_user.id
        }

        await post_event(access_token, event_data)

        await message.answer(
            "✅ <b>Мероприятие успешно создано</b>\n\n"
            "📌 <b>На сайте вы сможете улучшить мероприятие:</b>\n"
            "• Добавить подробное описание\n"
            "• Загрузить материалы (фото, документы)\n"
            "• Изменить установленные данные \n\n",
            parse_mode="HTML", reply_markup=main_keyboard()
        )

        await state.clear()
    except Exception as e:
        await message.answer("⚠ Произошла ошибка при создании мероприятия")



