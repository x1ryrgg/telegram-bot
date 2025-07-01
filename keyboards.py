from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta


def main_keyboard():
    kb_buttons = [
        [KeyboardButton(text='Создать мероприятие')],
        [KeyboardButton(text='Просмотреть мероприятия')],
        [KeyboardButton(text='Профиль')],
        [KeyboardButton(text='Выйти из акканута')]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_buttons, resize_keyboard=True,
                                   input_field_placeholder='Выбирите пункт на клавиатуре')
    return keyboard

def get_location_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ул. 20-летия Октября, 84",
                               callback_data="location_20_oktyabrya")
        ],
        [
            InlineKeyboardButton(text="ул. Плехановская, 11",
                               callback_data="location_plehanovskaya")
        ],
        [
            InlineKeyboardButton(text="Московский проспект, 179",
                               callback_data="location_moskovskiy")
        ]
    ])


def type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="конференция", callback_data="type_conference")],
    [InlineKeyboardButton(text="конкурс", callback_data="type_contest")],
    [InlineKeyboardButton(text="экскурсия", callback_data="type_excursion")],
    [InlineKeyboardButton(text="семинар", callback_data="type_seminar")]
])


def get_date_keyboard():
    """Клавиатура с предложением текущей даты и вариантами"""
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')

    builder = InlineKeyboardBuilder()

    for hour in [9, 13, 16]:
        # Сегодня - левый столбец
        builder.button(
            text=f"🕘 {hour}:00 (сегодня)",
            callback_data=f"date_{today} {hour}:00"
        )
        # Завтра - правый столбец
        builder.button(
            text=f"🕘 {hour}:00 (завтра)",
            callback_data=f"date_{tomorrow} {hour}:00"
        )

    builder.adjust(2, 2, 2)
    return builder.as_markup()
