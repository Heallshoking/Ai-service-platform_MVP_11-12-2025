'''
Business: API для работы с заявками (CRUD операции)
Args: event - dict с httpMethod, body, queryStringParameters
      context - object с request_id
Returns: HTTP response с данными заявок или результатом операции

Endpoints:
- GET / - получить все заявки (с фильтрами)
- GET /?id=ORD-123 - получить заявку по ID
- POST / - создать новую заявку
- PUT /?id=ORD-123 - обновить заявку
- DELETE /?id=ORD-123 - удалить заявку
'''

import json
import os
import psycopg2
import psycopg2.extras
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class OrderItem(BaseModel):
    name: str
    price: float
    quantity: int
    category: Optional[str] = None
    description: Optional[str] = None

class CreateOrderRequest(BaseModel):
    order_uid: str = Field(..., min_length=1)
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    address: str
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    items: List[OrderItem]
    total_price: float
    total_switches: int = 0
    total_outlets: int = 0
    total_points: int = 0
    estimated_cable: int = 0
    estimated_frames: int = 0
    status: str = 'new'
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    client_notes: Optional[str] = None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    query_params = event.get('queryStringParameters', {}) or {}
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'DATABASE_URL not configured'}),
            'isBase64Encoded': False
        }
    
    try:
        conn = psycopg2.connect(database_url)
        
        if method == 'GET':
            result = handle_get(conn, query_params)
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            result = handle_post(conn, body_data)
        elif method == 'PUT':
            body_data = json.loads(event.get('body', '{}'))
            result = handle_put(conn, query_params, body_data)
        elif method == 'DELETE':
            result = handle_delete(conn, query_params)
        else:
            result = {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Method not allowed'}),
                'isBase64Encoded': False
            }
        
        conn.close()
        return result
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Server error: {str(e)}'}),
            'isBase64Encoded': False
        }

def handle_get(conn, query_params: Dict[str, Any]) -> Dict[str, Any]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    order_id = query_params.get('id')
    status = query_params.get('status')
    assigned_to = query_params.get('assigned_to')
    
    if order_id:
        cur.execute(
            "SELECT * FROM t_p78209571_electric_service_aut.orders WHERE order_uid = %s",
            (order_id,)
        )
        order = cur.fetchone()
        cur.close()
        
        if order:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(dict(order), default=str),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Order not found'}),
                'isBase64Encoded': False
            }
    
    query = "SELECT * FROM t_p78209571_electric_service_aut.orders WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    if assigned_to:
        query += " AND assigned_to = %s"
        params.append(assigned_to)
    
    query += " ORDER BY created_at DESC"
    
    cur.execute(query, params)
    orders = cur.fetchall()
    cur.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([dict(order) for order in orders], default=str),
        'isBase64Encoded': False
    }

def handle_post(conn, body_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        order_req = CreateOrderRequest(**body_data)
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'Validation error: {str(e)}'}),
            'isBase64Encoded': False
        }
    
    cur = conn.cursor()
    
    items_json = json.dumps([item.dict() for item in order_req.items])
    
    cur.execute("""
        INSERT INTO t_p78209571_electric_service_aut.orders (
            order_uid, customer_name, customer_phone, customer_email,
            address, scheduled_date, scheduled_time, items, total_price,
            total_switches, total_outlets, total_points, estimated_cable, estimated_frames,
            status, assigned_to, assigned_to_name, client_notes,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        ) RETURNING id
    """, (
        order_req.order_uid, order_req.customer_name, order_req.customer_phone, order_req.customer_email,
        order_req.address, order_req.scheduled_date, order_req.scheduled_time, items_json, order_req.total_price,
        order_req.total_switches, order_req.total_outlets, order_req.total_points, 
        order_req.estimated_cable, order_req.estimated_frames,
        order_req.status, order_req.assigned_to, order_req.assigned_to_name, order_req.client_notes
    ))
    
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'success': True, 'id': order_id, 'order_uid': order_req.order_uid}),
        'isBase64Encoded': False
    }

def handle_put(conn, query_params: Dict[str, Any], body_data: Dict[str, Any]) -> Dict[str, Any]:
    order_uid = query_params.get('id')
    if not order_uid:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Order ID required'}),
            'isBase64Encoded': False
        }
    
    cur = conn.cursor()
    
    set_parts = []
    params = []
    
    if 'status' in body_data:
        set_parts.append("status = %s")
        params.append(body_data['status'])
    
    if 'assigned_to' in body_data:
        set_parts.append("assigned_to = %s")
        params.append(body_data['assigned_to'])
    
    if 'assigned_to_name' in body_data:
        set_parts.append("assigned_to_name = %s")
        params.append(body_data['assigned_to_name'])
    
    if 'planfix_task_id' in body_data:
        set_parts.append("planfix_task_id = %s")
        params.append(body_data['planfix_task_id'])
    
    if not set_parts:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'No fields to update'}),
            'isBase64Encoded': False
        }
    
    set_parts.append("updated_at = NOW()")
    params.append(order_uid)
    
    query = f"UPDATE t_p78209571_electric_service_aut.orders SET {', '.join(set_parts)} WHERE order_uid = %s"
    
    cur.execute(query, params)
    rows_updated = cur.rowcount
    conn.commit()
    cur.close()
    
    if rows_updated > 0:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': True, 'updated': rows_updated}),
            'isBase64Encoded': False
        }
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Order not found'}),
            'isBase64Encoded': False
        }

def handle_delete(conn, query_params: Dict[str, Any]) -> Dict[str, Any]:
    order_uid = query_params.get('id')
    if not order_uid:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Order ID required'}),
            'isBase64Encoded': False
        }
    
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM t_p78209571_electric_service_aut.orders WHERE order_uid = %s",
        (order_uid,)
    )
    rows_deleted = cur.rowcount
    conn.commit()
    cur.close()
    
    if rows_deleted > 0:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': True, 'deleted': rows_deleted}),
            'isBase64Encoded': False
        }
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Order not found'}),
            'isBase64Encoded': False
        }
