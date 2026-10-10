from io import StringIO
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.management import CommandError, call_command
from django.test import TestCase

from .models import Categoria, Servicio

CLAVE = 'clave-segura-12345'


def ejecutar(*args):
    salida = StringIO()
    call_command(*args, stdout=salida, stderr=StringIO())
    return salida.getvalue()


class CargarDatosTests(TestCase):
    def test_carga_2_categorias_y_16_servicios(self):
        ejecutar('cargar_datos')
        self.assertEqual(Categoria.objects.count(), 2)
        self.assertEqual(Servicio.objects.count(), 16)
        for categoria in Categoria.objects.all():
            self.assertEqual(categoria.servicios.count(), 8)

    def test_es_repetible_sin_duplicar(self):
        ejecutar('cargar_datos')
        ejecutar('cargar_datos')
        self.assertEqual(Categoria.objects.count(), 2)
        self.assertEqual(Servicio.objects.count(), 16)

    def test_no_pisa_cambios_hechos_en_el_panel(self):
        ejecutar('cargar_datos')
        servicio = Servicio.objects.get(nombre='App móvil para residentes')
        servicio.activo = False
        servicio.save()
        ejecutar('cargar_datos')
        servicio.refresh_from_db()
        self.assertFalse(servicio.activo)

    def test_un_destacado_por_categoria_y_sin_descripcion(self):
        ejecutar('cargar_datos')
        for categoria in Categoria.objects.all():
            self.assertEqual(categoria.servicios.filter(destacado=True).count(), 1)
        self.assertFalse(Servicio.objects.exclude(descripcion='').exists())

    def test_respeta_el_orden_del_pdf(self):
        ejecutar('cargar_datos')
        primero = Servicio.objects.first()
        self.assertEqual(primero.nombre, 'Notificaciones automáticas de pagos y cobros')


class CrearPerfilesTests(TestCase):
    def test_crea_grupo_con_8_permisos(self):
        ejecutar('crear_perfiles')
        grupo = Group.objects.get(name='Gestores de contenido')
        self.assertEqual(grupo.permissions.count(), 8)

    def test_es_repetible_sin_duplicar(self):
        ejecutar('crear_perfiles')
        ejecutar('crear_perfiles')
        self.assertEqual(Group.objects.filter(name='Gestores de contenido').count(), 1)

    @mock.patch('servicios.management.commands.crear_perfiles.getpass', return_value=CLAVE)
    def test_crea_usuario_gestor_con_clave_por_consola(self, _):
        ejecutar('crear_perfiles', '--usuario', 'gestor1')
        usuario = User.objects.get(username='gestor1')
        self.assertTrue(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertTrue(usuario.check_password(CLAVE))
        self.assertTrue(usuario.groups.filter(name='Gestores de contenido').exists())
        self.assertTrue(usuario.has_perm('servicios.change_servicio'))

    @mock.patch('servicios.management.commands.crear_perfiles.getpass', return_value=CLAVE)
    def test_usuario_existente_no_cambia_su_clave(self, _):
        User.objects.create_user('gestor1', password='otra-clave-98765')
        ejecutar('crear_perfiles', '--usuario', 'gestor1')
        usuario = User.objects.get(username='gestor1')
        self.assertTrue(usuario.check_password('otra-clave-98765'))
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.groups.filter(name='Gestores de contenido').exists())

    @mock.patch('servicios.management.commands.crear_perfiles.getpass', return_value='123')
    def test_clave_debil_no_crea_el_usuario(self, _):
        with self.assertRaises(CommandError):
            ejecutar('crear_perfiles', '--usuario', 'gestor1')
        self.assertFalse(User.objects.filter(username='gestor1').exists())
