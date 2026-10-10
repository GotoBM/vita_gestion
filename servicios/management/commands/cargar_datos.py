from django.core.management.base import BaseCommand
from django.db import transaction

from servicios.models import Categoria, Servicio

# ---------------------------------------------------------------------------
# Datos tomados tal cual de la presentación de Vita Gestión (PDF).
# Las descripciones de los servicios quedan vacías; la de cada categoría
# solo nombra su herramienta. No se inventan precios ni otros datos.
# ---------------------------------------------------------------------------
CATALOGO = [
    {
        'nombre': 'Administración de comunidades',
        'descripcion': 'Gestión financiera y administrativa con la herramienta Comunidad Feliz.',
        'orden': 1,
        'servicios': [
            'Notificaciones automáticas de pagos y cobros',
            'Cálculo preciso de gastos comunes',
            'Control centralizado de proveedores',
            'Reportes financieros certificados',
            'Gestión de remuneraciones (previred)',
            'App móvil para residentes',
            'Acceso a la plataforma seguro y controlado',
            'Reportes avanzados y certificados',
        ],
    },
    {
        'nombre': 'Gestión operativa',
        'descripcion': 'Gestión de tareas, visitas y mantenciones con la herramienta Swappi.',
        'orden': 2,
        'servicios': [
            'Gestión centralizada de tareas y responsabilidades',
            'Control de visitas en terreno y mantenciones',
            'Gestión integrada de proveedores',
            'Reportería detallada de actividades',
            'Notificaciones en tiempo real',
            'Seguimiento de equipos e instalaciones',
            'Control de accesos y seguridad',
            'Análisis del desempeño operativo',
        ],
    },
]

# Servicios que se muestran como destacados en la portada (uno por categoría).
# Se pueden cambiar aquí o desde el panel de gestión.
DESTACADOS = {
    'Cálculo preciso de gastos comunes',
    'Control de visitas en terreno y mantenciones',
}


class Command(BaseCommand):
    help = (
        'Carga las 2 categorías y los 16 servicios de la presentación de Vita Gestión. '
        'Es repetible: no duplica ni pisa los cambios hechos desde el panel.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        categorias_nuevas = servicios_nuevos = servicios_existentes = 0

        for datos in CATALOGO:
            # Se busca sin distinguir mayúsculas, igual que el formulario
            categoria = Categoria.objects.filter(nombre__iexact=datos['nombre']).first()
            if categoria is None:
                categoria = Categoria.objects.create(
                    nombre=datos['nombre'],
                    descripcion=datos['descripcion'],
                    orden=datos['orden'],
                )
                categorias_nuevas += 1

            for nombre in datos['servicios']:
                existe = Servicio.objects.filter(
                    categoria=categoria, nombre__iexact=nombre
                ).exists()
                if existe:
                    servicios_existentes += 1
                    continue
                Servicio.objects.create(
                    nombre=nombre,
                    categoria=categoria,
                    destacado=nombre in DESTACADOS,
                )
                servicios_nuevos += 1

        self.stdout.write(self.style.SUCCESS(
            f'Categorías creadas: {categorias_nuevas} · '
            f'Servicios creados: {servicios_nuevos} · '
            f'Servicios que ya existían: {servicios_existentes}'
        ))
        self.stdout.write(
            f'Total en la base de datos: {Categoria.objects.count()} categoría(s) '
            f'y {Servicio.objects.count()} servicio(s).'
        )
