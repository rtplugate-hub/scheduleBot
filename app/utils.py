from datetime import datetime
import logging

from aiogram.fsm.context import FSMContext

from app.config import Config


async def create_msg(config: Config, state: FSMContext, day_idx: int = None, target_date: datetime = None):
    now = target_date or datetime.now(config.tz)

    if day_idx is None:
        day_idx = now.weekday()

    week = config.get_week_for_date(now)

    day_name = config.days[day_idx]
    day_str = now.strftime("%d.%m")

    header = f"<b>📅 {day_name} ({day_str})</b>\n"
    header += f"<i>Тиждень {week}</i>"

    if day_idx > 4:
        return f"{header}\n\n<b>Вихідний! Пар немає</b>"

    try:
        day_schedule = config.settings.schedule[week - 1][day_idx]
    except IndexError:
        return f"{header}\n\nПомилка: Розклад не знайдено."

    lesson_rows = []
    for i, code in enumerate(day_schedule):
        if not code or code == "None":
            continue

        subject = config.settings.subjects.get(code)
        lesson_time = config.settings.time[i] if i < len(config.settings.time) else "--:--"

        if subject:
            row = f"<b>{i + 1}. [{lesson_time}] <a href='{subject.link}'>{subject.name}</a></b>"
            lesson_rows.append(row)

    if not lesson_rows:
        return f"{header}\n\nСьогодні пар немає, відпочивай!"

    return header + "\n\n" + "\n\n".join(lesson_rows)
