import aiogram, re, shlex
from aiogram import Bot, Dispatcher, types 
import asyncio
from dbConnection import *
from aiogram.dispatcher import Dispatcher, filters
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from keyboards import create_channels_keyboard
from request_func import *
import keyboards, textos
import user_related
from global_vars import clients

token = '6016165902:AAFI7MNk04SSykOHsqwB_0MT_wRuddTwNaw'
bot = Bot(token)


admins = ['5902107016', '788283947', '1365614344', '1697126178']


async def show(message: types.Message):
    chat_id = message.from_user.id
    if str(chat_id) in admins:
        message_text = message.text.replace("“", "\"").replace("”", "\"")
        args = shlex.split(message_text)[1:]
        print(f"output: {args}")
        action, thing = args
        if action == 'mostrar' and thing == 'usuarios':
            usuarios = await get_user_count()
            await message.reply(
                        f"Número de usuários conectados: {usuarios}",reply_markup=await keyboards.back_menu())
            return
        if action == 'mostrar' and thing == 'assinantes':
            assinantes = await get_subscriber_count()
            await message.reply(
                        f"Número de assinantes conectados: {assinantes}",reply_markup=await keyboards.back_menu())
            return
    else:
        await message.reply(
                        f"Não passarás.",reply_markup=await keyboards.back_menu())
        return


async def remove_someone(message: types.Message):
    chat_id = message.from_user.id
    if chat_id in admins:
        message_text = message.text.replace("“", "\"").replace("”", "\"")
        args = shlex.split(message_text)[1:]
        print(f"output: {args}")
        
