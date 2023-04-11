import requests
import json
import asyncio
import dbConnection

async def is_user_subscriber_api(user_id):
    email = await dbConnection.get_email(user_id)
    if email:
        url = f"https://ellodev.com/telecopy/?emailCliente={email}"
        response = requests.get(url)
        if response.status_code == 200:
            try:
                subscriber_data = response.json()
            except ValueError as e:
                print(f"Erro ao decodificar JSON: {e}")
                return False
            
            if subscriber_data and subscriber_data.get('subscription_status_enum') == 'Ativa':
                return True

    
    return False

async def is_user_subscriber_email(email):
    if email:
        url = f"https://ellodev.com/telecopy/?emailCliente={email}"
        response = requests.get(url)
        print(response)
        data = response.json()
        print(data)
        if response.status_code == 200:
            try:
                subscriber_data = response.json()
            except ValueError as e:
                print(f"Erro ao decodificar JSON: {e}")
                return False
            
            if subscriber_data and subscriber_data.get('subscription_status_enum') == 'Ativa':
                return True
    
    return False
