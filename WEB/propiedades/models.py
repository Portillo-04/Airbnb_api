from django.db import models
from usuarios.models import Usuario


class EstadoPropiedad(models.TextChoices):
    DISPONIBLE = 'DISPONIBLE', 'Disponible'
    ALQUILADA = 'ALQUILADA', 'Alquilada'
    MANTENIMIENTO = 'MANTENIMIENTO', 'En Mantenimiento'


class Propiedad(models.Model):
    direccion = models.CharField(max_length=255)
    descripcion = models.TextField(max_length=1000)
    precio_mensual = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=EstadoPropiedad.choices,
        default=EstadoPropiedad.DISPONIBLE
    )
    fotos_url = models.URLField(blank=True, null=True)
    propietario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='propiedades',
        limit_choices_to={'rol': Usuario.Rol.PROPIETARIO}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.direccion} - {self.estado}"
