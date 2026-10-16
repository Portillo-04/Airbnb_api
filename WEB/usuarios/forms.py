from django import forms


class AdminUserCreationForm(forms.Form):
    nombre = forms.CharField(
        label='Nombre de usuario',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: nuevo_admin'})
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'})
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '2777-XXXX'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Mínimo 6 caracteres'}),
        min_length=6
    )

    # AQUÍ ESTÁ LA DIFERENCIA: Incluye 'administrador'
    ROL_CHOICES = [
        ('propietario', 'Propietario'),
        ('inquilino', 'Inquilino'),
        ('visitante', 'Visitante'),
        ('administrador', 'Administrador'),
    ]
    rol = forms.ChoiceField(label='Rol del usuario', choices=ROL_CHOICES)
