import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        PROPIETARIO = 'propietario', 'Propietario'
        INQUILINO = 'inquilino', 'Inquilino'
        VISITANTE = 'visitante', 'Visitante'

    email = models.EmailField(unique=True, max_length=150)
    telefono = models.CharField(max_length=11, blank=True, null=True)
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.VISITANTE
    )
    activo = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def clean(self):
        super().clean()
        if self.telefono and not re.match(r"^\d{4,5}-\d{4}$", self.telefono):
            raise ValidationError(
                {'telefono': 'Formato inválido: 0000-0000 o 00000-0000'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
