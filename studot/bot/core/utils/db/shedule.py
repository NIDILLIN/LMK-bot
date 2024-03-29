import datetime
import logging

from typing import Literal, Union

from motor.motor_asyncio import AsyncIOMotorClient

from config import settings

from bot.core.utils.types.userinfo import UserInfo
from bot.core.utils.types.shedule import (
    WeekShedule, 
    WeekSheduleFactory, 
    DayShedule, 
    DaySheduleFactory,
    SHEDULE_DAY
)


shedule_db_logger = logging.getLogger(__name__)
shedule_db_logger.setLevel(logging.INFO)
handler = logging.FileHandler(f"logs/SheduleDB.log", mode='w')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
shedule_db_logger.addHandler(handler)
shedule_db_logger.addHandler(logging.StreamHandler())


class SheduleDB:
    def __init__(self) -> None:
        shedule_db_logger.info('Initiating MongoDB SHEDULE client')
        client = AsyncIOMotorClient(
            settings.mongo_host,
            settings.mongo_port
        )

        shedule_db_logger.info('Client connected')

        self._database = client['main']

        self._change_shedule = self._database['change_shedule']
        self._combined_shedule = self._database['combined_shedule']

        shedule_db_logger.info('SHEDULE Client is ready')

    async def _get_shedule_collection(self, week_type: Literal[0, 1, None] = None):
        """Get shedule collection by week color

        Args:
            week_type (Literal[0, 1]): 0 -- White color, 1 -- Green color

        Returns:
            Collection: Database shedule collection
        """
        if week_type is not None:
            color = week_type
        else:
            color = await self._get_week_color()

        if color == 0: # white color
            return self._database['white-shedule']
        return self._database['green-shedule']

    async def get_rings(self):
        rings = [
            'Обычные дни:',
            '8:00  - 9:30',
            '9:40  - 11:10',
            '11:40 - 13:10',
            '13:30 - 15:00',
            '15:10 - 16:40',
            '16:50 - 18:20',
            '18:30 - 20:00',

            'Среда:',
            '8:00  - 9:30',
            '9:40  - 11:10',
            '11:40 - 13:10',
            'Классный час 13:30 - 14:10',
            '14:20 – 15:50',
            '16:00 – 17:30',
            '17:40 – 19:10',
            '19:20 – 20:50'
        ]
        txt = '\n'.join(rings)
        return txt

    async def get_week_color(self):
        c = await self._get_week_color()
        if c == 0:
            return 'Белая'
        return 'Зеленая'

    async def _get_week_color(self) -> int:
        SHEDULE_DATE = datetime.datetime(2023, 1, 2)

        now_date = datetime.datetime.now()

        days = (now_date-SHEDULE_DATE).days
        days -= days%7

        if days%14==0:
            # print('белая')
            return 0
        else:
            # print('зеленая')
            return 1

    async def get_week_shedule(self, userInfo: UserInfo) -> WeekShedule:
        shedule_db_logger.info('Getting week shedule')

        shedule_collection = await self._get_shedule_collection()

        doc = await shedule_collection.find_one(
            {
                'Место': userInfo.place
            }
        )
        shedule_dict = doc['Курс'][userInfo.course][userInfo.group]
        weekShedule = WeekSheduleFactory(shedule_dict).get()

        return weekShedule

    async def get_next_week_shedule(self, userInfo: UserInfo) -> WeekShedule:
        shedule_db_logger.info('Getting week shedule')

        this_week_color = await self._get_week_color()
        if this_week_color == 0:
            next_week_color = 1
        else:
            next_week_color = 0

        shedule_collection = await self._get_shedule_collection(next_week_color)

        doc = await shedule_collection.find_one(
            {
                'Место': userInfo.place
            }
        )
        shedule_dict = doc['Курс'][userInfo.course][userInfo.group]
        weekShedule = WeekSheduleFactory(shedule_dict).get()

        return weekShedule

    async def _get_shedule_for_user(self, doc: dict, userInfo: UserInfo) -> dict:
        course_shedule = doc['Курс'].get(userInfo.course, None)
        if course_shedule is None:
            return f'Нет расписания для твоего курса ({userInfo.course})'
        
        group_shedule = course_shedule.get(userInfo.group, None)
        if group_shedule is None:
            return f'Нет расписания для твоей группы ({userInfo.group})'

        return group_shedule

    async def get_day_shedule(self, day: str, userInfo: UserInfo) -> DayShedule:
        shedule_db_logger.info('Getting day shedule')

        shedule_collection = await self._get_shedule_collection()

        doc = await shedule_collection.find_one(
            {'Место': userInfo.place}
        )
        group_shedule = await self._get_shedule_for_user(doc, userInfo)
        if isinstance(group_shedule, str):
            return group_shedule

        day_shedule = group_shedule.get(day, None)
        if day_shedule is None:
            day = 'Понедельник'
            day_shedule = group_shedule.get(day, None)

        shedule_dict = {
            day: day_shedule
        }
        dayShedule = DaySheduleFactory(shedule_dict).get()

        return dayShedule

    async def get_change_shedule(self, date: datetime.date, userInfo: UserInfo) -> DayShedule:
        shedule_db_logger.info('Getting change shedule')

        f_date = date
        if date.weekday() == 5:
            # Saturday to Monday
            f_date += datetime.timedelta(days=2)
        elif date.weekday() == 6:
            # Sunday to Monday
            f_date += datetime.timedelta(days=1)

        # Find change shedule tomorrow
        doc = await self._change_shedule.find_one(
            {
                "Место": userInfo.place,
                "Дата": f_date.strftime('%Y-%m-%d')

            }
        )
        # If no change to tomorrow find today
        if not doc:
            today = datetime.date.today()
            change_date = f_date
            f_date = today
            doc = await self._change_shedule.find_one(
                {
                    "Место": userInfo.place,
                    "Дата": today.strftime('%Y-%m-%d')
                }
            )
        try:
            course_shedule = doc["Курс"].get(userInfo.course, None)
        except TypeError:
            return f'Нет замен ни на {change_date.strftime("%m-%d")}, ни на {today.strftime("%m-%d")}'
        
        if course_shedule is None:
            return f'В заменах твоего курса ({userInfo.course}) нет'
        
        group_shedule = course_shedule.get(userInfo.group, None)
        if group_shedule is None:
            return f'В заменах твоей группы ({userInfo.group}) нет'

        day = SHEDULE_DAY.WEEKDAYS[f_date.weekday()]
        shedule = {
            day: group_shedule
        }
        dayShedule = DaySheduleFactory(shedule).get()

        return dayShedule

    async def get_combined_shedule(self, userInfo: UserInfo) -> DayShedule:
        shedule_db_logger.info('Getting combined shedule')

        shedule_collection = await self._get_shedule_collection()
        # TODO

    async def save_shedule(self, placeShedule: dict, place: str, weekType: Literal[0, 1]) -> None:
        shedule_db_logger.info('Saving group shedule')

        shedule_collection = await self._get_shedule_collection(week_type=weekType)

        r = await shedule_collection.insert_one(
            {
                "Место": place,
                **placeShedule
            }
        )

    async def save_change_shedule(self, change: dict, date: str):
        shedule_db_logger.info('Saving change shedule')

        r = await self._change_shedule.find_one(
            {
                "Место": "ЛМК",
                "Дата": date,
            }
        )
        if r is not None:
            re = await self._change_shedule.delete_one(
                {
                    "_id": r['_id']
                }
            )
        
        r = await self._change_shedule.insert_one(
            {
                "Место": "ЛМК",
                "Дата": date,
                **change
            }
        )


sheduleDB = SheduleDB()