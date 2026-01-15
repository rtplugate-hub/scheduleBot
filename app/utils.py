from datetime import datetime
import logging

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.config import Config
from app.states import Mode


async def create_msg(config: Config, state: FSMContext, day_idx: int = None, target_date: datetime = None):
    now = target_date or datetime.now(config.tz)

    if day_idx is None:
        day_idx = now.weekday()

    week = config.get_week_for_date(now)

    day_name = config.days[day_idx]
    day_str = now.strftime("%d.%m")

    header = f"<b>{day_name} ({day_str})</b>\n"
    header += f"<i>Тиждень {week}</i>"

    if day_idx > 4:
        return f"{header}\n\n<b>Вихідний! Пар немає</b>"

    day_schedule = config.get_day_schedule(week - 1, day_idx)

    if day_schedule is None:
        return f"{header}\n\nСьогодні пар немає, відпочивай!"

    lesson_rows = []

    for i, subject in enumerate(day_schedule):
        if not subject or subject == "None":
            continue

        if isinstance(subject, str):
            subject_obj = config.settings.subjects.get(subject)
        else:
            subject_obj = subject

        lesson_time = config.settings.time[i] if i < len(config.settings.time) else "--:--"

        if subject_obj:
            row = f"<b>{i + 1}. <a href='{subject_obj.link}'>{subject_obj.name}</a> [{lesson_time}]</b>"
            lesson_rows.append(row)

    if not lesson_rows:
        return f"{header}\n\nСьогодні пар немає, відпочивай!"

    return header + "\n\n" + "\n\n".join(lesson_rows)


async def render_keyboard(msg: types.Message, state: FSMContext, config: Config):
    await state.set_state(Mode.main)
    data = await state.get_data()
    viewing_week = data.get("viewing_week", config.current_week_number)

    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Сьогодні"), KeyboardButton(text="Завтра"))

    days_with_schedule = []
    week_schedule = config.settings.schedule[viewing_week - 1]

    for day_idx, day_name in enumerate(config.days):
        day_key = day_idx + 1

        day_lessons = week_schedule.get(day_key)

        if day_lessons and any(lesson is not None for lesson in day_lessons):
            days_with_schedule.append(day_name)

    for day in days_with_schedule:
        builder.add(KeyboardButton(text=day))

    builder.add(
        KeyboardButton(text="← Попередній тиждень"),
        KeyboardButton(text="Наступний тиждень →")
    )

    sizes = [2]
    num_day_buttons = len(days_with_schedule)
    if num_day_buttons > 0:
        sizes.extend([2] * (num_day_buttons // 2))
        if num_day_buttons % 2 == 1:
            sizes.append(1)

    sizes.append(2)
    builder.adjust(*sizes)

    await msg.answer(
        "Оберіть день або тиждень:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
