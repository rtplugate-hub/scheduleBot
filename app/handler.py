from datetime import datetime, timedelta
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import Config
from app.utils import create_msg, render_keyboard

rout = Router()


WEEKS_BUTTONS = {
    "← Попередній тиждень": -1,
    "Наступний тиждень →": 1
}

REL_BUTTONS = {
    "Сьогодні": 0,
    "Завтра": 1
}


@rout.message(Command('reload'))
async def reload_config(msg: types.Message, state: FSMContext, config: Config):
    if msg.from_user.id in config.settings.admins:
        config.load()
        await msg.answer("Config reloaded")
        await render_keyboard(msg, state, config)


@rout.message(Command("start"))
async def start(msg: types.Message, state: FSMContext, config: Config):
    await render_keyboard(msg, state, config)


@rout.message(F.text.in_(WEEKS_BUTTONS.keys()))
async def switch_week(msg: types.Message, state: FSMContext, config: Config):
    data = await state.get_data()
    viewing_week = data.get("viewing_week", config.current_week_number)

    step = WEEKS_BUTTONS[msg.text]

    new_week = (viewing_week + step - 1) % config.total_weeks + 1

    await state.update_data(viewing_week=new_week)
    await msg.answer(f"Увімкнено перегляд: <b>{new_week}-й тиждень</b>", parse_mode="HTML")
    await render_keyboard(msg, state, config)


@rout.message(F.text.in_({"Сьогодні", "Завтра"}))
async def rel_show(msg: types.Message, state: FSMContext, config: Config):
    target_date = datetime.now(config.tz) + timedelta(days=REL_BUTTONS[msg.text])

    day_idx = target_date.weekday()
    txt = await create_msg(config, state, day_idx=day_idx, target_date=target_date)

    await msg.answer(txt, parse_mode="HTML", disable_web_page_preview=True)


@rout.message(lambda msg, config: msg.text in config.days)
async def man_show(msg: types.Message, state: FSMContext, config: Config):
    data = await state.get_data()
    viewing_week = data.get("viewing_week", config.current_week_number)
    day_idx = config.days.index(msg.text)

    today = datetime.now(config.tz).replace(hour=0, minute=0, second=0, microsecond=0)
    days_diff = day_idx - today.weekday()
    target_date = today + timedelta(days=days_diff)

    actual_week = config.get_week_for_date(target_date)

    if actual_week != viewing_week:
        week_diff = viewing_week - actual_week
        target_date += timedelta(weeks=week_diff)

    await state.update_data(viewing_day=day_idx)
    txt = await create_msg(config, state, day_idx=day_idx, target_date=target_date)
    await msg.answer(txt, parse_mode="HTML", disable_web_page_preview=True)
