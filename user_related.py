import asyncio
import logging
import shutil
from telethon import TelegramClient, events
from global_vars import clients, admins, emails_free
import request_func
import dbConnection
import re
import datetime
import pytz
from dateutil import parser

logging.basicConfig(level=logging.INFO)

api_id = '23023328'
api_hash = '111f1ddc23d1b313112f7c7a0612b3d1'

db_lock = asyncio.Lock()
db_semaphore = asyncio.Semaphore(1)

message_id_mapping = {}

async def copy_session_file(session_path, new_session_path):
    shutil.copy2(session_path, new_session_path)
    
async def is_valid_chat_id(client, chat_id):
    return True

async def is_user_allowed(user_id):
    if user_id in admins:
        logging.info("é admin, tá suave")
        return True
    
    is_subscribed = await request_func.is_user_subscriber_api(user_id)
    if is_subscribed:
        logging.info("esse pagou, tá suave")
        return True
    
    email = await dbConnection.get_email(user_id)
    if email in emails_free:
        logging.info("alguem liberou esse email ein, tá suave")
        return True

    # Verifique o período de avaliação do usuário
    trial_start_str = await dbConnection.get_trial_start_date(user_id)
    trial_start = parser.parse(trial_start_str)  # Convertendo a string em datetime

    # Convertendo a data de início do período de teste para o fuso horário local
    local_timezone = pytz.timezone('America/Sao_Paulo')  # Substitua com o fuso horário desejado
    trial_start_local = trial_start.astimezone(local_timezone)

    trial_end = trial_start_local + datetime.timedelta(hours=24)
    now = datetime.datetime.now(local_timezone)
    now = now + datetime.timedelta(hours=27)

    if now < trial_end:
        logging.info("tá testando o telecopy")
        return True
    
    return False


async def get_chats_with_new_session(chat_id: int, session_file: str, max_chars_per_page: int = 1000):
    new_session_file = f'get_chats_{session_file}'
    await copy_session_file(session_file, new_session_file)
    chats = await get_chats(new_session_file, max_chars_per_page)
    await start_forwarding(chat_id, True)
    return chats

async def update_clients_dict(chat_id, client):
    clients[chat_id] = client

async def create_client_with_copied_session(session_path, new_session_path):
    print('copiando sessao...')
    await copy_session_file(session_path, new_session_path)
    print(f'sessao copiada para: {new_session_path}')
    
    return new_session_path

# função para conectar o cliente
async def connect_client(client):
    async with client:
        await client.start()
        await client.run_until_disconnected()
  
async def get_chats(user_id, max_chars_per_page=1000):
    print(clients)
    client = clients.get(str(user_id))

    # se o cliente não existe, cria um novo e armazena no dicionário
    chats = []
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group:
            chats.append({'id': dialog.id, 'name': dialog.title})

    pages = []
    page = f'\nNome do grupo/canal  |  ID do grupo/canal:\n\n'
    for chat in chats:
        msg = f"{chat['name']}  |  {chat['id']}\n"
        if len(page) + len(msg) <= max_chars_per_page:
            page += msg
        else:
            pages.append(page)
            page = msg

    pages.append(page)
    return pages

async def reconnect_client(forwarding_client, user_id):
    if forwarding_client is None:
        session = await dbConnection.get_session_file(user_id)
        forwarding_client = TelegramClient(f'{session}', api_id, api_hash)
        await forwarding_client.connect()
        await update_clients_dict(str(user_id), forwarding_client)
    while True:
        if not forwarding_client.is_connected():
            try:
                async with db_lock:
                    await forwarding_client.connect()
                break
            except Exception as e:
                logging.warning(f"Error connecting: {e}")
                await asyncio.sleep(5)
        else:
            break

async def start_forwarding_client(forwarding_client, user_id):
  
    if forwarding_client is None:
        session = await dbConnection.get_session_file(user_id)
        forwarding_client = TelegramClient(f'{session}', api_id, api_hash)
        await forwarding_client.connect()
        await update_clients_dict(str(user_id), forwarding_client)
      
    source_destination_pairs = await dbConnection.get_all_forwarding_pairs_dict(user_id)
    prohibited_words_dict = await dbConnection.check_blacklist(user_id)
    whitelist_dict = await dbConnection.check_whitelist(user_id)
  
    @forwarding_client.on(events.NewMessage(chats=[int(pair[0]) for pair in source_destination_pairs]))
    async def handler(event, user_id=user_id):
        source_destination_pairs = await dbConnection.get_all_forwarding_pairs_dict(user_id)
        prohibited_words_dict = await dbConnection.check_blacklist(user_id)
        whitelist_dict = await dbConnection.check_whitelist(user_id)
        grupo = event.message.chat.title
        date = event.message.date
        logging.info(f'\nchegou mensagem no {grupo}, pelo usuario {user_id}, as {date}\ncom o conteudo: {event.message.message}\n')

        allowed = await is_user_allowed(user_id)
        

        # Verificar se o usuário é assinante ou está no período de teste
        if allowed:
            for source_id, destination_id in source_destination_pairs:
                if event.chat_id == int(source_id):
                    prohibited_words = prohibited_words_dict.get(str(event.chat_id), [])
                    chat_whitelist = whitelist_dict.get(str(event.chat_id), [])

                    if not any(word.lower() in event.message.text.lower() for word in prohibited_words):
                        # Verifica se há uma palavra whitelist e faz a substituição
                        for item in chat_whitelist:
                            whitelisted_word = item.get("whitelisted")
                            if whitelisted_word:
                                # Verifica se a palavra whitelisted está na mensagem (levando em consideração os emojis)
                                pattern = re.compile(re.escape(whitelisted_word))
                                if pattern.search(event.message.text):
                                    # Substitui a palavra whitelisted pela palavra "changes" (levando em consideração os emojis)
                                    replacement_word = item.get("changes")
                                    event.message.text = pattern.sub(replacement_word, event.message.text)

                        sent_message = await forwarding_client.send_message(int(destination_id), event.message)
                        message_id_mapping[event.message.id] = sent_message.id
                        logging.info(f'mensagem enviada ao destino, pelo usuario {user_id}, as {date}\ncom o conteudo: {event.message.message}\n')
                    else:
                        logging.info("mensagem não enviada, conteúdo proibido")
        else:
            logging.info("mensagem não enviada, usuário não é assinante")

                    
    @forwarding_client.on(events.MessageDeleted())
    async def delete_handler(event, user_id=user_id):
        source_destination_pairs = await dbConnection.get_all_forwarding_pairs_dict(user_id)

        for source_id, destination_id in source_destination_pairs:
            if event.chat_id == int(source_id):
                original_message_id = event.deleted_id
                if original_message_id in message_id_mapping:
                    destination_message_id = message_id_mapping[original_message_id]
                    await forwarding_client.delete_messages(int(destination_id), destination_message_id)
                    # Verifique se a chave existe antes de excluí-la
                    if original_message_id in message_id_mapping:
                        del message_id_mapping[original_message_id]
                    logging.info(f"Mensagem {original_message_id} apagada no canal de origem, apagando a mensagem {destination_message_id} no canal de destino.")


    while True:
        await reconnect_client(forwarding_client, user_id)

        if not forwarding_client.is_connected():
            await forwarding_client.start()

        try:
            await forwarding_client.run_until_disconnected()
        except Exception as e:
            logging.warning(f"Client disconnected: {e}")
            await asyncio.sleep(5)


async def start_forwarding(user_id, reconnect):
    session = await dbConnection.get_session_file(user_id)
    forwarding_client = clients.get(str(user_id))
    if reconnect:
        asyncio.create_task(start_forwarding_client(forwarding_client, user_id))
    else:
        logging.info("start_forwarding entry")
        if not forwarding_client:
            # Adiciona o novo cliente Telegram no dicionário clients se ainda não existir
            client = TelegramClient(session, api_id, api_hash)
            await client.start()
            clients[str(user_id)] = client
            forwarding_client = client
        asyncio.create_task(start_forwarding_client(forwarding_client, user_id))
    return
