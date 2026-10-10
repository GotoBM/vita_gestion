from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Servicio

CLAVE = 'clave-segura-12345'


class DatosBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('gestor', password=CLAVE)
        cls.cat_admin = Categoria.objects.create(
            nombre='Administración de comunidades', descripcion='Herramienta Comunidad Feliz', orden=1
        )
        cls.cat_oper = Categoria.objects.create(
            nombre='Gestión operativa', descripcion='Herramienta Swappi', orden=2
        )
        cls.cat_inactiva = Categoria.objects.create(
            nombre='Categoría oculta', descripcion='No debe verse en el catálogo', orden=3, activa=False
        )
        cls.s1 = Servicio.objects.create(
            nombre='Cálculo preciso de gastos comunes', categoria=cls.cat_admin, destacado=True
        )
        cls.s2 = Servicio.objects.create(
            nombre='Control de accesos y seguridad', categoria=cls.cat_oper
        )
        cls.s3 = Servicio.objects.create(
            nombre='Servicio retirado', categoria=cls.cat_oper, activo=False
        )
        cls.s4 = Servicio.objects.create(
            nombre='Servicio de categoría oculta', categoria=cls.cat_inactiva
        )


class PaginasPublicasTests(DatosBase):
    def test_inicio_es_publico_y_muestra_destacados(self):
        r = self.client.get(reverse('servicios:inicio'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Administración Profesional de Comunidades')
        self.assertContains(r, 'Cálculo preciso de gastos comunes')   # destacado
        self.assertNotContains(r, 'Control de accesos y seguridad')   # no destacado

    def test_catalogo_oculta_inactivos(self):
        r = self.client.get(reverse('servicios:catalogo'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Control de accesos y seguridad')
        self.assertNotContains(r, 'Servicio retirado')
        self.assertNotContains(r, 'Servicio de categoría oculta')
        self.assertContains(r, '2 servicios encontrados')

    def test_buscador_ignora_tildes_y_mayusculas(self):
        r = self.client.get(reverse('servicios:catalogo'), {'q': 'CALCULO'})
        self.assertContains(r, 'Cálculo preciso de gastos comunes')
        self.assertNotContains(r, 'Control de accesos y seguridad')
        self.assertContains(r, '1 servicio encontrado')

    def test_filtro_por_categoria(self):
        r = self.client.get(reverse('servicios:catalogo'), {'categoria': self.cat_oper.pk})
        self.assertContains(r, 'Control de accesos y seguridad')
        self.assertNotContains(r, 'Cálculo preciso de gastos comunes')

    def test_parametros_invalidos_no_rompen(self):
        for valor in ('abc', '-5', '9' * 40, ''):
            r = self.client.get(reverse('servicios:catalogo'), {'categoria': valor, 'q': '<script>'})
            self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, '<script>alert')

    def test_sin_resultados_muestra_estado_vacio(self):
        r = self.client.get(reverse('servicios:catalogo'), {'q': 'zzzz'})
        self.assertContains(r, 'No se encontraron servicios')

    def test_anonimo_ve_iconos_de_persona_lapiz_y_crear(self):
        r = self.client.get(reverse('servicios:catalogo'))
        self.assertContains(r, 'bi-person')
        self.assertContains(r, '/admin/login/?next=%2Fcatalogo%2F')
        self.assertContains(r, 'aria-label="Gestionar servicios"')
        self.assertContains(r, 'aria-label="Crear servicio"')
        self.assertContains(r, 'class="con-crear"')
        # lápiz pequeño de cada servicio visible (se oculta con CSS hasta el hover)
        self.assertContains(r, reverse('servicios:servicio_editar', kwargs={'pk': self.s1.pk}))

    def test_usuario_sin_permisos_no_ve_lapices_ni_crear(self):
        User.objects.create_user('lector', password=CLAVE, is_staff=True)
        self.client.login(username='lector', password=CLAVE)
        r = self.client.get(reverse('servicios:catalogo'))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'aria-label="Gestionar servicios"')
        self.assertNotContains(r, 'aria-label="Crear servicio"')
        self.assertNotContains(r, 'btn-editar')
        self.assertContains(r, 'Cerrar sesión')

    def test_usuario_con_permisos_ve_lapiz_y_cerrar_sesion(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('servicios:catalogo'))
        self.assertContains(r, 'aria-label="Gestionar servicios"')
        self.assertContains(r, 'btn-editar')
        self.assertContains(r, 'action="/salir/"')

    def test_cerrar_sesion_por_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('salir'))
        self.assertRedirects(r, '/', fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('servicios:panel_servicios')).status_code, 302)


class PanelRenderizadoTests(DatosBase):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_listas_del_panel(self):
        r = self.client.get(reverse('servicios:panel_servicios'))
        self.assertContains(r, 'Gestión de servicios')
        self.assertContains(r, 'Servicio retirado')          # el panel sí muestra inactivos
        self.assertContains(r, 'Inactivo')
        r = self.client.get(reverse('servicios:panel_categorias'))
        self.assertContains(r, 'Gestión de categorías')
        self.assertContains(r, 'Categoría oculta')

    def test_busqueda_en_el_panel(self):
        r = self.client.get(reverse('servicios:panel_servicios'), {'q': 'gestion'})
        self.assertContains(r, 'Control de accesos y seguridad')   # coincide por su categoría
        self.assertNotContains(r, 'Cálculo preciso de gastos comunes')

    def test_formularios_se_muestran(self):
        for nombre, kwargs in [
            ('servicios:servicio_crear', {}), ('servicios:categoria_crear', {}),
            ('servicios:servicio_editar', {'pk': self.s1.pk}),
            ('servicios:categoria_editar', {'pk': self.cat_admin.pk}),
        ]:
            with self.subTest(ruta=nombre):
                self.assertEqual(self.client.get(reverse(nombre, kwargs=kwargs)).status_code, 200)

    def test_errores_de_validacion_se_muestran(self):
        r = self.client.post(reverse('servicios:servicio_crear'), {
            'nombre': '12345', 'descripcion': 'corta', 'categoria': self.cat_oper.pk, 'activo': 'on',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no puede ser solo números')
        self.assertContains(r, 'al menos 10 caracteres')
        self.assertContains(r, 'No se pudo guardar')

    def test_confirmacion_de_eliminar_advierte_si_hay_servicios(self):
        r = self.client.get(reverse('servicios:categoria_eliminar', kwargs={'pk': self.cat_oper.pk}))
        self.assertContains(r, '2 servicios asociados')
        r = self.client.get(reverse('servicios:servicio_eliminar', kwargs={'pk': self.s1.pk}))
        self.assertContains(r, 'Esta acción no se puede deshacer.')
        self.assertNotContains(r, 'asociado')

    def test_pagina_403_con_diseno(self):
        User.objects.create_user('lector', password=CLAVE, is_staff=True)
        self.client.logout()
        self.client.login(username='lector', password=CLAVE)
        r = self.client.get(reverse('servicios:panel_servicios'))
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, 'No tiene permisos para esta acción', status_code=403)

    def test_login_del_admin_usa_la_marca(self):
        self.client.logout()
        r = self.client.get('/admin/login/?next=/panel/servicios/')
        self.assertContains(r, 'logo-vita-pequeno.png')
        self.assertContains(r, 'admin_vita.css')
