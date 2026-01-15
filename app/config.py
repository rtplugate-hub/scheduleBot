import calendar
import locale
import logging
import os
from pathlib import Path

import pytz
import yaml
from pydantic import BaseModel, model_validator, ValidationError
from typing import Dict, List, Optional, Union
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
    schedule: List[Dict[int, List[Optional[Union[str, Subject]]]]]
    time: List[str]
    admins: List[int]
    academic_context: AcademicContext

    @model_validator(mode='after')
    def map_subjects(self):
        new_schedule = []
        for week in self.schedule:
            new_week = {}
            for day_idx, lessons in week.items():
                new_week[day_idx] = [
                    self.subjects.get(lesson) if isinstance(lesson, str) else lesson
                    for lesson in lessons
                ]
            new_schedule.append(new_week)
        self.schedule = new_schedule
        return self


class RootConfig(BaseModel):
    settings: ConfigSchema


class Config:
    def __init__(self, config_name="config.yaml"):
        self.path = BASE_DIR / config_name
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found at {self.path}")
        try:
            locale.setlocale(locale.LC_TIME, 'uk_UA.UTF-8')
        except locale.Error:
            logging.info('Could not set locale to uk_UA.UTF-8, trying ukr_ukr for Windows.')
            try:
                locale.setlocale(locale.LC_TIME, 'ukr_ukr')
            except locale.Error:
                raise RuntimeError("Could not set locale to 'uk_UA.UTF-8' or 'ukr_ukr'. Please check your system's locale settings.")
        self.days: List[str] = [d.capitalize() for d in calendar.day_name]
        self.tz = pytz.timezone('Europe/Kyiv')
        self.settings = None
        self.bot_token = None
        self.load()

    def load(self):
        load_dotenv(BASE_DIR / '.env')
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found at {self.path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file: {e}")

        try:
            root = RootConfig(**raw_data)
            self.settings = root.settings
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")

        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable not set")

    @property
    def total_weeks(self) -> int:
        return len(self.settings.schedule)

    @property
    def current_week_number(self) -> int:
        return self.get_week_for_date(datetime.now(self.tz))

    def get_week_for_date(self, date: datetime) -> int:
        ctx = self.settings.academic_context
        try:
            ref_date = datetime.strptime(ctx.reference_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid reference_date format in config. Expected YYYY-MM-DD")

        delta_days = (date.replace(tzinfo=None) - ref_date).days
        weeks_passed = delta_days // 7

        if self.total_weeks == 0:
            raise ValueError("The schedule is empty, cannot determine week number.")

        return (ctx.reference_week - 1 + weeks_passed) % self.total_weeks + 1

    def get_day_schedule(self, week_idx: int, day_idx: int) -> Optional[List[Optional[Subject]]]:
        if week_idx < 0 or week_idx >= len(self.settings.schedule):
            return None
        
        week_schedule = self.settings.schedule[week_idx]
        return week_schedule.get(day_idx + 1)

    @property
    def today_lessons(self) -> Optional[List[Optional[Subject]]]:
        week_idx = self.current_week_number - 1
        day_idx = datetime.now(self.tz).weekday()
        return self.get_day_schedule(week_idx, day_idx)


if __name__ == '__main__':
    try:
        config = Config('config.yaml')
        print(f"Week №{config.current_week_number}")
        print(config.today_lessons)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
