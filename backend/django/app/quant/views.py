from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from .forms import MT5LoginForm
from app.utils.api.mt5_client import create_mt5_client

@csrf_protect
def mt5_login_view(request):
    if request.method == 'POST':
        form = MT5LoginForm(request.POST)
        if form.is_valid():
            # Obtener credenciales del formulario
            login = form.cleaned_data['login']
            password = form.cleaned_data['password']
            server = form.cleaned_data['server']
            
            # Intentar login con API MT5
            client = create_mt5_client()
            result = client.login(login, password, server)
            
            if result['success']:
                # Guardar información en sesión Django
                request.session['mt5_authenticated'] = True
                request.session['mt5_token'] = client.token
                request.session['mt5_account_info'] = result['account_info']
                request.session['mt5_login'] = login
                request.session['mt5_server'] = server
                
                messages.success(request, 'Login exitoso en MetaTrader 5')
                return redirect('dashboard')
            else:
                messages.error(request, f"Error: {result['error']}")
    else:
        form = MT5LoginForm()
    
    return render(request, 'quant/mt5_login.html', {'form': form})

def mt5_logout_view(request):
    """Cerrar sesión MT5"""
    if request.session.get('mt5_authenticated'):
        # Cerrar sesión en API
        client = create_mt5_client()
        client.token = request.session.get('mt5_token')
        client.logout()
        
        # Limpiar sesión Django
        request.session.pop('mt5_authenticated', None)
        request.session.pop('mt5_token', None)
        request.session.pop('mt5_account_info', None)
        request.session.pop('mt5_login', None)
        request.session.pop('mt5_server', None)
        
        messages.success(request, 'Sesión cerrada correctamente')
    
    return redirect('mt5_login')

def dashboard_view(request):
    """Dashboard principal - requiere login MT5"""
    if not request.session.get('mt5_authenticated'):
        messages.warning(request, 'Debes iniciar sesión en MT5 primero')
        return redirect('mt5_login')
    
    # Crear cliente con token de sesión
    client = create_mt5_client()
    client.token = request.session.get('mt5_token')
    
    # Obtener datos
    positions = client.get_positions()
    account_info = request.session.get('mt5_account_info')
    
    context = {
        'account_info': account_info,
        'positions': positions,
    }
    
    return render(request, 'quant/dashboard.html', context)
