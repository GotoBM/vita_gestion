from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

NOMBRE_GRUPO = 'Gestores de contenido'

# Permisos nativos de Django: ver, agregar, cambiar y eliminar en ambos modelos
PERMISOS = [
    f'{accion}_{modelo}'
    for modelo in ('categoria', 'servicio')
    for accion in ('view', 'add', 'change', 'delete')
]

INTENTOS_CLAVE = 3


class Command(BaseCommand):
    help = (
        f'Crea (o actualiza) el grupo «{NOMBRE_GRUPO}» con los permisos del panel. '
        'Con --usuario también crea un usuario de ese perfil y pide la contraseña por consola.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            help='Nombre de un usuario gestor a crear o a agregar al grupo (opcional).',
        )

    def handle(self, *args, **options):
        grupo = self.preparar_grupo()
        nombre_usuario = (options.get('usuario') or '').strip()
        if nombre_usuario:
            self.preparar_usuario(nombre_usuario, grupo)

    # ------------------------------------------------------------------
    def preparar_grupo(self):
        permisos = Permission.objects.filter(
            content_type__app_label='servicios', codename__in=PERMISOS
        )
        if permisos.count() != len(PERMISOS):
            raise CommandError(
                'Faltan permisos de la aplicación «servicios». '
                'Ejecute primero: python manage.py migrate'
            )
        grupo, creado = Group.objects.get_or_create(name=NOMBRE_GRUPO)
        grupo.permissions.set(permisos)   # repetible: deja siempre los mismos 8
        estado = 'creado' if creado else 'actualizado'
        self.stdout.write(self.style.SUCCESS(
            f'Grupo «{NOMBRE_GRUPO}» {estado} con {len(PERMISOS)} permisos.'
        ))
        return grupo

    def preparar_usuario(self, nombre_usuario, grupo):
        Usuario = get_user_model()
        usuario = Usuario.objects.filter(username=nombre_usuario).first()

        if usuario is not None:
            # No se toca la contraseña de un usuario que ya existe
            cambios = []
            if not usuario.is_staff:
                usuario.is_staff = True   # necesario para entrar por /admin/login/
                usuario.save(update_fields=['is_staff'])
                cambios.append('marcado como staff')
            if not usuario.groups.filter(pk=grupo.pk).exists():
                usuario.groups.add(grupo)
                cambios.append(f'agregado a «{NOMBRE_GRUPO}»')
            detalle = ', '.join(cambios) if cambios else 'sin cambios'
            self.stdout.write(self.style.SUCCESS(
                f'El usuario «{nombre_usuario}» ya existía ({detalle}). '
                'Su contraseña no se modificó.'
            ))
            return

        clave = self.pedir_clave(nombre_usuario)
        with transaction.atomic():
            usuario = Usuario.objects.create_user(
                username=nombre_usuario, password=clave, is_staff=True
            )
            usuario.groups.add(grupo)
        self.stdout.write(self.style.SUCCESS(
            f'Usuario «{nombre_usuario}» creado y agregado a «{NOMBRE_GRUPO}».'
        ))

    def pedir_clave(self, nombre_usuario):
        """Pide la contraseña por consola (no se ve al escribir) y la valida."""
        for _ in range(INTENTOS_CLAVE):
            clave = getpass('Contraseña: ')
            repetida = getpass('Contraseña (otra vez): ')
            if clave != repetida:
                self.stderr.write('Las contraseñas no coinciden. Intente de nuevo.')
                continue
            try:
                validate_password(clave, user=get_user_model()(username=nombre_usuario))
            except ValidationError as error:
                for mensaje in error.messages:
                    self.stderr.write(mensaje)
                continue
            return clave
        raise CommandError('Demasiados intentos fallidos. No se creó el usuario.')
