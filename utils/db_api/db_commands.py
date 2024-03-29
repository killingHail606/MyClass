import datetime

from aiogram import types, Bot

from gino import Gino
from gino.schema import GinoSchemaVisitor

from sqlalchemy.dialects.postgresql import Any
from sqlalchemy import (Column, Integer, BigInteger, String, ARRAY, ForeignKey, Date, Sequence)
from sqlalchemy.orm import relationship
from sqlalchemy import sql

from data.config import db_pass, db_user, host

db = Gino()


class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    telegram_id = Column(BigInteger)
    tg_nickname = Column(String())
    class_id = Column(Integer)
    name = Column(String(150))

    query: sql.Select

    def __repr__(self):
        return f"id: {self.id}, telegram: {self.telegram_id}, class: {self.class_id}"


class SchoolClass(db.Model):
    __tablename__ = 'class'

    id = Column(Integer, Sequence('class_id_seq'), primary_key=True)
    name = Column(String(50))
    telegram_chat = Column(String(50))
    members = Column(ARRAY(BigInteger))

    query: sql.Select

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Notice(db.Model):
    __tablename__ = 'notice'

    id = Column(Integer, Sequence('notice_id_seq'), primary_key=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))
    name = Column(String(250))
    body = Column(String(500))

    query: sql.Select

    school_class = relationship('SchoolClass', foreign_keys='SchoolClass.class_id')


class Events(db.Model):
    __tablename__ = 'events'

    id = Column(Integer, Sequence('event_id_seq'), primary_key=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))
    name = Column(String(150))
    date = Column(Date())
    description = Column(String(500))
    tasks = Column(ARRAY(String(250)))
    complete_tasks = Column(ARRAY(String(250)))

    query: sql.Select

    school_class = relationship('SchoolClass', foreign_keys='SchoolClass.class_id')


class LessonSchedule(db.Model):
    __tablename__ = 'lesson_schedule'
    id = Column(Integer, Sequence('schedule_id_seq'), primary_key=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))
    monday = Column(ARRAY(String(100)))
    tuesday = Column(ARRAY(String(100)))
    wednesday = Column(ARRAY(String(100)))
    thursday = Column(ARRAY(String(100)))
    friday = Column(ARRAY(String(100)))

    query: sql.Select

    school_class = relationship('SchoolClass', foreign_keys='SchoolClass.class_id')


class home_task(db.Model):
    __tablename__ = 'home_task'
    id = Column(Integer, Sequence('home_task_seq'), primary_key=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))
    lesson = Column(String(250))
    date = Column(Date())
    task = Column(String(300))

    school_class = relationship('SchoolClass', foreign_keys='SchoolClass.class_id')


class CollectingMoney(db.Model):
    __tablename__ = 'collecting_money'

    id = Column(Integer, Sequence('money_id_seq'), primary_key=True)
    class_id = Column(Integer, ForeignKey(SchoolClass.id))
    name = Column(String(150))
    target = Column(Integer)

    query: sql.Select

    donated_money = relationship('User', backref='collecting_money', lazy='dynamic')
    school_class = relationship('SchoolClass', foreign_keys='SchoolClass.class_id')


async def get_user_from_db(telegram_id):
    user = await User.query.where(User.telegram_id == telegram_id).gino.first()
    return {'user': user, 'create': False}


async def new_user():
    user_id = types.User.get_current().id
    user_nickname = types.User.get_current().full_name
    old_user = await get_user_from_db(user_id)
    if old_user['user']:
        return old_user

    new_user = User()
    new_user.telegram_id = user_id
    new_user.tg_nickname = user_nickname
    await new_user.create()
    return {'user': new_user, 'create': True}


async def check_in_class():
    user = types.User.get_current()
    user_class = await SchoolClass.query.where(Any(user.id, SchoolClass.members)).gino.all()
    return user_class


async def get_class():
    user = types.User.get_current()
    user_class = await SchoolClass.query.where(Any(user.id, SchoolClass.members)).gino.first()
    return user_class


async def get_class_by_id(class_id):
    user_class = await SchoolClass.query.where(SchoolClass.id == int(class_id)).gino.first()
    return user_class


async def get_id_class():
    user_class = await check_in_class()
    id = str(user_class[0]).split(',')[0].split(':')[1].strip()  # [id: 0, name: name]
    return id


async def get_notice():
    id = await get_id_class()
    notices = await Notice.query.where(Notice.class_id == int(id)).gino.all()
    return notices


async def get_notice_by_id(notice_id):
    notice = await Notice.query.where(Notice.id == notice_id).gino.first()
    return notice


async def get_event():
    id = await get_id_class()
    events = await Events.query.where(Events.class_id == int(id)).gino.all()
    return events


async def get_event_by_id(event_id):
    event = await Events.query.where(Events.id == int(event_id)).gino.first()
    return event


async def get_schedule():
    id = await get_id_class()
    schedule = await LessonSchedule.query.where(LessonSchedule.class_id == int(id)).gino.first()
    return schedule


async def get_set_all_subjects():
    schedule = await get_schedule()
    all_days_lists = [schedule.monday, schedule.tuesday, schedule.wednesday, schedule.thursday, schedule.friday]
    all_days = []
    for schedule_day in all_days_lists:
        if schedule_day:
            for subject in schedule_day:
                all_days.append(subject)
    all_days = set(all_days)
    return all_days


async def get_days_of_subject(subject):
    schedule = await get_schedule()
    schedule_week_dict = {
        '1': schedule.monday,
        '2': schedule.tuesday,
        '3': schedule.wednesday,
        '4': schedule.thursday,
        '5': schedule.friday
    }

    days = []
    for day, schedule_of_day in schedule_week_dict.items():
        if schedule_of_day and subject in schedule_of_day:
            days.append(day)
    return days


async def get_user():
    tg_user = types.User.get_current().id
    user = await User.query.where(User.telegram_id == int(tg_user)).gino.first()
    return user


async def get_user_by_tg_id(tg_id):
    user = await User.query.where(User.telegram_id == int(tg_id)).gino.first()
    return user


async def get_hometasks_date_interval(start_date, end_date):
    home_tasks = await home_task.query.where(home_task.date >= start_date).where(home_task.date < end_date).gino.all()
    return home_tasks


async def create_db():
    await db.set_bind(f'postgresql://{db_user}:{db_pass}@{host}/my_class_db')

    # Create tables
    # db.gino: GinoSchemaVisitor
    # await db.gino.drop_all()
    # await db.gino.create_all()
