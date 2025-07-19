import logging
import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonSpam


API_ID = ""
API_HASH = ""
LOG_FILE = 'report_app.log'

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def report_message(client, chat, msg_id, reason):
    try:
        await client(ReportRequest(
            peer=chat,
            id=[msg_id],
            reason=InputReportReasonSpam(),
            message=""
        ))
        print(f"Жалоба отправлена: {msg_id}")
        return True
    except Exception as e:
        print(f"Ошибка при отправке жалобы: {e}")
        return False

async def process_message_link(link):
    try:
        parts = link.split('/')
        channel_username = parts[-2]
        message_id = int(parts[-1].split('?')[0])
        return channel_username, message_id
    except (IndexError, ValueError):
        return None, None

async def handle_demolition(link):
    success_count = 0
    failure_count = 0
    invalid_sessions = []

    complaints_per_account = 1
    channel_username, message_id = await process_message_link(link)
    if not channel_username:
        return success_count, failure_count

    async def process_session(session_file):
        nonlocal success_count, failure_count
        client = TelegramClient(f"sessions/{session_file}", API_ID, API_HASH)
        try:
            await client.connect()
            channel = await client.get_entity(channel_username)

            for _ in range(complaints_per_account):
                if await report_message(client, channel, message_id, "spam"):
                    success_count += 1
                else:
                    failure_count += 1
        except Exception as e:
            print(f"Ошибка с аккаунтом {session_file}: {e}")
            failure_count += 1
            if "The user has been deleted/deactivated" in str(e):
                invalid_sessions.append(session_file)
        finally:
            try:
                await client.disconnect()
            except Exception as e:
                print(f"Ошибка при отключении клиента {session_file}: {e}")

    tasks = []
    for session_file in os.listdir("sessions"):
        if session_file.endswith(".session"):
            tasks.append(process_session(session_file))

    await asyncio.gather(*tasks)

    return success_count, failure_count

async def botnet_report(link):
    if 'https://t.me/' not in link:
        print('Пожалуйста, укажите ссылку на сообщение в формате https://t.me/channel_name/message_id')
        return

    channel_username, message_id = await process_message_link(link)
    if not channel_username:
        print('Некорректная ссылка. Пожалуйста, введите ссылку на сообщение в формате https://t.me/channel_name/message_id')
        return

    print('Отправка жалоб началась...')
    successful_reports, failed_reports = await handle_demolition(link)

    print(f'Все жалобы отправлены\nУспешно: {successful_reports}\nНеуспешно: {failed_reports}')

async def main():
    print("Ваш личный ботнетик от всемогущего Хаски")
    link = input("Введите ссылку на сообщение для репорта: ")
    await botnet_report(link)

if __name__ == "__main__":
    asyncio.run(main())
