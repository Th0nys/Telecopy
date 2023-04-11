import mysql.connector
from mysql.connector.errors import IntegrityError
import asyncio
import datetime
from typing import List
import request_func
from mysql.connector import Error

async def get_db_connection():
    conn = mysql.connector.connect(
            host='telecopy-database.c4lyn4ii6vsu.us-east-2.rds.amazonaws.com',
            user='admin',
            password='telesqlcopy',
            database='sys',
            port='3306'
        )
    return conn

async def get_user_count():
    conn = await get_db_connection()
    cursor = conn.cursor()
    
    count_query = "SELECT COUNT(*) FROM users_tb"
    cursor.execute(count_query)
    user_count = cursor.fetchone()
    
    cursor.close()
    conn.close()

    return user_count[0]

async def is_user_logged_in(user_id):
    conn = await get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT is_logged_in FROM users_tb WHERE chat_id= %s", (user_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return False
    
async def delete_user():
    conn = await get_db_connection()
    cursor = conn.cursor()
    comand = '''
        DELETE FROM users_tb
        WHERE phone IS NULL OR phone = ''
    '''
    cursor.execute(comand)
    conn.commit()
    conn.close()
    
async def delete_user_by_id(chat_id):
    conn = await get_db_connection()
    cursor = conn.cursor()
    comand = "DELETE FROM users_tb WHERE chat_id = %s"
    cursor.execute(comand, (chat_id,))
    conn.commit()
    conn.close()

async def addUser(conn, values):
    cursor = conn.cursor()
    comand = '''
        UPDATE users_tb
        SET phone = %s, subscriber = %s, is_logged_in = %s WHERE chat_id = %s
    '''
    try:
        print(values)
        cursor.execute(comand, values)
        conn.commit()
    except IntegrityError as e:
        # You can add more error handling here if needed
        if 'Duplicate entry' in str(e):
            return 'DUPLICATE_PHONE'
        raise e


async def add_user_mail(values):
    conn = await get_db_connection()
    cursor = conn.cursor()
    print(values)
    comand = f'INSERT INTO users_tb (chat_id, username, email, phone, subscriber) VALUES (%s, %s, %s, %s, %s)'
    values.append(None)  # Insere um valor NULL para o campo phone
    values.append(0)
    cursor.execute(comand, values)
    conn.commit()
    conn.close()


async def get_phone(chatid):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("SELECT phone FROM users_tb WHERE chat_id=%s", (chatid,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


async def get_user_from_chat_id(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username FROM users_tb WHERE chat_id=%s", (chat_id,))
    result = c.fetchone()
    return result[0] if result else None

async def get_phone_from_chat_id(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("SELECT phone FROM users_tb WHERE chat_id=%s", (chat_id,))
    result = c.fetchone()
    return result[0] if result else None


async def get_session_file(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("SELECT phone FROM users_tb WHERE chat_id=%s", (chat_id,))
    result = c.fetchone()
    conn.close()
    if result:
        phone = result[0]
        session = f'tel:{phone}.session'
        print(f"Sessão do usuario de chat({chat_id}) = {session}")
        return session


async def add_source_to_target(chat_id, source_id, destination_id):
    conn = await get_db_connection()
    c = conn.cursor()
    comand = 'INSERT INTO from_to (user_id, source_id, destination_id) VALUES (%s, %s, %s)'
    values = [chat_id, source_id, destination_id]
    c.execute(comand, values)
    conn.commit()
    conn.close()

async def remove_source_to_target(chat_id, source_id, destination_id):
    conn = await get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM from_to WHERE user_id = %s AND source_id = %s AND destination_id = %s", (chat_id, source_id, destination_id))
        record = c.fetchall()
        
        if record:
            c.execute("DELETE FROM from_to WHERE user_id = %s AND source_id = %s AND destination_id = %s", (chat_id, source_id, destination_id))
            conn.commit()
            print(f'DEBUG: removido do banco de dados do usuario {chat_id} o chat {source_id} do chat {destination_id}')
            return True
    finally:
        c.close()

    return False


async def remove_blacklist(user_id, chat_id, blacklisted):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM blacklist WHERE user_id = %s AND chat_id = %s AND blacklisted = %s", (user_id, chat_id, blacklisted))
    conn.commit()
    c.close()
    

async def remove_whitelist(user_id, chat_id, whitelisted):
    conn = await get_db_connection()
    c = conn.cursor()
    
    # Verifique se o registro existe antes de tentar removê-lo
    c.execute("SELECT * FROM whitelist WHERE user_id = %s AND chat_id = %s AND whitelisted = %s", (user_id, chat_id, whitelisted))
    record = c.fetchone()
    
    if record:
        c.execute("DELETE FROM whitelist WHERE user_id = %s AND chat_id = %s AND whitelisted = %s", (user_id, chat_id, whitelisted))
        conn.commit()
        c.close()
        return True
    else:
        c.close()
        return False

async def get_all_forwarding_pairs(user_id):
    conn = await get_db_connection()
    c1 = conn.cursor()
    c2 = conn.cursor()
    command1 = "SELECT source_id FROM from_to WHERE user_id = %s"
    c1.execute(command1, (user_id,))
    source_id = c1.fetchall()
  
    command2 = "SELECT destination_id FROM from_to WHERE user_id = %s"
    c2.execute(command2, (user_id,))
    destination_id = c2.fetchall()
    conn.close()
    return source_id, destination_id
  
      
async def get_source_and_destination_groups(chat_id):
    conn = await get_db_connection()
    lists = []
    c = conn.cursor()

    command = "SELECT source_id, destination_id FROM from_to WHERE user_id=%s"

    c.execute(command, (chat_id,))
    results = c.fetchall()

    source_groups = [result[0] for result in results]
    destination_groups = [result[1] for result in results]

    print(f'source_id = {source_groups}\ndestination_id = {destination_groups}')
    c.fetchall()
    lists.append(results[0][0])
    lists.append(results[0][1])
    
    conn.close()
    return lists


async def get_all_forwarding_pairs_dict( user_id):
    query = "SELECT source_id, destination_id FROM from_to WHERE user_id = %s"
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute(query, (user_id,))
    pairs = c.fetchall()
    conn.close()
    return pairs

async def phone_cadastrado(chat_id, numero):
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute("SELECT phone WHERE chat_id = %s", (chat_id,))
    phones = c.fetchone()
    for phone in phones:
        if phone == numero:
            return True
    return False

async def select_table():
    conn = await get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users_tb')
    result = c.fetchone()
    print(result)


async def activate_trial(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """UPDATE users_tb
                SET trial_allowed = FALSE, trial_start_time = NOW() + INTERVAL 1 DAY
                WHERE chat_id = %s"""
    c.execute(query, (user_id,))
    conn.commit()
    conn.close()
    return

async def is_trial_active(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """SELECT trial_start_time > NOW() AS is_trial_active
            FROM users_tb
            WHERE chat_id = %s;"""
    c.execute(query, (user_id,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        return False
    
async def check_trial(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """SELECT (NOW() - trial_start_time) <= INTERVAL '24 hours' AS is_trial_active
            FROM users_tb
            WHERE chat_id = %s;"""
    c.execute(query, (user_id,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        return False

    
async def get_trial_start_date(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """SELECT trial_start_time
            FROM users_tb
            WHERE chat_id = %s;"""
    c.execute(query, (user_id,))
    result = c.fetchone()
    
    if not result:
        return False
    else:
        print(result[0])
        return result[0]

    
async def check_if_pair_exists(user_id, source_id, destination_id):
    conn = await get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM from_to WHERE user_id = %s AND source_id=%s AND destination_id=%s', (user_id, source_id, destination_id,))
    result = cursor.fetchone()

    conn.close()

    return result is not None

async def user_exists(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = "SELECT COUNT(*) FROM users_tb WHERE chat_id = %s"
    c.execute(query, (chat_id,))
    result = c.fetchone()
    count = result[0]
    conn.close()

    return count > 0

async def can_trial(user_id):
    conn = await get_db_connection()
    c = conn.cursor()
    query = """SELECT trial_allowed
            FROM users_tb
            WHERE chat_id = %s;"""
    c.execute(query, (user_id,))
    result = c.fetchall()
    print(result[0][0])
    return result[0][0]

async def delete_row():
    conn = await get_db_connection()
    c = conn.cursor()
    chat_id = '1365614344'
    c.execute('DELETE FROM users_tb WHERE chat_id = %s', (chat_id,))
    conn.commit()

async def check_whitelist(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    command = "SELECT chat_id, whitelisted, changes FROM whitelist WHERE user_id = %s"
    c.execute(command, (chat_id,))
    result = c.fetchall()
    result_dict = {}
    for (chat_id, whitelisted, changes) in result:
        if chat_id not in result_dict:
            result_dict[chat_id] = []
        result_dict[chat_id].append({"whitelisted": whitelisted, "changes": changes})
    return result_dict


async def add_whitelist(user_id, chat_id, word1, word2):
    conn = await get_db_connection()
    c = conn.cursor()
    comand = 'INSERT INTO whitelist (user_id, chat_id, whitelisted, changes) VALUES (%s, %s, %s, %s)'
    values = [user_id, chat_id, word1, word2]
    c.execute(comand, values)
    conn.commit()
    conn.close()
    return


async def update_email(user_id: int, email: str):
    conn = await get_db_connection()
    try:
        cursor = await conn.cursor()
        await cursor.execute("UPDATE users_tb SET email = %s WHERE id = %s", (email, user_id))
        await conn.commit()
    finally:
        await cursor.close()
        await conn.close()


async def check_blacklist(chat_id):
    conn = await get_db_connection()
    c = conn.cursor()
    command = "SELECT chat_id, blacklisted FROM blacklist WHERE user_id = %s"
    c.execute(command, (chat_id,))
    result = c.fetchall()
  
    prohibited_words_dict = {}
    for source_id, prohibited_word in result:
        if source_id not in prohibited_words_dict:
            prohibited_words_dict[source_id] = []
        prohibited_words_dict[source_id].append(prohibited_word)
    return prohibited_words_dict
  
async def get_all_ids():
    conn = await get_db_connection()
    c = conn.cursor()
    command = "SELECT DISTINCT chat_id FROM users_tb"
    c.execute(command)
    result = c.fetchall()
    ids = []
    for i in range(len(result)):
        ids.append(result[i][0])
    return ids
  
async def add_blacklist(user_id, chat_id, blacklisted):
    conn = await get_db_connection()
    c = conn.cursor()
    comand = 'INSERT INTO blacklist (user_id, chat_id, blacklisted) VALUES (%s, %s, %s)'
    values = [user_id, chat_id, blacklisted]
    c.execute(comand, values)
    conn.commit()
    print(f'a palavra {blacklisted} foi adicionada ao banco de dados do usuario {user_id}')
    conn.close()
    return

async def is_user_subscriber(user_id):
    conn = await get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT subscriber, trial_start_time FROM users_tb WHERE chat_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        subscriber = row[0]
        trial_start_time = row[1]
        if subscriber:
            return True
        elif trial_start_time:
            now = datetime.datetime.now()
            trial_duration = now - trial_start_time
            return trial_duration < datetime.timedelta(days=1)
    return False

async def get_email(user_id):
    conn = await get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users_tb WHERE chat_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return None
    
async def get_emails_from_db() -> List[str]:
    conn = await get_db_connection()
    cursor = conn.cursor()
    
    email_query = "SELECT email FROM users_tb"
    cursor.execute(email_query)
    emails = cursor.fetchall()
    
    conn.close()

    return [email[0] for email in emails]

async def get_subscriber_count():
    emails = await get_emails_from_db()
    subscriber_count = 0

    for email in emails:
        is_subscriber = await request_func.is_user_subscriber_email(email)
        if is_subscriber:
            subscriber_count += 1

    return subscriber_count

async def main():
    trial = await can_trial('788283947')
    if not trial:
        print("pode nao em")
    elif trial:
        print("ta suave")
    
if __name__ == '__main__':
    asyncio.run(main())




