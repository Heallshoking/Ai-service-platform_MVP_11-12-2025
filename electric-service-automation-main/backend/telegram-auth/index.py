'''
Business: Telegram authentication for users with role selection (client/executor)
Args: event with httpMethod, body containing initData from Telegram WebApp
Returns: JWT token and user info with selected role
'''

import json
import hmac
import hashlib
import os
from typing import Dict, Any, Optional
from urllib.parse import parse_qs
from dataclasses import dataclass
import time

@dataclass
class TelegramUser:
    id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    photo_url: Optional[str]

def verify_telegram_auth(init_data: str, bot_token: str) -> Optional[TelegramUser]:
    try:
        params = parse_qs(init_data)
        
        data_check_string_parts = []
        for key in sorted(params.keys()):
            if key != 'hash':
                value = params[key][0]
                data_check_string_parts.append(f'{key}={value}')
        
        data_check_string = '\n'.join(data_check_string_parts)
        
        secret_key = hmac.new(
            'WebAppData'.encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        received_hash = params.get('hash', [''])[0]
        
        if calculated_hash != received_hash:
            return None
        
        user_data = json.loads(params.get('user', ['{}'])[0])
        
        return TelegramUser(
            id=user_data.get('id'),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name'),
            username=user_data.get('username'),
            photo_url=user_data.get('photo_url')
        )
    except Exception:
        return None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Auth-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        init_data = body_data.get('initData', '')
        role = body_data.get('role', 'client')
        
        if not init_data:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'initData is required'})
            }
        
        if role not in ['client', 'executor']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid role. Must be client or executor'})
            }
        
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        if not bot_token:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Bot token not configured'})
            }
        
        telegram_user = verify_telegram_auth(init_data, bot_token)
        
        if not telegram_user:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid Telegram authentication'})
            }
        
        user_info = {
            'uid': f'tg_{telegram_user.id}',
            'telegram_id': telegram_user.id,
            'name': f'{telegram_user.first_name} {telegram_user.last_name or ""}'.strip(),
            'username': telegram_user.username,
            'photo_url': telegram_user.photo_url,
            'role': role,
            'created_at': int(time.time())
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'success': True,
                'user': user_info,
                'token': f'tg_token_{telegram_user.id}_{int(time.time())}'
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
