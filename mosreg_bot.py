from telethon import TelegramClient, events, Button, types
from telethon.events import CallbackQuery
from telethon.tl.patched import Message

import asyncio
import logging
import tracemalloc
import datetime
import collections

import sqlite3
import json
import os

import mosreg_api

loop = asyncio.get_event_loop()
scriptName = str(os.path.basename(__file__).split(".")[0])
print("Starting", scriptName)
api_id = 6
api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
app_version = '5.11.0 (1709)'
device_model = 'SM-M205FN'
system_version = 'SDK 29'

tracemalloc.start()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARN)
logger = logging.getLogger(__name__)

dbConnection = sqlite3.connect(f"data_{scriptName}.db", isolation_level=None, check_same_thread=False)


async def read_one_sqlite(sql, *args):
    data = await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args).fetchone())
    return data


async def read_all_sqlite(sql, *args):
    data = await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args).fetchall())
    return data


async def exec_sqlite(sql, *args):
    return await loop.run_in_executor(None, lambda: dbConnection.cursor().execute(sql, args))


class BotUser:
    def __init__(self, user_id, mosreg_token, payload, value, access_hash):
        self.user_id: int = user_id
        self.mosreg_token: str = str(mosreg_token)
        self.payload: str = str(payload)
        self.value: dict = json.loads(value)
        self.access_hash: int = access_hash

    async def push_changes(self):
        await exec_sqlite(
            "UPDATE mosreg_bot_user SET `mosreg_token` = ?, `payload` = ?, `value` = ?, `access_hash` = ? WHERE user_id = ?",
            self.mosreg_token, self.payload, json.dumps(self.value), self.access_hash, self.user_id)


async def get_user(in_db_id: int):
    res = await read_one_sqlite("SELECT * FROM mosreg_bot_user WHERE user_id = ?", in_db_id)
    if res is None:
        return None
    else:
        return BotUser(*res)


bot = TelegramClient("bot_" + scriptName, api_id, api_hash, app_version=app_version, device_model=device_model,
                     system_version=system_version)


async def get_text_of_hw_period(user: BotUser, start_time, end_time):
    client = mosreg_api.MosregClient(user.mosreg_token)
    homework_today = await client.get_homework_period(start_time, end_time)
    subject_map = {}
    for subject in homework_today.subjects:
        subject_map.update({subject.id: subject})
    files_map = {}
    for file in homework_today.files:
        files_map.update({file.id: file})
    full_text = ""
    days = {}
    for homework in homework_today.works:
        text = ""
        '%d/%m'
        ts = datetime.datetime.fromisoformat(homework.target_date.split('T')[0]).timestamp()
        homework: mosreg_api.FullHomeworkWork
        subject: mosreg_api.FullHomeworkSubject = subject_map[homework.subject_id]

        text = f"**{subject.name}** - {homework.text}"
        for file in homework.files:
            file: mosreg_api.FullHomeworkFile = files_map[file]
            text += f"\n[📂{file.name}]({file.download_url})"
        if ts not in days:
            days.update({ts: []})
        days[ts].append(text)
    days = dict(collections.OrderedDict(sorted(days.items())))
    for key, value in zip(days.keys(), days.values()):
        part = f"\n`--------------`\n`{datetime.datetime.fromtimestamp(key).strftime('%d/%m/%Y')}`"
        for text in value:
            part += "\n\n" + text
        full_text += part
    if not full_text:
        full_text = "Нет ДЗ за этот период"
    return full_text


async def get_text_of_marks_period(user: BotUser, start_time, end_time):
    client = mosreg_api.MosregClient(user.mosreg_token)
    full_text = ""
    days = {}
    lessons = await client.get_lessons_period(start_time, end_time)
    lesson_map = {}
    for lesson in lessons:
        lesson_map.update({lesson.id: lesson})
    marks = await client.get_marks_period(start_time, end_time)
    for mark in marks:
        ts = datetime.datetime.fromisoformat(mark.date.split('T')[0]).timestamp()
        if ts not in days:
            days.update({ts: {}})
        lesson = lesson_map[mark.lesson]
        if lesson.number not in days[ts]:
            days[ts].update({lesson.number: {'marks': [], 'name': lesson.subject.name}})
        days[ts][lesson.number]['marks'].append(mark.text_value)
    days = dict(collections.OrderedDict(sorted(days.items())))
    for day, v in zip(days.keys(), days.values()):
        part = f"\n`--------------`\n`{datetime.datetime.fromtimestamp(day).strftime('%d/%m/%Y')}`"
        v = dict(collections.OrderedDict(sorted(v.items())))
        for lesson, value in zip(v.keys(), v.values()):
            if not value['marks']:
                continue
            for mark in value['marks']:
                part += f"\n{lesson}) **{value['name']}** - {mark}"
        full_text += part + "\n\n"
    if not full_text:
        full_text = "Нет оценок за этот период"
    return full_text


def get_main_keyboard(user: BotUser):
    if not user.mosreg_token:
        kb = [Button.url("🔗Привязать ШП🔗", f"https://login.school.mosreg.ru/oauth2?response_type=token&client_id="
                                             f"594df05cfea34e66994960ae72a2150d&scope=EducationalInfo,CommonInfo,"
                                             f"SocialInfo,Files,Wall,Messages,FriendsAndRelatives&redirect_uri"
                                             f"=http://185.185.126.24:8050/get_request&state={user.user_id}&cc_key=")]
    else:
        kb = \
            [
                [Button.inline("📆Расписание📆", "schedule")],
                [Button.inline("📚Д/З📚", "homework_menu")],
                [Button.inline("5️⃣Оценки5️⃣", "marks_menu")],

                [Button.url("🔗Пере-привязать ШП🔗",
                            f"https://login.school.mosreg.ru/oauth2?response_type=token&client_id="
                            f"594df05cfea34e66994960ae72a2150d&scope=EducationalInfo,CommonInfo,"
                            f"SocialInfo,Files,Wall,Messages,FriendsAndRelatives&redirect_uri"
                            f"=http://185.185.126.24:8050/get_request&state={user.user_id}&cc_key=")],
                [Button.inline("➖Отвязать ШП➖", "unlink")]
            ]
    return kb


@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event: events.newmessage.NewMessage.Event):
    message: Message = event.message
    user = await get_user(message.sender_id)
    if not user:
        sender: types.User = await message.get_sender() if not message.sender else message.sender
        await exec_sqlite("insert into mosreg_bot_user (user_id, access_hash) values (?, ?)", message.sender_id,
                          sender.access_hash)
        user = await get_user(message.sender_id)
        await event.respond("Привязывая аккунт Школьного Портала (schools.school.mosreg.ru) Вы даете разрещение на "
                            "использование полученного доступа к вашей учётной записи Школьного Портала данным ботом."
                            " Доступ будет использоваться исключительно когда Вы делаете запрос на то или иное действие"
                            " у бота. Вы можете в любой момент отвязать аккаунт нажав на кнопку `➖Отвязать ШП➖`,"
                            " и токен доступа бдует удален. данный бот не сохраняет никакой информации о Вас, кроме "
                            "предоставлденной сервисом Telegram (что именно предоставляется указано в "
                            "пользовательском соглашении Telegram). Сервис предоставляется AS-IS (как есть), и "
                            "создатель не несет ответственности за его неполадки.")
    await event.respond("Добро пожаловать!", buttons=get_main_keyboard(user))
    raise events.StopPropagation


@bot.on(events.NewMessage())
async def message_handler(event: events.NewMessage.Event):
    message: Message = event.message


@bot.on(events.CallbackQuery)
async def callback(event: CallbackQuery.Event):
    data: str = event.data.decode("UTF-8")
    main_menu_button = [Button.inline("🔙Главное меню🏘", "main_menu")]
    user = await get_user(event.sender_id)
    homework_menu_kb = [
        [Button.inline("💼Д/З на сегодня💼", "homework_today")],
        [Button.inline("💼Д/З на завтра💼", "homework_tomorrow")],
        [Button.inline("💼Д/З на эту неделю💼", "homework_this_week")],
        [Button.inline("💼Д/З на след. неделю💼", "homework_next_week")],
        main_menu_button
    ]
    marks_menu_kb = [
        [Button.inline("💼Оценки за сегодня💼", "marks_today")],
        [Button.inline("💼Оценки за эту неделю💼", "marks_this_week")],
        [Button.inline("💼Оценки за пред. неделю💼", "marks_prev_week")],
        main_menu_button
    ]
    if data == "main_menu":
        await event.edit("Главное меню", buttons=get_main_keyboard(user))
    elif data == "homework_menu":
        await event.edit("Выберите период Д/З", buttons=homework_menu_kb)
    elif data == "homework_today":
        await event.answer("Получаю данные...")
        text = await get_text_of_hw_period(user, datetime.date.today().isoformat(), datetime.date.today().isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Д/З", buttons=homework_menu_kb)
    elif data == "homework_tomorrow":
        await event.answer("Получаю данные...")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        text = await get_text_of_hw_period(user, tomorrow, tomorrow)
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Д/З", buttons=homework_menu_kb)
    elif data == "homework_this_week":
        await event.answer("Получаю данные...")
        today = datetime.date.today()
        this_monday = today - datetime.timedelta(days=today.weekday())
        next_monday = this_monday + datetime.timedelta(days=6)
        text = await get_text_of_hw_period(user, this_monday.isoformat(), next_monday.isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Д/З", buttons=homework_menu_kb)
    elif data == "homework_next_week":
        await event.answer("Получаю данные...")
        today_plus_seven = datetime.date.today() + datetime.timedelta(days=7)
        next_monday = today_plus_seven - datetime.timedelta(days=today_plus_seven.weekday())
        next_next_monday = next_monday + datetime.timedelta(days=6)
        text = await get_text_of_hw_period(user, next_monday.isoformat(), next_next_monday.isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Д/З", buttons=homework_menu_kb)
    elif data == "schedule":
        full_text = ""
        today = datetime.date.today()
        this_monday = today - datetime.timedelta(days=today.weekday())
        next_monday = this_monday + datetime.timedelta(days=6)
        client = mosreg_api.MosregClient(user.mosreg_token)
        schedule = await client.get_schedule(this_monday.isoformat(), next_monday.isoformat())
        subjects_map = {}
        for day in schedule.days:
            for subject in day.subjects:
                subjects_map.update({subject.id: subject.name})
        for day in schedule.days:
            if not day.lessons:
                continue
            date = datetime.date.fromisoformat(day.date.split("T")[0]).strftime("%d/%m/%Y %A")
            prat_text = f"\n`--------------`\n`{date}`\n"
            for lesson in day.lessons:
                prat_text += f"{lesson.number}) **{subjects_map[lesson.subject_id]}**\n"
            full_text += prat_text
        await event.edit(full_text, buttons=None, link_preview=False)
        await event.respond("Главное меню", buttons=get_main_keyboard(user))
    elif data == "marks_menu":
        await event.edit("Выберите период Оценок", buttons=marks_menu_kb)
    elif data == "marks_today":
        await event.answer("Получаю данные...")
        text = await get_text_of_marks_period(user, datetime.date.today().isoformat(),
                                              datetime.date.today().isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Оценок", buttons=marks_menu_kb)
    elif data == "marks_this_week":
        await event.answer("Получаю данные...")
        today = datetime.date.today()
        this_monday = today - datetime.timedelta(days=today.weekday())
        next_monday = this_monday + datetime.timedelta(days=6)
        text = await get_text_of_marks_period(user, this_monday.isoformat(), next_monday.isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Оценок", buttons=marks_menu_kb)
    elif data == "marks_prev_week":
        await event.answer("Получаю данные...")
        today_plus_seven = datetime.date.today() - datetime.timedelta(days=7)
        next_monday = today_plus_seven - datetime.timedelta(days=today_plus_seven.weekday())
        next_next_monday = next_monday + datetime.timedelta(days=6)
        text = await get_text_of_marks_period(user, next_monday.isoformat(), next_next_monday.isoformat())
        await event.edit(text, buttons=None, link_preview=False)
        await event.respond("Выберите период Оценок", buttons=marks_menu_kb)
    elif data == "unlink":
        user.mosreg_token = ""
        await user.push_changes()
        await event.edit("ШП отвязан.", buttons=get_main_keyboard(user))


async def main():
    print('Preparing database...')
    await exec_sqlite("CREATE TABLE IF NOT EXISTS mosreg_bot_user (`user_id` INTEGER DEFAULT 0 PRIMARY KEY ,"
                      " `mosreg_token` TEXT DEFAULT '', `payload` TEXT DEFAULT '', `value` TEXT DEFAULT '{}', "
                      "`access_hash` INTEGER DEFAULT 0)")
    print('Starting bot...')
    await bot.start()
    print('Starting client')
    bot_user = await bot.get_me()
    print(f"Authorized bot as @{bot_user.username}")
    print('Started')
    await asyncio.gather(bot.run_until_disconnected())


loop.run_until_complete(main())
