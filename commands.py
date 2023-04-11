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
from global_vars import clients, admins, emails_free

token = '6016165902:AAFI7MNk04SSykOHsqwB_0MT_wRuddTwNaw'
bot = Bot(token)


async def set_groups_command(message: types.Message):
    chat_id = message.from_user.id
    is_subscriber = await is_user_subscriber_api(chat_id)
    trial = await is_trial_active(chat_id)
    message_text = message.text.replace("“", "\"").replace("”", "\"")
    args = shlex.split(message_text)[1:]
    print(f"output: {args}")
    email = await get_email(chat_id)
    if chat_id in admins:
        admin = chat_id
    if is_subscriber or trial or admin or email in emails_free:
        if len(args) != 3:
            texto = textos.set_groups()
            await message.reply(texto,reply_markup=await keyboards.back_menu())
            return
    
        action, source_group_id, destination_group_id = args
    
        # Verifique se os IDs são números válidos
        try:
            int(source_group_id)
            int(destination_group_id)
        except ValueError:
            await message.reply("Os chat_ids devem ser números. Por favor, tente novamente.",reply_markup=await keyboards.back_menu())
            return
  
        if action == 'add':
            client = clients.get(str(chat_id))
            if await user_related.is_valid_chat_id(client, int(source_group_id)) and await user_related.is_valid_chat_id(client, int(destination_group_id)):
                import dbConnection
                chat_id = message.from_user.id
                exists = await dbConnection.check_if_pair_exists(str(chat_id), str(source_group_id), str(destination_group_id))
                if not exists:
                    await add_source_to_target(str(chat_id), str(source_group_id), str(destination_group_id))
            
                    await message.reply(
                        f"Grupo de origem definido como: {source_group_id}\nGrupo de destino definido como: {destination_group_id}\n\nEm no máximo 1 minuto, todas as mensagens que chegarem ao grupo de origem serão repassadas ao grupo de destino!",reply_markup=await keyboards.back_menu())
                    return
                else:
                    await message.reply(
                        f"Esse repasse ao grupo {destination_group_id} já está cadastrado.",reply_markup=await keyboards.back_menu())
                    return
            else:
                await message.reply("Um ou ambos os IDs de chat fornecidos são inválidos. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
            return

        elif action == 'remove':
            client = clients.get(str(chat_id))
            if await user_related.is_valid_chat_id(client, int(source_group_id)) and await user_related.is_valid_chat_id(client, int(destination_group_id)):
                chat_id = message.from_user.id
                await remove_source_to_target(str(chat_id), str(source_group_id), str(destination_group_id))
                await message.reply(
                f"Grupo de origem {source_group_id} removido do grupo de destino {destination_group_id} com sucesso!",reply_markup=await keyboards.back_menu())
                return
            else:
                await message.reply("Um ou ambos os IDs de chat fornecidos são inválidos. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
            return
                                                                               
    else:
        await message.reply("Acesso negado.\n\nApenas assinantes podem usar esse comando.",reply_markup=await keyboards.back_menu())     
        return 


async def set_blacklist_command(message: types.Message):
    user_id = message.from_user.id
    client = clients.get(str(user_id))
    is_subscriber = await is_user_subscriber_api(user_id)
    trial = await is_trial_active(user_id)
    message_text = message.text.replace("“", "\"").replace("”", "\"")
    args = shlex.split(message_text)[1:]
    print(f"shlex.split output: {args}")
    email = await get_email(chat_id)
    if chat_id in admins:
        admin = chat_id
    if is_subscriber or trial or admin or email in emails_free:
        if len(args) != 3:
            texto = textos.set_blacklist()
            await message.reply(texto,reply_markup=await keyboards.back_menu())
            return

        action, group_id, word = args

        # Verifique se os IDs são números válidos
        try:
            int(group_id)
        except ValueError:
            await message.reply("O chat_id deve ser número. Por favor, tente novamente.",reply_markup=await keyboards.back_menu())
            return

        if action == 'add':
            if await user_related.is_valid_chat_id(client, int(group_id)):
                import dbConnection
                chat_id = message.from_user.id
                await dbConnection.add_blacklist(str(chat_id), str(group_id), str(word))
            
                await message.reply(f"Palavra cadastrada no banco.\n\nAgora sempre que uma frase contendo a sentença '{word}' chegar no grupo de id {group_id}, será bloqueada!",reply_markup=await keyboards.back_menu())
            else:
                await message.reply("O id do grupo fornecido é inválido. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
                return

        elif action == 'remove':
            # Verifique se o chat_id é válido antes de remover do banco de dados
            if await user_related.is_valid_chat_id(client, int(group_id)):
                import dbConnection
                chat_id = message.from_user.id
                await dbConnection.remove_blacklist(str(chat_id), str(group_id), str(word))
                await message.reply(f"A palavra '{word}' foi removida da lista negra do grupo {group_id}.",reply_markup=await keyboards.back_menu())
            else:
                await message.reply("O id do grupo fornecido é inválido. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
                return
    
    else:
        await message.reply("Acesso negado.\n\nApenas assinantes podem usar esse comando.",reply_markup=await keyboards.back_menu()) 


async def set_whitelist_command(message: types.Message):
    chat_id = message.from_user.id
    client = clients.get(str(chat_id))
    is_subscriber = await is_user_subscriber_api(chat_id)
    trial = await is_trial_active(chat_id)
    message_text = message.text.replace("“", "\"").replace("”", "\"")
    args = shlex.split(message_text)[1:]
    print(f"shlex.split output: {args}")
    email = await get_email(chat_id)
    if chat_id in admins:
        admin = chat_id
    if is_subscriber or trial or admin or email in emails_free:
        if len(args) != 4:
            texto = textos.transform()
            await message.reply(texto,reply_markup=await keyboards.back_menu())
            return

        action, group_id, word1, word2 = args
        print(args)

        # Verifique se os IDs são números válidos
        try:
            int(group_id)
        except ValueError:
            await message.reply("O chat_id deve ser número. Por favor, tente novamente.",reply_markup=await keyboards.back_menu())
            return

        if action == 'add':
            # Verifique se o chat_id é válido antes de adicionar ao banco de dados
            if await user_related.is_valid_chat_id(client, int(group_id)):
                import dbConnection
                chat_id = message.from_user.id
                await dbConnection.add_whitelist(str(chat_id), str(group_id), str(word1), str(word2))

                await message.reply(
                    f"Palavra cadastrada no banco.\n\nAgora sempre que uma frase contendo sentença '{word1}' chegar no grupo de id {group_id}, será transformada para '{word2}'!",reply_markup=await keyboards.back_menu())
                return
            else:
                await message.reply("O id do grupo fornecido é inválido. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
                return

        
        elif action == 'remove':
            if await user_related.is_valid_chat_id(client, int(group_id)):
                import dbConnection
                chat_id = message.from_user.id
                removed = await dbConnection.remove_whitelist(str(chat_id), str(group_id), str(word1))
                if removed:
                    await message.reply(f"A palavra '{word1}' foi removida da lista branca do grupo {group_id}.",reply_markup=await keyboards.back_menu())
                else:
                    await message.reply(f"A palavra '{word1}' não foi encontrada na lista branca do grupo {group_id}.",reply_markup=await keyboards.back_menu())
            else:
                await message.reply("O id do grupo fornecido é inválido. Por favor, verifique e tente novamente.", reply_markup=await keyboards.back_menu())
                return
    
    else:
        await message.reply("Acesso negado.\n\nApenas assinantes podem usar esse comando.",reply_markup=await keyboards.back_menu())


async def add_email_command(message: types.Message):
    message_text = message.text.replace("“", "\"").replace("”", "\"")
    args = shlex.split(message_text)[1:]
    chat_id = message.from_user.id
    
    if len(args) != 2:
        await message.reply(text=textos.email(),reply_markup=await keyboards.back_menu())
        return

    action, email = args
    print(args)
    print(action)
    print(email)
    
    if action == 'add':
        import dbConnection
        conn = await dbConnection.get_db_connection()
        c = conn.cursor()
        query = "UPDATE users_tb SET email = %s WHERE chat_id = %s"
        c.execute(query, (email, chat_id,))
        conn.commit()
        conn.close()
        await message.reply(text='Obrigado, agora seu email está cadastrado em nossos bancos.\n\nCaso você não seja assinante, basta adquirir nosso produto com o mesmo email cadastrado no Telecopy! :)',reply_markup=await keyboards.back_menu())
        
    elif action == 'troca':
        import dbConnection
        conn = await dbConnection.get_db_connection()
        c = conn.cursor()
        query = "UPDATE users_tb SET email = %s WHERE chat_id = %s"
        c.execute(query, (email, chat_id,))
        conn.commit()
        conn.close()
        await message.reply(text=f'Certo, agora seu email foi mudado para {email}.\n\n Caso você não seja assinante, basta adquirir nosso produto com o mesmo email cadastrado no Telecopy! 😁',reply_markup=await keyboards.back_menu())

    elif action == 'remove':
        import dbConnection
        conn = await dbConnection.get_db_connection()
        c = conn.cursor()
        query = "UPDATE users_tb SET email = NULL WHERE chat_id = %s"
        c.execute(query, (chat_id,))
        conn.commit()
        conn.close()
        await message.reply(text='Sinto muito pelo incoveniente, agora seu email não está mais cadastrado em nossos bancos. :(',reply_markup=await keyboards.back_menu())
    
    elif action == 'verifica':
        user_id = message.from_user.id
        is_subscriber = await is_user_subscriber_email(email)
        if is_subscriber:
            await message.reply(text=f"Seu email: '{email}' consta como assinante em nossos bancos, obrigado por assinar nosso produto!\n\nFaça bom proveito 😁",reply_markup=await keyboards.back_menu())
            return
        await message.reply(text=f"Seu email: '{email}' não consta como assinante em nossos bancos, obrigado por assinar nosso produto!\n\nCaso ache que isso é um engano, entre em contato com nosso suporte usando /suporte", reply_markup=await keyboards.back_menu())
