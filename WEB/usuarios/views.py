import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model
from django import forms

# ==============================================================================
# FORMULARIO EXCLUSIVO PARA ADMIN (Permite los 4 roles)
# ==============================================================================


class AdminUserCreationForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre de usuario',
        max_length=100,
        widget=forms.TextInput(
            attrs={'placeholder': 'Ej: nuevo_admin', 'class': 'vTextField'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(
            attrs={'placeholder': 'correo@ejemplo.com', 'class': 'vTextField'})
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': '2777-XXXX', 'class': 'vTextField'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Mínimo 6 caracteres', 'class': 'vTextField'}),
        min_length=6
    )

    # Incluye 'administrador' a diferencia del registro público
    ROL_CHOICES = [
        ('propietario', 'Propietario'),
        ('inquilino', 'Inquilino'),
        ('visitante', 'Visitante'),
        ('administrador', 'Administrador'),
    ]
    rol = forms.ChoiceField(label='Rol del usuario', choices=ROL_CHOICES)


# ==============================================================================
# BACKEND DE AUTENTICACIÓN PERSONALIZADO (El Puente Robusto)
# ==============================================================================
class ApiUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()

        # Intento A: Buscar como usuario normal de Django
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        # Intento B: Buscar DIRECTAMENTE en la tabla 'usuarios' de la API
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, email, password, rol FROM usuarios WHERE email = %s OR nombre = %s",
                [username, username]
            )
            row = cursor.fetchone()

        if row:
            user_id, nombre, email, hashed_pw, rol_db = row

            # Verificar contraseña
            is_valid = False
            try:
                from lib.pwd import verify_password
                is_valid = verify_password(password, hashed_pw)
            except ImportError:
                from django.contrib.auth.hashers import check_password
                is_valid = check_password(password, hashed_pw)

            if is_valid:
                # Crear objeto usuario virtual
                user_obj = User(id=user_id, username=nombre, email=email)

                # Guardar rol en minúsculas para el template
                user_obj.rol = rol_db.lower()

                # Asignar permisos AL VUELO
                if user_obj.rol in ['administrador', 'admin', 'propietario']:
                    user_obj.is_staff = True
                    if user_obj.rol in ['administrador', 'admin']:
                        user_obj.is_superuser = True

                return user_obj

        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre, email, rol FROM usuarios WHERE id = %s", [user_id])
                row = cursor.fetchone()

            if row:
                user_obj = User(id=row[0], username=row[1], email=row[2])
                # Guardar rol aquí también
                user_obj.rol = row[3].lower()

                if user_obj.rol in ['administrador', 'admin', 'propietario']:
                    user_obj.is_staff = True
                return user_obj
            return None


# ==============================================================================
# VISTAS DE AUTENTICACIÓN Y DASHBOARD
# ==============================================================================

def register_view(request):
    """Registro PÚBLICO: Solo permite Propietario, Inquilino y Visitante"""
    if request.method == 'POST':
        rol_seleccionado = request.POST.get('rol', 'visitante')

        # SEGURIDAD: Bloquear intento de registrarse como admin desde web pública
        ROLES_PERMITIDOS = ['propietario', 'inquilino', 'visitante']
        if rol_seleccionado not in ROLES_PERMITIDOS:
            messages.error(request, "Rol no válido para registro público.")
            return redirect('usuarios:register')

        # Limpiar teléfono (quitar guiones) para la API
        telefono_limpio = request.POST.get('telefono', '').replace('-', '')

        # Payload corregido: 'nombre' en vez de 'username'
        payload = {
            'nombre': request.POST.get('username'),
            'email': request.POST.get('email'),
            'telefono': telefono_limpio,
            'password': request.POST.get('password'),
            'rol': rol_seleccionado
        }

        try:
            response = requests.post(
                f"{settings.API_BASE_URL}/usuarios/register",
                json=payload,
                timeout=5
            )

            if response.status_code == 201:
                messages.success(
                    request, '¡Cuenta creada exitosamente! Ya podés iniciar sesión.')
                return redirect('usuarios:custom-login')
            else:
                errors = response.json().get('detail', 'Error desconocido')
                if isinstance(errors, list):
                    first_error = errors[0] if errors else {}
                    msg = first_error.get('msg', str(first_error))
                    loc = first_error.get('loc', [])
                    field = loc[-1] if len(loc) > 0 else 'campo'
                    errors = f"Error en '{field}': {msg}"
                messages.error(request, f"Error al registrar: {errors}")

        except requests.exceptions.ConnectionError:
            messages.error(request, 'No se pudo conectar con la API.')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')

    return render(request, 'usuarios/register.html')


def custom_login_view(request):
    """Login personalizado que consume la API y redirige al Dashboard"""
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')

    if request.method == 'POST':
        email_or_user = request.POST.get(
            'email') or request.POST.get('username')
        password = request.POST.get('password')
        payload = {"username": email_or_user, "password": password}

        try:
            response = requests.post(
                f"{settings.API_BASE_URL}/usuarios/login", data=payload, timeout=5)
            if response.status_code == 200:
                request.session['jwt_token'] = response.json().get(
                    'access_token')
                user = ApiUserBackend().authenticate(
                    request, username=email_or_user, password=password)

                if user:
                    from django.contrib.auth import login
                    login(request, user, backend='usuarios.views.ApiUserBackend')
                    return redirect('usuarios:dashboard')
                else:
                    messages.error(
                        request, "Error sincronizando sesión local.")
            else:
                messages.error(
                    request, "Credenciales inválidas o usuario inactivo")
        except Exception as e:
            messages.error(request, f"Error de conexión: {str(e)}")

    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    """Cierra sesión en Django y limpia el token JWT"""
    from django.contrib.auth import logout
    logout(request)
    if 'jwt_token' in request.session:
        del request.session['jwt_token']
    return redirect('usuarios:custom-login')


@login_required
def dashboard_view(request):
    """Muestra el panel principal con diseño idéntico a la app móvil"""
    return render(request, 'usuarios/dashboard.html')


@login_required
def ver_solicitudes_alquiler(request):
    token = request.session.get('jwt_token')
    if not token:
        return render(request, 'usuarios/error_auth.html', {'msg': 'Sesión expirada'})
    try:
        resp = requests.get(f"{settings.API_BASE_URL}/solicitudes-alquiler/propietario",
                            headers={"Authorization": f"Bearer {token}"}, timeout=5)
        solicitudes = resp.json() if resp.status_code == 200 else []
    except:
        solicitudes = []
    return render(request, 'usuarios/solicitudes_alquiler.html', {'solicitudes': solicitudes})


@login_required
def ver_solicitudes_visita(request):
    token = request.session.get('jwt_token')
    if not token:
        return render(request, 'usuarios/error_auth.html', {'msg': 'Sesión expirada'})
    try:
        resp = requests.get(f"{settings.API_BASE_URL}/solicitudes-visita/propietario",
                            headers={"Authorization": f"Bearer {token}"}, timeout=5)
        solicitudes = resp.json() if resp.status_code == 200 else []
    except:
        solicitudes = []
    return render(request, 'usuarios/solicitudes_visita.html', {'solicitudes': solicitudes})


# ==============================================================================
# VISTA EXCLUSIVA PARA ADMINISTRADORES (Crear usuarios con los 4 roles)
# ==============================================================================

@staff_member_required
def admin_crear_usuario(request):
    """Vista protegida: Solo accesible si el usuario es Staff/Admin en Django"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            payload = {
                'nombre': form.cleaned_data['nombre'],
                'email': form.cleaned_data['email'],
                'telefono': form.cleaned_data['telefono'].replace('-', ''),
                'password': form.cleaned_data['password'],
                'rol': form.cleaned_data['rol']  # Puede ser 'administrador'
            }

            try:
                # Usamos el token del admin actual para autorizar esta acción ante la API
                token = request.session.get('jwt_token')
                headers = {"Authorization": f"Bearer {token}"}

                response = requests.post(
                    f"{settings.API_BASE_URL}/usuarios/register",
                    json=payload,
                    headers=headers,
                    timeout=5
                )

                if response.status_code == 201:
                    messages.success(
                        request, f"Usuario '{payload['nombre']}' creado exitosamente con rol '{payload['rol']}'.")
                else:
                    detail = response.json().get('detail', 'Error desconocido')
                    messages.error(request, f"Error API: {detail}")

            except requests.exceptions.ConnectionError:
                messages.error(request, 'No se pudo conectar con la API.')
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = AdminUserCreationForm()

    return render(request, 'admin/crear_usuario.html', {'form': form, 'title': 'Crear Nuevo Usuario'})
