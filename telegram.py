import json
from configparser import ConfigParser
from telethon import TelegramClient, events, Button

import logging

logging.basicConfig(
    format="[%(levelname) 5s/%(a sctime)s] %(name)s: %(message)s", level=logging.WARNING
)

# Reading Configs
config = ConfigParser()
config.read("config.ini")

# Setting configuration values
api_id = config["Telegram"]["api_id"]
api_hash = config["Telegram"]["api_hash"]

phone = config["Telegram"]["phone"]
username = config["Telegram"]["username"]

client = TelegramClient(username, api_id, api_hash)


async def send_telegram_message(msg):
    await client.send_message("+918257803929", msg)


with client:
    client.loop.run_until_complete(send_telegram_message("Hello friends!"))
