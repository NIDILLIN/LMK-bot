# from overrides import override
from typing import Union
from dataclasses import dataclass

from .userinfo import UserInfo


@dataclass(frozen=True)
class SHEDULE_DAY:
    monday = 'Понедельник'
    tuesday = 'Вторник'
    wednesday = 'Среда'
    thursday = 'Четверг'
    friday = 'Пятница'
    saturday = 'Суббота'
    sunday = 'Воскресенье'

    WEEKDAYS = [
        'Понедельник', 
        'Вторник', 
        'Среда', 
        'Четверг',
        'Пятница',
        'Суббота',
        'Воскресенье',

        'Понедельник'
    ]
    MONTHS = [
        'Январь', 
        'Февраль', 
        'Март', 
        'Апрель', 
        'Май', 
        'Июнь', 
        'Июль', 
        'Август', 
        'Сентябрь', 
        'Октрябрь', 
        'Ноябрь', 
        'Декабрь'
    ]


@dataclass(frozen=True)
class SHEDULE_TIME:
    one = ('8:00', '9:30')
    two = ('9:40', '11:10')
    three = ('11:40', '13:10')
    hour = ('13:30', '14:10')
    four = ('13:30', '15:00')
    five = ('15:10', '16:40')
    six = ('16:50', '18:20')
    seven = ('18:30', '20:00')

    wed_four = ('14:20', '15:50')
    wed_five = ('16:00', '17:30')
    wed_six = ('17:40', '19:10')
    wed_seven = ('19:20', '20:50')

    SUBJECTS = [one, two, three, four, five, six, seven]
    WED_SUBJECTS = [one, two, three, wed_four, wed_five, wed_six, wed_seven]


class Subject:
    """Subject class for representive subjects

    Attributes:
        name (str): Group name
        time (str): Time in string when subject to start
    """

    name: str
    time: tuple[str]

    def __init__(self, name: str, time: Union[tuple[str], list[str], str]) -> None:
        self.name = name
        self.time = time
        if isinstance(time, str):
            time = time.split('-')
            self.time = (time[0], time[1])

    def __str__(self) -> str:
        return self.__dict__().__str__()

    def __repr__(self) -> str:
        return self.__dict__().__str__()

    def __dict__(self) -> dict:
        return {
            "Пара": self.name,
            "Время": f"{self.time[0]}-{self.time[1]}"
        }


class IShedule:
    def dict(self) -> dict:
        ...


class DayShedule(IShedule):
    """Represent of a day shedule

    Attributes:
        name (str): Day name of the week
        subjects (lits[Subject]): List of subjects by a day
    """

    _name: str
    _subjects: list[Subject]

    def __init__(self, 
            day: SHEDULE_DAY, 
            subjects: list[Subject],
            keys: list[str]) -> None:
        
        self._name = day
        self._subjects = subjects
        self.keys = keys

        self._make_dict()

    def _make_dict(self):
        subs = [sub.__dict__() for sub in self._subjects]

        self.shedule = dict(zip(self.keys, subs))

    @property
    def name(self) -> str:
        return self._name

    @property
    def subjects(self) -> list[Subject]:
        return self._subjects

    # @override
    def dict(self) -> dict:
        return self.shedule

    def __repr__(self) -> str:
        re = ''
        for c, subject in enumerate(self._subjects):
            re += f'{self.keys[c]}: {subject.name}\n({subject.time[0]}-{subject.time[1]})\n'
        return re


class WeekShedule(IShedule):
    """
    Represent of a week shedule.
    This is a list of DayShedule
    """

    def __init__(self, days_shedule: list[DayShedule]) -> None:
        days = [day.name for day in days_shedule]
        shedule = [day_shed.dict() for day_shed in days_shedule]

        self.week_shedule = dict(zip(days, shedule))
        self._shedule = days_shedule

    # @override
    def dict(self) -> dict:
        return self.week_shedule

    def day(self, day: str) -> DayShedule:
        return self.week_shedule[day]

    def days_with(self, subject: str):
        con = {}
        for day, shedule in self.week_shedule.items():
            for sub in shedule.values():
                if sub.name == subject:
                    con[day] = shedule
                    break
        return con

    def __repr__(self) -> str:
        re = ''
        for shedule in self._shedule:
            re += f'{shedule.name}:\n{shedule}\n\n'
        return re


class GroupShedule(IShedule):
    """Represent User group info

    Attributes:
        group (str): Group name
        place (str): Place where group from
        shedule (WeekShedule): Shedule for a week for that group
    """

    group: str
    course: int
    place: str
    shedule: WeekShedule

    def __init__(self, userInfo: UserInfo, shedule: WeekShedule) -> None:
        self.group = userInfo.group
        self.place = userInfo.place
        self.course = userInfo.course
        self.shedule = shedule

    def get_shedule_for(self, day: SHEDULE_DAY) -> DayShedule:
        shedule = self.shedule.day(day)
        return shedule

    def days_with_subject(self, subject: str) -> WeekShedule:
        shedule = self.shedule.days_with(subject)
        return shedule

    # @override
    def dict(self):
        d = {
            'Группа': self.group,
            'Место': self.place,
            'Расписание': self.shedule.dict()
        }
        return d


class ISheduleFactory:
    def __init__(self, document: dict) -> None:
        self.shedule = self._process_doc(document)

    def get(self) -> IShedule:
        return self.shedule

    def _process_doc(self, document: dict) -> None:
        """Must be overided
        """
        ...


class DaySheduleFactory(ISheduleFactory):
    """Build DayShedule from a dict
    """
    # @override
    def _process_doc(self, document: dict) -> None:
        # {
        #     'Понедельник': {
        #         '1': {
        #             "Пара": "Математика",
        #             "Время": "8:00-9:30"
        #         }

        #     }
        # }
        day = list(document.keys())[0]
        subs = document[day]
        keys = list(document[day].keys())

        shedule = DayShedule(
            day=day,
            subjects=[
                Subject(sub['Пара'], sub['Время']) 
                for sub in subs.values()
            ],
            keys=keys
        )
        return shedule


class WeekSheduleFactory(ISheduleFactory):
    """Build WeekShedule from a dict
    """
    def _process_doc(self, document: dict) -> WeekShedule:
        days = []
        for day, shedule in document.items():
            keys = list(shedule.keys())
            days.append(
                DayShedule(
                    day=day,
                    subjects=[
                        Subject(sub['Пара'], sub['Время']) 
                        for sub in shedule.values()
                    ],
                    keys=keys
                )
            )
        return WeekShedule(days)