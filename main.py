import aiogram, logging, asyncio
from telethon import TelegramClient
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import os, glob
from global_vars import clients, admins
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import CallbackQuery
import datetime
from dateutil import parser
import pytz

from pathlib import Path
import textos, commands, login_form, user_related
from from_to import select_destination_group, select_source_group, GroupSelectForm
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text

from login_form import phone_session_exists
from dbConnection import *
import dbConnection
import keyboards
from aiogram.types import CallbackQuery
from commands import *
import admin

logging.basicConfig(level=logging.INFO)
lock = asyncio.Lock()   

api_id = '23023328'
api_hash = '111f1ddc23d1b313112f7c7a0612b3d1'

phone = '+5582993162373'
token = '6016165902:AAFI7MNk04SSykOHsqwB_0MT_wRuddTwNaw'
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

from aiogram.dispatcher.middlewares import BaseMiddleware
import dbConnection

class Pilha:
    def __init__(self):
        self.itens = []  # Inicializa a lista que armazenará os itens da pilha

    def is_empty(self):
        # Retorna True se a pilha estiver vazia, False caso contrário
        return not bool(self.itens)

    def push(self, item):
        # Adiciona um item ao topo da pilha
        self.itens.append(item)

    def pop(self):
        # Remove e retorna o item do topo da pilha, se não estiver vazia
        if not self.is_empty():
            return self.itens.pop()

    def peek(self):
        # Retorna o item do topo da pilha sem removê-lo, se a pilha não estiver vazia
        if not self.is_empty():
            return self.itens[-1]

    def size(self):
        # Retorna o número de itens na pilha
        return len(self.itens)


async def disconnect_session(session_file):
    async with lock:
        temp_client = TelegramClient(session_file, api_id, api_hash)
        if temp_client.is_connected:
            await temp_client.disconnect()
        else:
            print(f'{session_file} is not connected')
    
processing_login = False
logins = Pilha()
pages = []
planos_keyboard = None
pag_keyboard = None
inline_keyboard = None


async def is_user_registered(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """SELECT EXISTS(SELECT 1 FROM users_tb WHERE chat_id = %s);"""
    c.execute(query, (user_id,))
    result = c.fetchone()
    return result[0]

async def is_trial_period_valid(user_id):
    if user_id in admins:
        return True 
    subscriber = await is_user_subscriber_api(user_id)

    if not subscriber:
        is_registered = await is_user_registered(user_id)
        if not is_registered:
            return True  # Permitir acesso a usuários não registrados

        trial_start_str = await get_trial_start_date(user_id)

        if not trial_start_str:
            return True

        trial_start = parser.parse(trial_start_str)  # Convertendo a string em datetime

        # Convertendo a data de início do período de teste para o fuso horário local
        local_timezone = pytz.timezone('America/Sao_Paulo')  # Substitua com o fuso horário desejado
        trial_start_local = trial_start.astimezone(local_timezone)

        print(f"data de inicio: {trial_start_local}")
        trial_end = trial_start_local + datetime.timedelta(hours=24)
        now = datetime.datetime.now(local_timezone)
        now = now + datetime.timedelta(hours=27)
        print(f"agora: {now}")
        print(f"final: {trial_end}")

        if now < trial_end:
            return True
        return False

    return True


# Função para enviar uma mensagem informando que o período de teste acabou
async def send_trial_period_expired_message(chat_id):
    message = "Seu período de teste acabou. Por favor, adquira o Telecopy para continuar usando nossos serviços."
    await bot.send_message(chat_id, message, reply_markup=await keyboards.planos())

async def teclados():
    planos_keyboard = await keyboards.planos_keyboard()
    pag_keyboard = await keyboards.pag_keyboard()
    inline_keyboard = await keyboards.menu_keyboard()

async def schedule_deletion(interval_minutes):
    while True:
        await dbConnection.delete_user()
        await asyncio.sleep(interval_minutes * 60)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    inline_keyboard_logged = await keyboards.logged_keyboard(user_id)
    trial_valid = await is_trial_period_valid(user_id)

    if not trial_valid:
        await send_trial_period_expired_message(message.chat.id)
        return
    else:
        if await is_user_logged_in(user_id):
            await bot.send_message(message.chat.id, f'{textos.logged()}',
                                reply_markup=inline_keyboard_logged)
            return

        await bot.send_message(message.chat.id, f'{textos.ola()}', reply_markup=await keyboards.menu_keyboard())

@dp.callback_query_handler(lambda query: query.data in 'info')
async def process_callback_button1(callback_query: CallbackQuery):
    # obter o valor de retorno do botão
    button = callback_query.data
    
    if button == 'info':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=f"{textos.info()}", reply_markup=await keyboards.back_menu())

@dp.callback_query_handler(lambda c: c.data == 'planos')
async def handle_opcao1(callback_query: CallbackQuery):
    buttons = callback_query.data
    texto = textos.planos()
    if buttons == 'planos':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,text=texto, reply_markup=await keyboards.pagamento())
     
@dp.callback_query_handler(lambda c: c.data == 'voltar')
async def handle_opcao1(callback_query: CallbackQuery):
     buttons = callback_query.data
     
     if buttons == 'voltar':
         await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=f"{textos.ola()}", reply_markup=inline_keyboard)

async def create_pagination_keyboard(current_page: int, total_pages: int):
    keyboard = aiogram.types.InlineKeyboardMarkup(row_width=2)

    if current_page > 0:
        keyboard.insert(aiogram.types.InlineKeyboardButton("⬅️ Anterior", callback_data=f"page:{current_page - 1}"))

    if current_page < total_pages - 1:
        keyboard.insert(aiogram.types.InlineKeyboardButton("Próximo ➡️", callback_data=f"page:{current_page + 1}"))

    return keyboard

    
async def send_paginated_message(chat_id: int, page: int, pages, max_chars_per_page: int = 1000):
    keyboard = await create_pagination_keyboard(page, len(pages))
    content = pages[page]
    while len(content) > max_chars_per_page:
        await bot.send_message(chat_id, content[:max_chars_per_page], reply_markup=keyboard)
        content = content[max_chars_per_page:]
    await bot.send_message(chat_id, content, reply_markup=keyboard)    

@dp.callback_query_handler(lambda c: c.data == 'view_channels')
async def handle_view_channels(callback_query: CallbackQuery):
    buttons = callback_query.data
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    
    if buttons == 'view_channels':
        chat_id = callback_query.message.chat.id
        session = str(await get_session_file(chat_id))
        
        max_chars_per_page = 1000
        global pages
        
               
        # Obtém os chats do client
        channels = await user_related.get_chats(chat_id, max_chars_per_page)
        pages = channels
        
        await send_paginated_message(chat_id, 0, pages, max_chars_per_page)


@dp.callback_query_handler(lambda c: c.data.startswith("channel:"))
async def on_channel_click(callback_query: CallbackQuery):
    channel_id = int(callback_query.data.split(":")[1])
    await bot.send_message(callback_query.message.chat.id, f"Você selecionou o canal com ID: {channel_id}")
    await bot.answer_callback_query(callback_query.id)
  
    
@dp.callback_query_handler(lambda c: c.data.startswith("page:"))
async def on_page_click(callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    keyboard = await create_pagination_keyboard(page, len(pages))
    content = pages[page]

    await bot.edit_message_text(content, callback_query.message.chat.id, callback_query.message.message_id, reply_markup=keyboard)
    await bot.answer_callback_query(callback_query.id)
    

@dp.callback_query_handler(lambda c: c.data in ["conta"])
async def conta(callback_query: aiogram.types.CallbackQuery):
    chat_id = callback_query.from_user.id
    buttons = callback_query.data
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    
    texto = "Nesse menu você encontra tudo relacionado a sua conta no Telecopy! Fique a vontade:"
    keyboard = await keyboards.conta()
  
    if buttons == 'conta':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=texto,reply_markup=keyboard)
  
  
@dp.message_handler(commands=['email']) # função para o comando 'set_groups' que é explicado ao clicar no botao de selecionar canais:
async def set_email(message: types.Message):
    chat_id = message.from_user.id
    
    await commands.add_email_command(message)
    
    
@dp.message_handler(commands=['admin']) # função para o comando 'set_groups' que é explicado ao clicar no botao de selecionar canais:
async def adminz(message: types.Message):
    chat_id = message.from_user.id
    await admin.show(message)


@dp.callback_query_handler(lambda c: c.data in ["email", "view_email"])
async def on_button_click(callback_query: aiogram.types.CallbackQuery):
    chat_id = callback_query.from_user.id
    buttons = callback_query.data
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    keyboard = await keyboards.back_menu()
    email = await dbConnection.get_email(chat_id)
    texto2 = f"Seu email cadastrado no banco de dados é: {email}\n\n"
    texto3 = textos.email()
    if buttons == 'email':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=textos.email(),reply_markup=keyboard)
    if buttons == 'view_email':
        if email:
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=texto2+texto3,reply_markup=await keyboards.back_conta())
        else:
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Você ainda não cadastrou seu email.',reply_markup=await keyboards.back_conta())

@dp.message_handler(commands=['delete']) # função para o comando 'repassar'
async def delete_user(message: types.Message):
    chat_id = message.from_user.id
    await dbConnection.delete_user_by_id(chat_id)
    phone = await dbConnection.get_phone_from_chat_id(chat_id)
    if phone:
        session_filename = Path(f'tel:{phone}.session')
        if session_filename.exists():
            session_filename.unlink()
    await message.reply('Dados apagados.')


@dp.message_handler(commands=['repassar']) # função para o comando 'repassar'
async def set_groups(message: types.Message):
    chat_id = message.from_user.id
    user_id = message.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(message.chat.id)
        return
    await commands.set_groups_command(message)
    client = clients.get(str(chat_id))
    print(f"DEBUG: client ao repassar = {client}")
    await user_related.start_forwarding_client(client, chat_id)


@dp.callback_query_handler(lambda c: c.data in ["set_groups", "view_repass"])
async def on_button_click(callback_query: aiogram.types.CallbackQuery):
    texto = textos.set_groups()
    chat_id = callback_query.from_user.id
    buttons = callback_query.data
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    texto2 = await dbConnection.get_all_forwarding_pairs_dict(chat_id)

    if buttons == 'set_groups':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=texto,reply_markup=await keyboards.back_menu())
    if buttons == 'view_repass':
        if texto2:
            output = ""
            for source_id, destination_id in texto2:
                output += f"{source_id} 👉 {destination_id}\n\n"

            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f'Seus repasses:\n\n{output}',reply_markup=await keyboards.back_conta())
        else:
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Não há nenhum grupo cadastrado para o repasse ainda!',reply_markup=await keyboards.back_conta())
    
    
@dp.message_handler(commands=['blacklist']) # função para o comando 'set_groups' que é explicado ao clicar no botao de selecionar canais:
async def set_command(message: types.Message):
    chat_id = message.from_user.id
    user_id = message.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(message.chat.id)
        return
    await commands.set_blacklist_command(message)
  

@dp.message_handler(commands=['transformar']) # função para o comando 'set_groups' que é explicado ao clicar no botao de selecionar canais:
async def set_transform(message: types.Message):
    chat_id = message.from_user.id
    user_id = message.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(message.chat.id)
        return
    await commands.set_whitelist_command(message)

@dp.callback_query_handler(lambda c: c.data in ["blacklist", "view_blacklist"])
async def on_button_click(callback_query: aiogram.types.CallbackQuery):
    chat_id = callback_query.from_user.id
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    texto1 = textos.set_blacklist()
    texto2 = await dbConnection.check_blacklist(chat_id)
    buttons = callback_query.data
    

    if buttons == 'blacklist':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=texto1,reply_markup=await keyboards.back_menu())
    if buttons == 'view_blacklist':
        if texto2:
            output = ""
            for group_id, words in texto2.items():
                for word in words:
                    output += f"No grupo '{group_id}' está proibida a palavra '{word}'\n\n"
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f'Sua blacklist:\n\n{output}',reply_markup=await keyboards.back_conta())
        else:
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Não há nenhuma palavra cadastrada na blacklist ainda!',reply_markup=await keyboards.back_conta())
        

@dp.callback_query_handler(lambda c: c.data in ["whitelist", "view_transform"])
async def on_button_click(callback_query: aiogram.types.CallbackQuery):
    texto = textos.transform()
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    chat_id = callback_query.from_user.id
    texto2 = await dbConnection.check_whitelist(chat_id)
    buttons = callback_query.data

    if buttons == 'whitelist':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=texto,reply_markup=await keyboards.back_menu())
    if buttons == 'view_transform':
        if texto2:
            output = ""
            for group_id, transformations in texto2.items():
                for transformation in transformations:
                    whitelisted = transformation['whitelisted']
                    changes = transformation['changes']
                    output += f"No grupo '{group_id}', a palavra '{whitelisted}' será transformada em '{changes}'\n\n"
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f'Suas transformações:\n\n{output}',reply_markup=await keyboards.back_conta())
        else:
            await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text='Não há nenhuma palavra cadastrada para ser transformada ainda!',reply_markup=await keyboards.back_conta())


MAX_SIMULTANEOUS_LOGINS = 8  # Ajuste este valor conforme necessário
semaphore = asyncio.Semaphore(MAX_SIMULTANEOUS_LOGINS)

    
async def process_login_queue(message):
    global processing_login
    tasks = []  # Lista para armazenar tarefas assíncronas
    while not logins.is_empty():
        processing_login = True
        chat_id = logins.pop()
        
        async with semaphore:  # Adquire o Semaphore
            task = asyncio.create_task(login_form.start_login(message, chat_id))
            tasks.append(task)  # Adiciona a tarefa à lista
        
    # Aguarda todas as tarefas na lista serem concluídas
    await asyncio.gather(*tasks)
    processing_login = False
    
    
@dp.callback_query_handler(lambda c: c.data in ["login", "teste"])
async def on_button_click(callback_query: CallbackQuery):
    # Mapeia callback_data às funções correspondentes
    data = callback_query.data
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message = callback_query.message
    print(f"\ndados da mensagem = {message}\n")

    if data == "login":
        logins.push(chat_id)  # Adicione o chat_id à pilha de logins
        await bot.send_message(chat_id, "Vamos começar a processar seu login.\n\nIsso pode levar até 2 minutos.")
        if not processing_login:
            await process_login_queue(message)
    elif data == "teste":
        logins.push(chat_id)  # Adicione o chat_id à pilha de logins
        await bot.send_message(chat_id, "Para usufruir de TODAS as ferramentes de forma GRATUITA, é necessário conectar-se primeiro!\n\nVamos começar a efetuar seu cadastro...")
        if not processing_login:
            await process_login_queue(message)
            
            
@dp.callback_query_handler(lambda c: c.data in ['back'])
async def handle_opcao3(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    inline_keyboard_logged = await keyboards.logged_keyboard(user_id)
    buttons = callback_query.data
    user_id = callback_query.from_user.id
    trial_valid = await is_trial_period_valid(user_id)
    

    if not trial_valid:
        await send_trial_period_expired_message(callback_query.message.chat.id)
        return
    
    if buttons == 'back':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, text=f'{textos.logged()}', reply_markup=inline_keyboard_logged)       

dp.register_message_handler(login_form.handle_email, state=login_form.MyForm.email)
dp.register_message_handler(login_form.get_phone, state=login_form.MyForm.phone)
dp.register_message_handler(login_form.get_code, state=login_form.MyForm.code)
dp.register_message_handler(login_form.get_pass, state=login_form.MyForm.two_step_pass)


async def get_users_with_expired_trial():
    conn = await get_db_connection()
    c = conn.cursor()

    query = """SELECT chat_id, trial_start_time FROM users_tb;"""
    c.execute(query)
    users = c.fetchall()

    expired_users = []
    local_timezone = pytz.timezone('America/Sao_Paulo')

    for user in users:
        user_id, trial_start_str = user
        
        # Verifique se trial_start_str não é None antes de analisá-lo
        if trial_start_str is not None:
            trial_start = parser.parse(trial_start_str)
            trial_start_local = trial_start.astimezone(local_timezone)
            trial_end = trial_start_local + datetime.timedelta(hours=24)
            now = datetime.datetime.now(local_timezone)
            now = now + datetime.timedelta(hours=27)

            if now > trial_end:
                expired_users.append(user_id)

    return expired_users


async def notify_expired_trials():
    expired_users = await get_users_with_expired_trial()
    telefones = []
    telstr = ''
    for id in expired_users:
        numero = await dbConnection.get_phone_from_chat_id(id)
        nome = await dbConnection.get_user_from_chat_id(id)
        telstr = telstr + f'\n{nome} = https://wa.me/{numero}'
    if telefones:
        expired_users_str = ', '.join(str(user_id) for user_id in expired_users)
        message = f"Os seguintes usuários tiveram o período de teste expirado: {telefones}"
        await bot.send_message(chat_id=-1001682567457, text=message)
    else:
        message = "Nenhum usuário teve o período de teste expirado no momento."
        await bot.send_message(chat_id=-1001682567457, text=message)
      
async def check_expired_trials_periodically():
    while True:
        await notify_expired_trials()
        await asyncio.sleep(3600)  # Verificar a cada hora (3600 segundos)
        
async def main():
    await teclados()

    polling_task = asyncio.create_task(dp.start_polling())
    check_expired_trials_task = asyncio.create_task(check_expired_trials_periodically())

    diretorio = os.getcwd()
    arquivos = glob.glob(diretorio + '/*.session')

    if arquivos:
        ids = await dbConnection.get_all_ids()
        tasks_forwarding = []

        for user_id in ids:
            phone = await dbConnection.get_phone(user_id)
            if phone:
                tasks_forwarding.append(asyncio.create_task(user_related.start_forwarding(user_id, True)))
            else:
                print(f"Telefone não encontrado para o usuário {user_id}. Pulando start_forwarding.")

        dp.middleware.setup(LoggingMiddleware())

        # Execute todas as tarefas simultaneamente
        await asyncio.gather(polling_task, check_expired_trials_task, *tasks_forwarding)
    else:
        dp.middleware.setup(LoggingMiddleware())

        # Execute as tarefas de polling e verificação de trials simultaneamente
        await asyncio.gather(polling_task, check_expired_trials_task)


if __name__ == '__main__':
    asyncio.run(main())
