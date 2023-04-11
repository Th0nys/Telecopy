
import aiogram, asyncio
from typing import Dict, List, Union
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from request_func import is_user_subscriber_api
from dbConnection import *
from global_vars import admins

async def back_conta():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()
    inline_keyboard.add(aiogram.types.InlineKeyboardButton('🔙 VOLTAR', callback_data='conta'))
    return inline_keyboard

async def back_menu():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()
    inline_keyboard.add(aiogram.types.InlineKeyboardButton('🔙 VOLTAR AO MENU', callback_data='back'))
    return inline_keyboard

async def usar_ferramenta():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()
    inline_keyboard.add(aiogram.types.InlineKeyboardButton('COMEÇAR A USAR A FERRAMENTA 🔜', callback_data='back'))
    return inline_keyboard

async def back_menu_button():
    return aiogram.types.InlineKeyboardButton('🔙 VOLTAR AO MENU', callback_data='back')

async def conta():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()
    row1 = [aiogram.types.InlineKeyboardButton('VER EMAIL', callback_data='view_email'),
           aiogram.types.InlineKeyboardButton('VER GRUPOS REPASSADOS', callback_data='view_repass')]
    row2 = [aiogram.types.InlineKeyboardButton('VER BLACKLIST', callback_data='view_blacklist'),
           aiogram.types.InlineKeyboardButton('VER TRANSFORMAR', callback_data='view_transform')]

    inline_keyboard.add(*row1)
    inline_keyboard.add(*row2)
    inline_keyboard.add(await back_menu_button())
  
    return inline_keyboard

async def escolher_from_to():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()

    row1 = [aiogram.types.InlineKeyboardButton('ESCOLHER FONTE', callback_data='add_source')]
    row2 = [aiogram.types.InlineKeyboardButton('ESCOLHER DESTINO', callback_data='add_destination')]

    inline_keyboard.row(*row1)
    inline_keyboard.row(*row2)
    inline_keyboard.add(await back_menu())

    return inline_keyboard

async def menu_keyboard():
    inline_keyboard = aiogram.types.InlineKeyboardMarkup()
    
    row1 = [aiogram.types.InlineKeyboardButton('🌐 CONECTAR', callback_data='login'),
            aiogram.types.InlineKeyboardButton('💸 ASSINAR AGORA', callback_data='planos')]
    row2 = [aiogram.types.InlineKeyboardButton('🕑 TESTAR AGORA (24H)', callback_data='teste')]
    
    inline_keyboard.row(*row1)
    inline_keyboard.row(*row2)
    
    return inline_keyboard

async def pag_keyboard():
    pag_keyboard = aiogram.types.InlineKeyboardMarkup()
    
    row6 =  [aiogram.types.InlineKeyboardButton('❖ PIX', callback_data='pix')]
    row7 =  [aiogram.types.InlineKeyboardButton('💳 Cartão de Crédito', callback_data='card')]
    
    pag_keyboard.row(*row6)
    pag_keyboard.row(*row7)
    pag_keyboard.add(await back_menu())
    
    return pag_keyboard


async def planos():
    keyboard = InlineKeyboardMarkup()

    comprar_plano_button = InlineKeyboardButton(text='💰 COMPRAR PLANO',
                                                url="https://go.perfectpay.com.br/PPU38CLQJEL",
                                                callback_data='assinar')
    suporte_button = InlineKeyboardButton('SUPORTE',
                                          url='https://t.me/Telecopysuporte')
    keyboard.add(suporte_button, comprar_plano_button)

    return keyboard

async def planos_keyboard():
    planos_keyboard = aiogram.types.InlineKeyboardMarkup()
    
    comprar_plano_button = aiogram.types.InlineKeyboardButton(text='💰 COMPRAR PLANO', url="https://go.perfectpay.com.br/PPU38CLQJEL", callback_data='assinar')
    
    planos_keyboard.row(comprar_plano_button)
    planos_keyboard.add(await back_menu())
    
    return planos_keyboard


async def logged_keyboard(user_id):
    inline_keyboard_logged = aiogram.types.InlineKeyboardMarkup()
    is_subscriber = await is_user_subscriber_api(user_id)
    email = await get_email(user_id)
    chat_url = "https://t.me/Telecopysuporte"
    url_afiliado = "https://app.perfectpay.com.br/afilie/PPPB4ECT"
    row5 = None

    row1 = [aiogram.types.InlineKeyboardButton('VER CHATS', callback_data='view_channels'),
            aiogram.types.InlineKeyboardButton('CONTA', callback_data='conta')]
    row2 = [aiogram.types.InlineKeyboardButton('REPASSE DE MENSAGENS', callback_data='set_groups')]
    row3 = [aiogram.types.InlineKeyboardButton('BLACKLIST', callback_data='blacklist'),
            aiogram.types.InlineKeyboardButton('TRANSFORMAR MENSAGENS', callback_data='whitelist')]
    
    if email:
        if is_subscriber:
            row4 = [aiogram.types.InlineKeyboardButton('SUPORTE', url=chat_url)]
            row5 = [aiogram.types.InlineKeyboardButton('SEJA UM AFILIADO', url=url_afiliado)]
        else:
            in_trial = await is_trial_active(user_id)
            row4 = [aiogram.types.InlineKeyboardButton('💸 ASSINAR AGORA', callback_data='planos'),
                    aiogram.types.InlineKeyboardButton('SUPORTE', url=chat_url) if in_trial else None]
            row5 = [aiogram.types.InlineKeyboardButton('SUPORTE', url=chat_url)] if not in_trial else None
    else:
        row1[1] = aiogram.types.InlineKeyboardButton('CADASTRAR EMAIL', callback_data='email')
        row4 = [aiogram.types.InlineKeyboardButton('💸 ASSINAR AGORA', callback_data='planos')]

    inline_keyboard_logged.row(*row1)
    inline_keyboard_logged.row(*row2)
    inline_keyboard_logged.row(*row3)
    if row4:
        inline_keyboard_logged.row(*filter(None, row4))
    if row5:
        inline_keyboard_logged.row(*row5)

    return inline_keyboard_logged




async def info():
    keyboard = back_menu()    
    return keyboard

async def create_pagination_keyboard(current_page: int, total_pages: int):
    keyboard = aiogram.types.InlineKeyboardMarkup(row_width=2)

    if current_page > 0:
        keyboard.insert(aiogram.types.InlineKeyboardButton("⬅️ Anterior", callback_data=f"page:{current_page - 1}"))

    if current_page < total_pages - 1:
        keyboard.insert(aiogram.types.InlineKeyboardButton("Próximo ➡️", callback_data=f"page:{current_page + 1}"))
    
    return keyboard

async def create_channels_keyboard(channels: List[Dict[str, Union[str, int]]]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    for channel in channels:
        title = channel["title"]
        channel_id = channel["id"]
        button = InlineKeyboardButton(text=title, callback_data=f"select_channel_{channel_id}")
        keyboard.add(button)
    keyboard.add(await back_menu())
    return keyboard


async def parse_channels_from_pages(pages):
    channels = []

    for page in pages:
        lines = page.split('\n')[2:]  # Ignorar as duas primeiras linhas (cabeçalho)
        for line in lines:
            if not line:
                continue
            title, channel_id = line.rsplit(' ', 1)
            channels.append({"title": title, "id": int(channel_id)})

    return channels

async def pagamento():
    inline_pay = aiogram.types.InlineKeyboardMarkup()
    
    row1 = [aiogram.types.InlineKeyboardButton('ADQUIRIR PLANO', url='https://go.perfectpay.com.br/PPU38CLQJEL')]
    inline_pay.row(*row1)
    
    return inline_pay
    
