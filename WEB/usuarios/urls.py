from .views import admin_crear_usuario  # <--- Agregá este import arriba
from django.urls import path
from .views import (
    dashboard_view,
    custom_login_view,
    register_view,
    logout_view,
    ver_solicitudes_alquiler,
    ver_solicitudes_visita
)

# Espacio de nombres para evitar conflictos de URLs
app_name = 'usuarios'

urlpatterns = [
    # Raíz: Muestra el Dashboard "Paloma" si está logueado
    path('', dashboard_view, name='dashboard'),

    # Autenticación Personalizada
    path('login/', custom_login_view, name='custom-login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

    # Vistas Específicas para Propietarios
    path('solicitudes-alquiler/', ver_solicitudes_alquiler,
         name='solicitudes-alquiler'),
    path('solicitudes-visita/', ver_solicitudes_visita, name='solicitudes-visita'),
]


urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('login/', custom_login_view, name='custom-login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('solicitudes-alquiler/', ver_solicitudes_alquiler,
         name='solicitudes-alquiler'),
    path('solicitudes-visita/', ver_solicitudes_visita, name='solicitudes-visita'),

    # AGREGÁ ESTA LÍNEA AQUÍ:
    path('admin/crear-usuario/', admin_crear_usuario, name='admin-crear-usuario'),
]
