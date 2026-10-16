from django.contrib import admin
from .models import Usuario
from .views import ver_solicitudes_alquiler, ver_solicitudes_visita


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'rol',
                    'telefono', 'activo', 'date_joined']
    list_filter = ['rol', 'activo', 'date_joined']
    search_fields = ['username', 'email', 'telefono']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        ('Información Personal', {
         'fields': ('username', 'email', 'password')}),
        ('Detalles de Contacto', {'fields': ('telefono', 'rol', 'activo')}),
        ('Fechas del Sistema', {
         'fields': ('date_joined', 'last_login'), 'classes': ('collapse',)}),
    )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('solicitudes-alquiler/', self.admin_site.admin_view(
                ver_solicitudes_alquiler), name='solicitudes-alquiler'),
            path('solicitudes-visita/', self.admin_site.admin_view(
                ver_solicitudes_visita), name='solicitudes-visita'),
        ]
        return custom_urls + urls
