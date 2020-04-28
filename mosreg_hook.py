from aiohttp import web
from telethon import TelegramClient
from telethon.tl.types import InputUser
import os
import json
import asyncio
import logging
import tracemalloc
import sqlite3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARN)
tracemalloc.start()
scriptName = str(os.path.basename(__file__).split(".")[0])
loop = asyncio.get_event_loop()
print("Starting", scriptName)
api_id = 6
api_hash = "eb06d4abfb49dc3eeb1aeb98ae0f581e"
app_version = '5.11.0 (1709)'
device_model = 'SM-M205FN'
system_version = 'SDK 29'
dbConnection = sqlite3.connect(f"data_mosreg_bot.db", isolation_level=None, check_same_thread=False)
bot = TelegramClient("bot_" + scriptName, api_id, api_hash, app_version=app_version, device_model=device_model,
                     system_version=system_version)


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


async def get_request(request: web.Request):
    body = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title></title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
Аккаунт привязан.
<script type="text/javascript">
console.log("Hi")
if (document.URL.indexOf("#") != -1)
{
    console.log("!")
    var this_url = document.URL.replace("#", "?").replace("get_request", "token_listen");
    console.log(this_url)
    const request = new XMLHttpRequest();
    request.open('GET', this_url);
    request.setRequestHeader('Content-Type', 'application/x-www-form-url');
    request.addEventListener("readystatechange", () => {
    if (request.readyState === 4 && request.status === 200) {
        document.location.href = "tg://@school_mosreg_bot";
    }
});
    request.send(); 
    console.log(request.readyState)
    
    
}
</script> 
</body>
</html>"""
    return web.Response(status=200, body=body, headers={"content-type": "text/html; charset=utf-8"})


async def token_listen(request: web.Request):
    print("Got token")
    access_token = request.rel_url.query['access_token']
    user_id = int(request.rel_url.query['state'])
    user = await get_user(user_id)
    user.mosreg_token = access_token
    await user.push_changes()
    await bot.send_message(InputUser(user.user_id, user.access_hash), "✅Аккаунт привязан!✅\nОтправь /start чтобы "
                                                                      "открыть меню")
    return web.Response(status=200)


app = web.Application()
app.add_routes([
    web.get("/get_request", get_request),
    web.get("/token_listen", token_listen),
])


async def main():
    await bot.start()
    task = web._run_app(app, shutdown_timeout=60.0, backlog=128, port=8050)
    await asyncio.gather(task)


loop.run_until_complete(main())
