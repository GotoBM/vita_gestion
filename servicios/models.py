from django.db import models


class Categoria(models.Model):
    """Área de servicio de Vita Gestión (ej.: Administración de comunidades)."""

    nombre = models.CharField('nombre', max_length=100, unique=True)
    descripcion = models.TextField('descripción', max_length=500)
    orden = models.PositiveIntegerField('orden', default=0)
    activa = models.BooleanField('activa', default=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    """Solución que ofrece Vita Gestión. Pertenece a una sola categoría."""

    nombre = models.CharField('nombre', max_length=150)
    descripcion = models.TextField('descripción', max_length=500, blank=True)
    categoria = models.ForeignKey(
        Categoria,
        verbose_name='categoría',
        on_delete=models.PROTECT,   # no se puede borrar una categoría con servicios
        related_name='servicios',
    )
    destacado = models.BooleanField('destacado', default=False)
    activo = models.BooleanField('activo', default=True)
    creado = models.DateTimeField('creado', auto_now_add=True)
    actualizado = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'
        # Se ordena por 'id' para respetar el orden del PDF al cargar los datos
        ordering = ['categoria__orden', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['categoria', 'nombre'],
                name='servicio_nombre_unico_por_categoria',
            ),
        ]

    def __str__(self):
        return f'{self.nombre} ({self.categoria})'
