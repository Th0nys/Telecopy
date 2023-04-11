import aiogram
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import logging

logging.basicConfig(level=logging.INFO)

bot = Bot('6087028385:AAHRBTY2TvIM2yuhZkWOzZvVwwfQ9xwBiC4')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

chat_id = None

class GroupSelectForm(StatesGroup):
    source = State()  # O usuário deve digitar o grupo de origem
    destination = State()  # O usuário deve digitar o grupo de destino


async def select_from_to(message: types.Message):
    global chat_id
    chat_id = message.chat.id
    texto = "Para redirecionar as mensagens de um grupo para o outro, é necessário seguir dois passos:\n\nPrimeiro, enviar o grupo de onde virá as mensagens (chat_id do grupo/canal)\n\nSegundo, escolha o grupo de destino para o redirecionamento das mensagens (chat_id do grupo/canal)"
    await message.reply(f"{texto}")
    await GroupSelectForm.source.set()
    logging.info("Definiu o estado ButtonForm.source")


async def select_source_group(message: types.Message, state=GroupSelectForm.source):
    global chat_id
    print("entrou aqui nessa buceta de select_source_group")
    logging.info("Entrou na função select_source")
    texto = "Envie o id do grupo/canal de origem:"
    await message.reply(f"{texto}")
    async with state.proxy() as data:
        data['source_group'] = message.text
        source_group = data['source_group']
        source_group_name = await bot.get_chat(chat_id=source_group)
        await message.reply(f"Ok, o grupo de origem escolhido é: {source_group_name.title}\n\nAgora, envie o chat_id do grupo/canal de destino (exemplo: -1001234567890):")
    await GroupSelectForm.destination.set()


async def select_destination_group(message: types.Message, state=GroupSelectForm.destination):
    texto = "Envie o id do grupo/canal de destino:"
    await message.reply(f"{texto}")
    async with state.proxy() as data:
        data['destination_group'] = message.text
        destination_group = data['destination_group']
        destination_group_name = await bot.get_chat(chat_id=destination_group)
        texto2 = "A partir de agora, todas as mensagens que chegarem no grupo de origem serão repassadas ao grupo de destino."
        await message.reply(f"Ok, o grupo de destino escolhido é: {destination_group_name.title}\n\nAs mensagens do grupo {data['source_group']} serão redirecionadas para o grupo {data['destination_group']}.\n\n{texto2}")
        # Salvar os grupos de origem e destino no banco de dados
        import dbConnection
        values = [str(chat_id), data['source_id'], data['destination']]
        await dbConnection.add_source_to_target(data['source_id'], data['destination_group'])
    await state.finish()
