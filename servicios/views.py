import unicodedata

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)

from .forms import CategoriaForm, ServicioForm
from .models import Categoria, Servicio


# ---------------------------------------------------------------------------
# Apoyo: búsqueda sin distinguir mayúsculas ni tildes
# ---------------------------------------------------------------------------
def normalizar(texto):
    """Minúsculas y sin tildes: 'Gestión' -> 'gestion'."""
    descompuesto = unicodedata.normalize('NFD', texto or '')
    sin_tildes = ''.join(c for c in descompuesto if unicodedata.category(c) != 'Mn')
    return sin_tildes.casefold()


def buscar(queryset, texto, textos_de):
    """Filtra el queryset por los textos que devuelve textos_de(objeto)."""
    consulta = normalizar(texto.strip())
    if not consulta:
        return queryset
    ids = [
        objeto.pk
        for objeto in queryset
        if any(consulta in normalizar(t) for t in textos_de(objeto))
    ]
    return queryset.filter(pk__in=ids)


def textos_servicio(servicio):
    return [servicio.nombre, servicio.descripcion, servicio.categoria.nombre]


def textos_categoria(categoria):
    return [categoria.nombre, categoria.descripcion]


def entero_o_none(valor):
    """Convierte un parámetro GET a entero positivo, o None si no es válido."""
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if 0 < numero < 10**9 else None


# ---------------------------------------------------------------------------
# Vistas públicas (sin login)
# ---------------------------------------------------------------------------
class InicioView(TemplateView):
    template_name = 'servicios/inicio.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['destacados'] = Servicio.objects.filter(
            activo=True, destacado=True, categoria__activa=True
        ).select_related('categoria')
        return contexto


class CatalogoView(TemplateView):
    template_name = 'servicios/catalogo.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        categoria_sel = entero_o_none(self.request.GET.get('categoria'))

        servicios = Servicio.objects.filter(
            activo=True, categoria__activa=True
        ).select_related('categoria')
        if categoria_sel:
            servicios = servicios.filter(categoria_id=categoria_sel)
        servicios = list(buscar(servicios, q, textos_servicio))

        categorias = list(Categoria.objects.filter(activa=True))
        grupos = []
        for categoria in categorias:
            items = [s for s in servicios if s.categoria_id == categoria.pk]
            if items:
                grupos.append({'categoria': categoria, 'servicios': items})

        contexto.update({
            'grupos': grupos,
            'categorias': categorias,
            'q': q,
            'categoria_sel': categoria_sel,
            'total': len(servicios),
        })
        return contexto


# ---------------------------------------------------------------------------
# Mixins del panel de gestión
# ---------------------------------------------------------------------------
class PanelMixin(PermissionRequiredMixin):
    """Sin sesión -> redirige a LOGIN_URL (?next=). Con sesión sin permiso -> 403."""

    seccion = ''

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['seccion'] = self.seccion
        return contexto


class FormularioMensajesMixin:
    """Mensajes de éxito (al guardar) y de error (formulario inválido)."""

    mensaje_exito = ''

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito.format(nombre=self.object.nombre))
        return respuesta

    def form_invalid(self, form):
        messages.error(self.request, 'No se pudo guardar: revise los campos marcados.')
        return super().form_invalid(form)


class EliminarMixin:
    """Elimina por POST y convierte ProtectedError en un mensaje claro."""

    mensaje_exito = ''

    def mensaje_protegido(self):
        return 'No se puede eliminar: tiene registros asociados.'

    def form_valid(self, form):
        nombre = self.object.nombre
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.mensaje_protegido())
            return redirect(self.get_success_url())
        messages.success(self.request, self.mensaje_exito.format(nombre=nombre))
        return respuesta


# ---------------------------------------------------------------------------
# CRUD de Servicios
# ---------------------------------------------------------------------------
class ServicioListaView(PanelMixin, ListView):
    permission_required = 'servicios.view_servicio'
    template_name = 'servicios/panel_servicios.html'
    context_object_name = 'servicios'
    seccion = 'servicios'

    def get_queryset(self):
        queryset = Servicio.objects.select_related('categoria')
        return buscar(queryset, self.request.GET.get('q', ''), textos_servicio)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['q'] = self.request.GET.get('q', '').strip()
        return contexto


class ServicioCrearView(PanelMixin, FormularioMensajesMixin, CreateView):
    permission_required = 'servicios.add_servicio'
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicios/servicio_form.html'
    success_url = reverse_lazy('servicios:panel_servicios')
    mensaje_exito = 'Servicio «{nombre}» creado correctamente.'
    seccion = 'servicios'


class ServicioEditarView(PanelMixin, FormularioMensajesMixin, UpdateView):
    permission_required = 'servicios.change_servicio'
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicios/servicio_form.html'
    success_url = reverse_lazy('servicios:panel_servicios')
    mensaje_exito = 'Servicio «{nombre}» actualizado correctamente.'
    seccion = 'servicios'


class ServicioEliminarView(PanelMixin, EliminarMixin, DeleteView):
    permission_required = 'servicios.delete_servicio'
    model = Servicio
    template_name = 'servicios/confirmar_eliminar.html'
    success_url = reverse_lazy('servicios:panel_servicios')
    mensaje_exito = 'Servicio «{nombre}» eliminado correctamente.'
    seccion = 'servicios'


# ---------------------------------------------------------------------------
# CRUD de Categorías
# ---------------------------------------------------------------------------
class CategoriaListaView(PanelMixin, ListView):
    permission_required = 'servicios.view_categoria'
    template_name = 'servicios/panel_categorias.html'
    context_object_name = 'categorias'
    seccion = 'categorias'

    def get_queryset(self):
        queryset = Categoria.objects.annotate(num_servicios=Count('servicios'))
        return buscar(queryset, self.request.GET.get('q', ''), textos_categoria)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['q'] = self.request.GET.get('q', '').strip()
        return contexto


class CategoriaCrearView(PanelMixin, FormularioMensajesMixin, CreateView):
    permission_required = 'servicios.add_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'servicios/categoria_form.html'
    success_url = reverse_lazy('servicios:panel_categorias')
    mensaje_exito = 'Categoría «{nombre}» creada correctamente.'
    seccion = 'categorias'


class CategoriaEditarView(PanelMixin, FormularioMensajesMixin, UpdateView):
    permission_required = 'servicios.change_categoria'
    model = Categoria
    form_class = CategoriaForm
    template_name = 'servicios/categoria_form.html'
    success_url = reverse_lazy('servicios:panel_categorias')
    mensaje_exito = 'Categoría «{nombre}» actualizada correctamente.'
    seccion = 'categorias'


class CategoriaEliminarView(PanelMixin, EliminarMixin, DeleteView):
    permission_required = 'servicios.delete_categoria'
    model = Categoria
    template_name = 'servicios/confirmar_eliminar.html'
    success_url = reverse_lazy('servicios:panel_categorias')
    mensaje_exito = 'Categoría «{nombre}» eliminada correctamente.'
    seccion = 'categorias'

    def mensaje_protegido(self):
        cantidad = self.object.servicios.count()
        return (
            f'No se puede eliminar la categoría «{self.object.nombre}»: tiene '
            f'{cantidad} servicio(s) asociado(s). Elimine o reasigne esos servicios primero.'
        )