import calendar
import locale
import logging
import os
from pathlib import Path

import pytz
import yaml
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


class Subject(BaseModel):
    name: str
    link: str


class AcademicContext(BaseModel):
    reference_date: str
    reference_week: int


class ConfigSchema(BaseModel):
    subjects: Dict[str, Subject]
    schedule: List[List[List[Optional[str]]]]
    time: List[str]
    admins: List[int]
    academic_context: AcademicContext


class RootConfig(BaseModel):
    settings: ConfigSchema


class Config:
    def __init__(self, config_name="config.yaml"):
        self.path = BASE_DIR / config_name
        try:
            locale.setlocale(locale.LC_TIME, 'uk_UA.UTF-8')
        except:
            logging.info('fuck windows')
            locale.setlocale(locale.LC_TIME, 'ukr_ukr')
        self.days: List[str] = [d.capitalize() for d in calendar.day_name]
        self.tz = pytz.timezone('Europe/Kyiv')
        self.reload()

    def reload(self):
        load_dotenv(BASE_DIR / '.env')
        with open(self.path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        root = RootConfig(**raw_data)
        self.settings = root.settings
        self.bot_token = os.getenv('BOT_TOKEN')

    @property
    def total_weeks(self) -> int:
        return len(self.settings.schedule)

    @property
    def current_week_number(self) -> int:
        return self.get_week_for_date(datetime.now(self.tz))

    def get_week_for_date(self, date: datetime) -> int:
        ctx = self.settings.academic_context
        ref_date = datetime.strptime(ctx.reference_date, "%Y-%m-%d")

        delta_days = (date.replace(tzinfo=None) - ref_date).days
        weeks_passed = delta_days // 7

        return (ctx.reference_week - 1 + weeks_passed) % self.total_weeks + 1

    @property
    def today_lesson(self):
        week_idx = self.current_week_number - 1
        day_idx = datetime.now(self.tz).weekday()

        if day_idx > 4:
            return 'Вихідний!'

        return self.settings.schedule[week_idx][day_idx]


if __name__ == '__main__':
    config = Config('../config.yaml')
    print(f"Week №{config.current_week_number}")
    print(config.today_lesson)
