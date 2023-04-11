from telethon import TelegramClient
import asyncio

lock = asyncio.Lock()

admins = ['5902107016', '788283947', '1365614344', '1697126178']
emails_free = ['Joaopedroribeiroempresa@gmail.com', 'dak4rtt@gmail.com']

clients = {}

api_id = '23023328'
api_hash = '111f1ddc23d1b313112f7c7a0612b3d1'

async def disconnect_session(session_file):
    async with lock:
        temp_client = TelegramClient(session_file, api_id, api_hash)
        if temp_client.is_connected:
            await temp_client.disconnect()
        else:
            print(f'{session_file} is not connected')
