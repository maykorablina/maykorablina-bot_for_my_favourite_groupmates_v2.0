import base64
import asyncio
import time
import sqlite3
from gmail_functions import check_gmail, instance_check_gmail
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

TOKEN_API = "nothing to see here"
bot = Bot(TOKEN_API, parse_mode="HTML")
dp = Dispatcher()
my_channel_id = 7355608

waiting_time = 60


@dp.message(Command("start"))
async def beginning(message):
    msg = await message.answer(text="initializing bot")
    msg = await msg.answer(text="getting the first letter...")
    first_mail = instance_check_gmail()[0]
    if first_mail:
        msg = await msg.answer(text=f"got first letter with id:{first_mail}")
        msg = await msg.answer(text=f"initializing monitoring procedure")
        time.sleep(waiting_time)
        await main_process(msg, first_mail)


async def main_process(message, last_mail_id):
    new_mail_id = instance_check_gmail()[0]
    msg = await message.answer(text=f"got letter with id:{new_mail_id}")
    if last_mail_id == new_mail_id:
        msg = await msg.answer(text=f"no new letters so far")
        time.sleep(waiting_time)
        await main_process(msg, last_mail_id)
    else:
        msg = await msg.answer(text=f"new letter! id:{new_mail_id}")
        last_mail = check_gmail()[0]
        if last_mail["topic"] in [
            "Важное оповещение системы безопасности",
            "Оповещение системы безопасности",
        ]:
            msg = await msg.answer(text=f"security letter -- skip")
            time.sleep(waiting_time)

        else:
            try:
                await send_letter_to_channel(msg)
                msg = await msg.answer(
                    text=f"id:{new_mail_id} successfully sent to the channel"
                )
                time.sleep(waiting_time)
                await main_process(msg, new_mail_id)
            except Exception as exception:
                msg = await msg.answer(
                    text=f"something went wrond and id:{new_mail_id} hasnt been sent to channel"
                )
                msg = await msg.answer(
                    text=f"a mistake occured: {type(exception).__name__}"
                )
                time.sleep(waiting_time)
                await main_process(msg, new_mail_id)


async def send_letter_to_channel(message):
    last_mail = check_gmail()[0]
    if last_mail["topic"] in [
        "Важное оповещение системы безопасности",
        "Оповещение системы безопасности",
    ]:
        return -1
    text = last_mail["text"]
    text = text.replace(">", "")
    text = text.replace("<", "")
    text = text.replace("\t", " ")
    text = text.replace("\r", " ")
    text = text.split("\n")
    text = [x.strip() for x in text if x != " "]
    text = [x for x in text if x != ""]
    for x in text:
        if text.count(x) > 1:
            text.remove(x)
    text_joined = "\n".join(text)
    if len(text_joined) > 4096:
        parts = []
        parts_lens = []
        for t in text:
            parts_lens.append(len(t))
        k = 0
        for i in range(len(parts_lens)):
            if k + parts_lens[i] + 50 + len(last_mail["topic"]) < 3000:
                k += parts_lens[i]
            else:
                parts.append(i)
                k = 0
        msg = await bot.send_message(
            chat_id=my_channel_id,
            text=f"<b>{last_mail['topic']}</b>"
                 + "\n\n"
                 + "\n\n".join(text[0: parts[0]]),
        )
        for i in range(len(parts)):
            if i == len(parts) - 1:
                msg = await msg.answer(text="\n\n".join(text[parts[i]:]))
                break
            msg = await msg.answer(text="\n\n".join(text[parts[i]: parts[i + 1]]))
    else:
        await bot.send_message(
            chat_id=my_channel_id,
            text=f"<b>{last_mail['topic']}</b>" + "\n\n" + text_joined,
        )
    if last_mail["attachments"] != {}:
        if len(list(last_mail["attachments"].values())) == 1:
            filename = list(last_mail["attachments"].keys())[0]
            file = base64.urlsafe_b64decode(
                list(last_mail["attachments"].values())[0].encode("UTF-8")
            )
            file_obj = types.BufferedInputFile(file=file, filename=filename)
            await bot.send_document(chat_id=my_channel_id, document=file_obj)
        else:
            for filename, data in last_mail["attachments"].items():
                file = base64.urlsafe_b64decode(data.encode("UTF-8"))
                file_obj = types.BufferedInputFile(file=file, filename=filename)
                await bot.send_document(chat_id=my_channel_id, document=file_obj)
                time.sleep(1)


#
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
