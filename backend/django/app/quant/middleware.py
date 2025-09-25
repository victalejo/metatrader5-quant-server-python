from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class MT5AuthMiddleware:
    """Middleware para verificar autenticación MT5 en vistas protegidas"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Rutas protegidas que requieren login MT5
        self.protected_paths = [
            '/',  # dashboard
        ]
        # Rutas libres que no requieren autenticación
        self.free_paths = [
            '/login/',
            '/logout/',
            '/admin/',
            '/api/',
        ]

    def __call__(self, request):
        # Verificar si la ruta necesita protección
        path = request.path_info
        
        # Si es una ruta libre, continuar
        if any(path.startswith(free_path) for free_path in self.free_paths):
            response = self.get_response(request)
            return response
        
        # Si es una ruta protegida, verificar autenticación
        if any(path.startswith(protected_path) for protected_path in self.protected_paths):
            if not request.session.get('mt5_authenticated'):
                messages.warning(request, 'Debes iniciar sesión en MT5 primero')
                return redirect('mt5_login')
        
        response = self.get_response(request)
        return response