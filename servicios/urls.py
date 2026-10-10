from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'servicios'

urlpatterns = [
    # Públicas
    path('', views.InicioView.as_view(), name='inicio'),
    path('catalogo/', views.CatalogoView.as_view(), name='catalogo'),

    # Panel de gestión (login + permisos)
    path('panel/', RedirectView.as_view(pattern_name='servicios:panel_servicios'), name='panel'),

    path('panel/servicios/', views.ServicioListaView.as_view(), name='panel_servicios'),
    path('panel/servicios/nuevo/', views.ServicioCrearView.as_view(), name='servicio_crear'),
    path('panel/servicios/<int:pk>/editar/', views.ServicioEditarView.as_view(), name='servicio_editar'),
    path('panel/servicios/<int:pk>/eliminar/', views.ServicioEliminarView.as_view(), name='servicio_eliminar'),

    path('panel/categorias/', views.CategoriaListaView.as_view(), name='panel_categorias'),
    path('panel/categorias/nueva/', views.CategoriaCrearView.as_view(), name='categoria_crear'),
    path('panel/categorias/<int:pk>/editar/', views.CategoriaEditarView.as_view(), name='categoria_editar'),
    path('panel/categorias/<int:pk>/eliminar/', views.CategoriaEliminarView.as_view(), name='categoria_eliminar'),
]