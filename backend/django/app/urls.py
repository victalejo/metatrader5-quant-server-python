# backend/django/app/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.shortcuts import render

def home_view(request):
    return HttpResponse("""
    <html>
    <head><title>MT5 Trading System</title></head>
    <body style="font-family: Arial; margin: 40px;">
        <h1>🚀 MT5 Trading System</h1>
        <h2>✅ Django está funcionando!</h2>
        
        <h3>📋 Enlaces disponibles:</h3>
        <ul>
            <li><a href="/admin/">Django Admin</a></li>
            <li><a href="/v1/">API REST (nexus)</a></li>
            <li><strong>Próximamente:</strong> Login MT5</li>
        </ul>
        
        <h3>🔗 Otros servicios:</h3>
        <ul>
            <li><a href="http://mt5-api.localhost">MT5 API</a></li>
            <li><a href="http://mt5-vnc.localhost">MT5 VNC</a></li>
            <li><a href="http://traefik.localhost">Traefik Dashboard</a></li>
            <li><a href="http://grafana.localhost:3001">Grafana</a></li>
        </ul>
        
        <p><strong>Sprint 1.1:</strong> Sistema de autenticación en desarrollo</p>
    </body>
    </html>
    """)

urlpatterns = [
    path('', home_view, name='home'),  # ✅ Nueva línea
    path('admin/', admin.site.urls),
    path('v1/', include('app.nexus.urls')),
]