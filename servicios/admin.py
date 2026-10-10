from django.contrib import admin

from .models import Categoria, Servicio

# Identidad de Vita Gestión en el administrador de Django
admin.site.site_header = 'Vita Gestión · Administración'
admin.site.site_title = 'Vita Gestión'
admin.site.index_title = 'Panel de administración'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activa', 'cantidad_servicios')
    list_editable = ('orden', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')

    @admin.display(description='servicios')
    def cantidad_servicios(self, obj):
        return obj.servicios.count()


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'destacado', 'activo', 'actualizado')
    list_editable = ('destacado', 'activo')
    list_filter = ('categoria', 'destacado', 'activo')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    list_select_related = ('categoria',)
    readonly_fields = ('creado', 'actualizado')