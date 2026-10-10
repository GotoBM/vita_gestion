from django.test import TestCase

from .forms import CategoriaForm, ServicioForm
from .models import Categoria, Servicio


class CategoriaFormTests(TestCase):
    def datos(self, **cambios):
        base = {
            'nombre': 'Administración de comunidades',
            'descripcion': 'Herramienta Comunidad Feliz',
            'orden': 1,
            'activa': True,
        }
        base.update(cambios)
        return base

    def test_datos_validos(self):
        self.assertTrue(CategoriaForm(self.datos()).is_valid())

    def test_nombre_muy_corto(self):
        form = CategoriaForm(self.datos(nombre='ab'))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_solo_numeros(self):
        form = CategoriaForm(self.datos(nombre='12345'))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_nombre_duplicado_ignora_mayusculas(self):
        Categoria.objects.create(nombre='Gestión operativa', descripcion='Herramienta Swappi')
        form = CategoriaForm(self.datos(nombre='GESTIÓN OPERATIVA'))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_descripcion_muy_corta(self):
        form = CategoriaForm(self.datos(descripcion='corta'))
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

    def test_orden_negativo(self):
        form = CategoriaForm(self.datos(orden=-1))
        self.assertFalse(form.is_valid())
        self.assertIn('orden', form.errors)

    def test_no_se_puede_desactivar_con_servicios_activos(self):
        categoria = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi'
        )
        Servicio.objects.create(nombre='Control de accesos y seguridad', categoria=categoria)
        form = CategoriaForm(
            self.datos(nombre='Gestión operativa', activa=False), instance=categoria
        )
        self.assertFalse(form.is_valid())
        self.assertIn('activa', form.errors)

    def test_se_puede_desactivar_si_sus_servicios_estan_inactivos(self):
        categoria = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi'
        )
        Servicio.objects.create(
            nombre='Control de accesos y seguridad', categoria=categoria, activo=False
        )
        form = CategoriaForm(
            self.datos(nombre='Gestión operativa', activa=False), instance=categoria
        )
        self.assertTrue(form.is_valid())


class ServicioFormTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi'
        )
        self.otra = Categoria.objects.create(
            nombre='Administración de comunidades',
            descripcion='Herramienta Comunidad Feliz',
        )

    def datos(self, **cambios):
        base = {
            'nombre': 'Notificaciones en tiempo real',
            'descripcion': '',
            'categoria': self.cat.pk,
            'destacado': False,
            'activo': True,
        }
        base.update(cambios)
        return base

    def test_valido_sin_descripcion(self):
        self.assertTrue(ServicioForm(self.datos()).is_valid())

    def test_descripcion_corta_si_se_escribe(self):
        form = ServicioForm(self.datos(descripcion='corta'))
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

    def test_nombre_duplicado_en_misma_categoria(self):
        Servicio.objects.create(nombre='Notificaciones en tiempo real', categoria=self.cat)
        form = ServicioForm(self.datos(nombre='NOTIFICACIONES EN TIEMPO REAL'))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_mismo_nombre_en_otra_categoria_es_valido(self):
        Servicio.objects.create(nombre='Notificaciones en tiempo real', categoria=self.otra)
        self.assertTrue(ServicioForm(self.datos()).is_valid())

    def test_categoria_inactiva_es_rechazada(self):
        self.cat.activa = False
        self.cat.save()
        form = ServicioForm(self.datos())
        self.assertFalse(form.is_valid())
        self.assertIn('categoria', form.errors)

    def test_editar_no_se_cuenta_como_duplicado_de_si_mismo(self):
        servicio = Servicio.objects.create(
            nombre='Control de accesos y seguridad', categoria=self.cat
        )
        form = ServicioForm(
            self.datos(nombre='Control de accesos y seguridad'), instance=servicio
        )
        self.assertTrue(form.is_valid())
    def test_destacado_requiere_servicio_activo(self):
        form = ServicioForm(self.datos(destacado=True, activo=False))
        self.assertFalse(form.is_valid())
        self.assertIn('destacado', form.errors)

    def test_destacado_y_activo_es_valido(self):
        form = ServicioForm(self.datos(destacado=True, activo=True))
        self.assertTrue(form.is_valid())