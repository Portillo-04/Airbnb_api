from rest_framework import generics, permissions
from .models import Propiedad
from .serializers import PropiedadSerializer


class IsPropietarioOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.rol == 'administrador':
            return True
        return obj.propietario == request.user


class PropiedadListCreateView(generics.ListCreateAPIView):
    serializer_class = PropiedadSerializer

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'administrador':
            return Propiedad.objects.all()
        return Propiedad.objects.filter(propietario=user)

    def perform_create(self, serializer):
        serializer.save(propietario=self.request.user)


class PropiedadDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Propiedad.objects.all()
    serializer_class = PropiedadSerializer
    permission_classes = [IsPropietarioOrAdmin]


class PropiedadDisponiblesView(generics.ListAPIView):
    serializer_class = PropiedadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Propiedad.objects.filter(estado='DISPONIBLE')
