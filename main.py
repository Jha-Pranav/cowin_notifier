import requests
from datetime import date, datetime
from pygame import mixer
import schedule
import time
from twilio.rest import Client
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


async def send_telegram_message(receiver, msg):
    print("Sending message to : ", receiver)
    await client.send_message(receiver, msg)


def play_music():
    audio_file_path = "Bavra Mann Dekhne Lyric Video Cover Song.mp3"
    # Starting the mixer
    mixer.init()

    # Loading the song
    mixer.music.load(audio_file_path)

    # Setting the volume
    mixer.music.set_volume(1)

    # Start playing the song
    mixer.music.play()

    # infinite loop
    while True:

        print("Press 'p' to pause, 'r' to resume")
        print("Press 'e' to exit the program")
        query = input(" ")

        if query == "p":

            # Pausing the music
            mixer.music.pause()
        elif query == "r":

            # Resuming the music
            mixer.music.unpause()
        elif query == "e":

            # Stop the mixer
            mixer.music.stop()
            break


def send_text_sms(msg):
    # this is the Twilio sandbox testing number
    from_number = "+14704607438"
    # replace this number with your own WhatsApp Messaging number
    to_number = "+9182*****"

    twilio_client.messages.create(body=msg, from_=from_number, to=to_number)


def filter_response(
    result, age_group, only_free=False, minimum_seat_required=None, only_fist_dose=False
):
    text = ""
    for en in result["centers"]:
        fee_type = en["fee_type"]
        if only_free and fee_type.lower() != "free":
            continue
        sessions = en["sessions"]
        availability = (
            session
            for session in sessions
            if session["available_capacity"] > 0
            and session["min_age_limit"] == age_group
        )
        availability = [i for i in availability if i]
        if minimum_seat_required:
            availability = [
                i
                for i in availability
                if i["available_capacity"] >= minimum_seat_required
            ]

        if any(availability):
            center = (
                en["name"]
                + ", "
                + en["address"]
                + ", "
                + en["district_name"]
                + ", "
                + en["state_name"]
            )

            if only_fist_dose and sum(
                [
                    details["available_capacity"] - details["available_capacity_dose2"]
                    for details in availability
                ]
            ):
                text += f"Center : {center}\n"
                for details in availability:
                    if only_fist_dose:
                        if not (
                            details["available_capacity"]
                            - details["available_capacity_dose2"]
                        ):
                            continue

                    text += f"Date : {details['date']}  Vaccine : {details['vaccine']}  Available: {details['available_capacity']}\n"
                    text += f"Dose1 : {details['available_capacity_dose1']}  Dose2 : {details['available_capacity_dose2']}\n"
                text += "--" * 15 + "\n"
    return text


def get_response(pincode):
    headers = {
        "authority": "cdn-api.co-vin.in",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        "accept": "application/json, text/plain, */*",
        "dnt": "1",
        "sec-ch-ua-mobile": "?0",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
        "origin": "http://www.cowin.gov.in",
        "sec-fetch-site": "cross-site",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "referer": "http://www.cowin.gov.in/",
        "accept-language": "en-US,en;q=0.9,hi;q=0.8,lb;q=0.7",
        "if-none-match": 'W/"4a9-uQBLeZh9sZX2prS+yRP/SfykrE8"',
    }

    params = (
        ("pincode", pincode),
        ("date", date.today().strftime("%d-%m-%Y")),
    )

    response = requests.get(
        "http://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin",
        headers=headers,
        params=params,
    )
    result = response.json()
    return result


def main(bucket):
    for pincode, values in bucket.items():
        result = get_response(pincode)

        text_message = filter_response(
            result, values[1], values[2], values[3], values[4]
        )
        if text_message:
            # play_music()
            text_message += "\nhttps://www.cowin.gov.in/home"
            send_text_sms(text_message)
            with client:
                for number in values[0]:
                    client.loop.run_until_complete(
                        send_telegram_message(number, text_message)
                    )


if __name__ == "__main__":

    # Your Account SID from twilio.com/console
    account_sid = "AC5f431f3b4d4acdee0a35b6f5c715edb8"
    # Your Auth Token from twilio.com/console
    auth_token = "b164682f3bbada624039085d05b97751"
    twilio_client = Client(account_sid, auth_token)

    bucket = {
        "847409": (["+918257803929"], 18, True, 1, True),
        "846004": (
            ["+918257803929", "+917004221223", "+918294515154"],
            18,
            True,
            1,
            True,
        ),
        "122001": (["+918257803929"], 18, True, 2, True),
        "414002": (["+918329622093"], 18, True, 5, True),
    }

    def perform_query():
        print(f"Availability @ {datetime.now()} checked.")
        main(bucket)

    perform_query()
    schedule.every(5).minutes.do(perform_query)
    while True:
        schedule.run_pending()
        time.sleep(1)
