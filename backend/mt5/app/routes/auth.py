import os
import secrets
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
import MetaTrader5 as mt5
from functools import wraps
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Configuración de sesiones
SESSIONS = {}
SESSION_TIMEOUT = 30 * 60  # 30 minutos

def require_auth(f):
    """Middleware de autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Buscar token en headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Token malformado'}), 401
        
        if not token:
            return jsonify({'error': 'Token requerido'}), 401
        
        try:
            # Verificar token JWT
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            session_id = data['session_id']
            
            # Verificar sesión activa
            if session_id not in SESSIONS:
                return jsonify({'error': 'Sesión expirada'}), 401
            
            session = SESSIONS[session_id]
            
            # Verificar timeout
            if datetime.now() > session['expires_at']:
                del SESSIONS[session_id]
                return jsonify({'error': 'Sesión expirada'}), 401
            
            # Renovar sesión
            SESSIONS[session_id]['expires_at'] = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'parameters': [
        {
            'name': 'credentials',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'login': {'type': 'integer', 'description': 'Login MT5'},
                    'password': {'type': 'string', 'description': 'Password MT5'},
                    'server': {'type': 'string', 'description': 'Servidor MT5'}
                },
                'required': ['login', 'password', 'server']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login exitoso',
            'schema': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string'},
                    'expires_in': {'type': 'integer'},
                    'account_info': {'type': 'object'}
                }
            }
        },
        401: {'description': 'Credenciales inválidas'},
        500: {'description': 'Error interno del servidor'}
    }
})
def login():
    """
    Autenticación en MetaTrader 5
    ---
    description: Inicia sesión en MT5 y devuelve un token de acceso.
    """
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['login', 'password', 'server']):
            return jsonify({'error': 'Login, password y server son requeridos'}), 400
        
        # Intentar login en MT5
        authorized = mt5.login(
            login=int(data['login']),
            password=str(data['password']),
            server=str(data['server'])
        )
        
        if not authorized:
            error_code = mt5.last_error()
            logger.error(f"Error de login MT5: {error_code}")
            return jsonify({'error': 'Credenciales inválidas o error de conexión'}), 401
        
        # Obtener info de la cuenta
        account_info = mt5.account_info()
        if account_info is None:
            return jsonify({'error': 'Error obteniendo información de cuenta'}), 500
        
        # Crear sesión
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
        
        SESSIONS[session_id] = {
            'login': data['login'],
            'server': data['server'],
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'account_info': account_info._asdict()
        }
        
        # Generar token JWT
        token_payload = {
            'session_id': session_id,
            'login': data['login'],
            'exp': expires_at
        }
        
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'expires_in': SESSION_TIMEOUT,
            'account_info': account_info._asdict()
        })
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
@swag_from({
    'tags': ['Authentication'],
    'security': [{'ApiKeyAuth': []}],
    'responses': {
        200: {'description': 'Logout exitoso'},
        401: {'description': 'Token inválido'}
    }
})
def logout():
    """
    Cerrar Sesión
    ---
    description: Cierra la sesión actual y desconecta de MT5.
    """
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        session_id = data['session_id']
        
        # Eliminar sesión
        if session_id in SESSIONS:
            del SESSIONS[session_id]
        
        # Desconectar de MT5
        mt5.shutdown()
        
        return jsonify({'message': 'Logout exitoso'})
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/session', methods=['GET'])
@require_auth
@swag_from({
    'tags': ['Authentication'],
    'security': [{'ApiKeyAuth': []}],
    'responses': {
        200: {
            'description': 'Información de sesión',
            'schema': {
                'type': 'object',
                'properties': {
                    'session_id': {'type': 'string'},
                    'login': {'type': 'integer'},
                    'server': {'type': 'string'},
                    'expires_at': {'type': 'string'},
                    'account_info': {'type': 'object'}
                }
            }
        },
        401: {'description': 'Token inválido'}
    }
})
def session_info():
    """
    Información de Sesión
    ---
    description: Obtiene información de la sesión actual.
    """
    try:
        token = request.headers.get('Authorization').split(" ")[1]
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        session_id = data['session_id']
        
        session = SESSIONS[session_id]
        
        return jsonify({
            'session_id': session_id,
            'login': session['login'],
            'server': session['server'],
            'expires_at': session['expires_at'].isoformat(),
            'account_info': session['account_info']
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo sesión: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500