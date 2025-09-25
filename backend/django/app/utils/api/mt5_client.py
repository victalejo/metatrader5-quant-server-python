import os
import requests
import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class MT5Client:
    """Cliente robusto para la API MT5 - SIN credenciales hardcodeadas"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.expires_at = None
        self.account_info = None
        
        # Configurar sesión HTTP
        self.session = requests.Session()
    
    def login(self, login: int, password: str, server: str) -> Dict:
        """
        Login con credenciales proporcionadas por el usuario
        Retorna información del login o error
        """
        try:
            url = f"{self.base_url}/login"
            data = {
                'login': int(login),
                'password': str(password),
                'server': str(server)
            }
            
            response = self.session.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result['token']
                self.expires_at = datetime.now() + timedelta(seconds=result['expires_in'])
                self.account_info = result['account_info']
                
                # Configurar headers para próximas requests
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                
                logger.info(f"Login exitoso para cuenta {login}")
                return {
                    'success': True,
                    'account_info': self.account_info,
                    'message': 'Login exitoso'
                }
            else:
                error_msg = response.json().get('error', 'Error desconocido')
                logger.error(f"Error en login: {response.status_code} - {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Excepción en login: {str(e)}")
            return {
                'success': False,
                'error': 'Error de conexión con la API'
            }
    
    def is_authenticated(self) -> bool:
        """Verifica si tenemos una sesión válida"""
        if not self.token or not self.expires_at:
            return False
        
        # Considerar expirado 5 minutos antes
        buffer_time = timedelta(minutes=5)
        return datetime.now() < (self.expires_at - buffer_time)
    
    def logout(self) -> bool:
        """Cierra sesión"""
        try:
            if self.token:
                url = f"{self.base_url}/logout"
                self.session.post(url, timeout=10)
            
            # Limpiar estado
            self.token = None
            self.expires_at = None
            self.account_info = None
            self.session.headers.pop('Authorization', None)
            
            return True
            
        except Exception as e:
            logger.error(f"Error en logout: {str(e)}")
            return False
    
    def get_positions(self, magic: Optional[int] = None) -> Optional[Dict]:
        """Obtener posiciones abiertas"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            params = {'magic': magic} if magic else {}
            response = self.session.get(f"{self.base_url}/get_positions", params=params, timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {str(e)}")
            return {'error': str(e)}
    
    def get_account_info(self) -> Optional[Dict]:
        """Obtener información de la cuenta"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            response = self.session.get(f"{self.base_url}/account_info", timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error obteniendo info cuenta: {str(e)}")
            return {'error': str(e)}
    
    def place_order(self, symbol: str, volume: float, order_type: str, **kwargs) -> Optional[Dict]:
        """Colocar una orden"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            data = {
                'symbol': symbol,
                'volume': volume,
                'type': order_type,
                **kwargs
            }
            response = self.session.post(f"{self.base_url}/order", json=data, timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error colocando orden: {str(e)}")
            return {'error': str(e)}
    
    def close_position(self, position_data: Dict) -> Optional[Dict]:
        """Cerrar una posición específica"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            data = {'position': position_data}
            response = self.session.post(f"{self.base_url}/close_position", json=data, timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error cerrando posición: {str(e)}")
            return {'error': str(e)}
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Obtener información de símbolo"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            response = self.session.get(f"{self.base_url}/symbol_info/{symbol}", timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error obteniendo info símbolo: {str(e)}")
            return {'error': str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str = 'M1', num_bars: int = 100) -> Optional[Dict]:
        """Obtener datos de mercado"""
        if not self.is_authenticated():
            return {'error': 'No autenticado'}
        
        try:
            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'num_bars': num_bars
            }
            response = self.session.get(f"{self.base_url}/fetch_data_pos", params=params, timeout=30)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error obteniendo datos mercado: {str(e)}")
            return {'error': str(e)}


# Función helper SIN credenciales por defecto
def create_mt5_client() -> MT5Client:
    """Crea un cliente MT5 usando solo la URL base"""
    base_url = os.getenv('MT5_API_URL', 'http://mt5:5001')
    return MT5Client(base_url)