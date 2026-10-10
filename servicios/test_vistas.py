from django.contrib.auth.models import Permission, User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Servicio

CLAVE = 'clave-segura-12345'

RUTAS_PANEL = [
    ('servicios:panel_servicios', {}),
    ('servicios:servicio_crear', {}),
    ('servicios:servicio_editar', {'pk': 1}),
    ('servicios:servicio_eliminar', {'pk': 1}),
    ('servicios:panel_categorias', {}),
    ('servicios:categoria_crear', {}),
    ('servicios:categoria_editar', {'pk': 1}),
    ('servicios:categoria_eliminar', {'pk': 1}),
]


def usuario_con_permisos(nombre, *codenames):
    """Crea un usuario staff con solo los permisos indicados."""
    usuario = User.objects.create_user(nombre, password=CLAVE, is_staff=True)
    usuario.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label='servicios', codename__in=codenames
        )
    )
    return usuario


class AccesoPanelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi'
        )
        cls.servicio = Servicio.objects.create(
            nombre='Control de accesos y seguridad', categoria=cls.categoria
        )

    def test_anonimo_es_redirigido_al_login(self):
        for nombre, kwargs in RUTAS_PANEL:
            with self.subTest(ruta=nombre):
                url = reverse(nombre, kwargs=kwargs)
                respuesta = self.client.get(url)
                self.assertRedirects(
                    respuesta, f'/admin/login/?next={url}',
                    fetch_redirect_response=False,
                )

    def test_usuario_sin_permisos_recibe_403(self):
        self.client.force_login(usuario_con_permisos('sin_permisos'))
        for nombre, kwargs in RUTAS_PANEL:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre, kwargs=kwargs))
                self.assertEqual(respuesta.status_code, 403)

    def test_permiso_granular(self):
        """Con solo 'add_servicio': puede crear, pero no editar ni eliminar."""
        self.client.force_login(usuario_con_permisos('solo_crea', 'add_servicio'))
        datos = {
            'nombre': 'Notificaciones en tiempo real',
            'descripcion': '',
            'categoria': self.categoria.pk,
            'activo': 'on',
        }
        crear = self.client.post(reverse('servicios:servicio_crear'), datos)
        self.assertRedirects(
            crear, reverse('servicios:panel_servicios'), fetch_redirect_response=False
        )
        editar = self.client.post(
            reverse('servicios:servicio_editar', kwargs={'pk': self.servicio.pk}), datos
        )
        eliminar = self.client.post(
            reverse('servicios:servicio_eliminar', kwargs={'pk': self.servicio.pk})
        )
        self.assertEqual(editar.status_code, 403)
        self.assertEqual(eliminar.status_code, 403)
        self.assertTrue(Servicio.objects.filter(pk=self.servicio.pk).exists())


class CrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('gestor', password=CLAVE)
        cls.categoria = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi'
        )
        cls.servicio = Servicio.objects.create(
            nombre='Control de accesos y seguridad', categoria=cls.categoria
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_crear_servicio(self):
        respuesta = self.client.post(reverse('servicios:servicio_crear'), {
            'nombre': 'Notificaciones en tiempo real',
            'descripcion': '',
            'categoria': self.categoria.pk,
            'activo': 'on',
        })
        self.assertRedirects(
            respuesta, reverse('servicios:panel_servicios'), fetch_redirect_response=False
        )
        self.assertTrue(
            Servicio.objects.filter(nombre='Notificaciones en tiempo real').exists()
        )

    def test_editar_servicio(self):
        respuesta = self.client.post(
            reverse('servicios:servicio_editar', kwargs={'pk': self.servicio.pk}),
            {
                'nombre': 'Control de accesos',
                'descripcion': '',
                'categoria': self.categoria.pk,
                'activo': 'on',
            },
        )
        self.assertRedirects(
            respuesta, reverse('servicios:panel_servicios'), fetch_redirect_response=False
        )
        self.servicio.refresh_from_db()
        self.assertEqual(self.servicio.nombre, 'Control de accesos')

    def test_eliminar_servicio(self):
        respuesta = self.client.post(
            reverse('servicios:servicio_eliminar', kwargs={'pk': self.servicio.pk})
        )
        self.assertRedirects(
            respuesta, reverse('servicios:panel_servicios'), fetch_redirect_response=False
        )
        self.assertFalse(Servicio.objects.filter(pk=self.servicio.pk).exists())

    def test_crear_categoria(self):
        respuesta = self.client.post(reverse('servicios:categoria_crear'), {
            'nombre': 'Administración de comunidades',
            'descripcion': 'Herramienta Comunidad Feliz',
            'orden': 1,
            'activa': 'on',
        })
        self.assertRedirects(
            respuesta, reverse('servicios:panel_categorias'), fetch_redirect_response=False
        )
        self.assertTrue(
            Categoria.objects.filter(nombre='Administración de comunidades').exists()
        )

    def test_editar_categoria(self):
        respuesta = self.client.post(
            reverse('servicios:categoria_editar', kwargs={'pk': self.categoria.pk}),
            {
                'nombre': 'Gestión operativa',
                'descripcion': 'Herramienta Swappi de Comunidad Feliz',
                'orden': 2,
                'activa': 'on',
            },
        )
        self.assertRedirects(
            respuesta, reverse('servicios:panel_categorias'), fetch_redirect_response=False
        )
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.orden, 2)

    def test_eliminar_categoria_con_servicios_esta_protegida(self):
        respuesta = self.client.post(
            reverse('servicios:categoria_eliminar', kwargs={'pk': self.categoria.pk})
        )
        self.assertRedirects(
            respuesta, reverse('servicios:panel_categorias'), fetch_redirect_response=False
        )
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        mensajes = [str(m) for m in get_messages(respuesta.wsgi_request)]
        self.assertTrue(any('No se puede eliminar' in m for m in mensajes))

    def test_eliminar_categoria_sin_servicios(self):
        vacia = Categoria.objects.create(
            nombre='Categoría vacía', descripcion='Sin servicios asociados'
        )
        self.client.post(
            reverse('servicios:categoria_eliminar', kwargs={'pk': vacia.pk})
        )
        self.assertFalse(Categoria.objects.filter(pk=vacia.pk).exists())