from django import forms

from .models import Categoria, Servicio


# ---------------------------------------------------------------------------
# Funciones de apoyo (reutilizadas por ambos formularios)
# ---------------------------------------------------------------------------
def validar_nombre(nombre):
    """Normaliza espacios y exige largo mínimo y al menos una letra."""
    nombre = ' '.join(nombre.split())  # quita espacios sobrantes
    if len(nombre) < 3:
        raise forms.ValidationError('El nombre debe tener al menos 3 caracteres.')
    if not any(caracter.isalpha() for caracter in nombre):
        raise forms.ValidationError(
            'El nombre no puede ser solo números o símbolos: debe incluir letras.'
        )
    return nombre


def validar_descripcion(texto, minimo=10, maximo=500):
    """Valida el largo de una descripción ya recortada (strip)."""
    texto = texto.strip()
    if len(texto) < minimo:
        raise forms.ValidationError(
            f'La descripción debe tener al menos {minimo} caracteres.'
        )
    if len(texto) > maximo:
        raise forms.ValidationError(
            f'La descripción no puede superar los {maximo} caracteres.'
        )
    return texto


class EstiloCamposMixin:
    """Agrega una clase CSS a cada campo (se usará en la Etapa 5)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            es_check = isinstance(campo.widget, forms.CheckboxInput)
            campo.widget.attrs['class'] = 'check' if es_check else 'campo'


class CategoriaChoiceField(forms.ModelChoiceField):
    """Lista desplegable que marca las categorías inactivas."""

    def label_from_instance(self, obj):
        return obj.nombre if obj.activa else f'{obj.nombre} (inactiva)'


# ---------------------------------------------------------------------------
# Formulario de Categoría
# ---------------------------------------------------------------------------
class CategoriaForm(EstiloCamposMixin, forms.ModelForm):
    # Se declara aquí (sin min_value) para que la regla "no negativo"
    # la aplique nuestro clean_orden y no el mensaje genérico de Django.
    orden = forms.IntegerField(
        label='Orden',
        initial=0,
        help_text='Posición en que se muestra la categoría (0 = primero).',
        error_messages={
            'required': 'El orden es obligatorio.',
            'invalid': 'Ingrese un número entero.',
        },
    )

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'orden', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej.: Gestión operativa'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.',
                'max_length': 'El nombre no puede superar los 100 caracteres.',
            },
            'descripcion': {
                'required': 'La descripción es obligatoria.',
                'max_length': 'La descripción no puede superar los 500 caracteres.',
            },
        }

    def clean_nombre(self):
        nombre = validar_nombre(self.cleaned_data['nombre'])
        clave = nombre.casefold()
        existentes = Categoria.objects.exclude(pk=self.instance.pk).values_list(
            'nombre', flat=True
        )
        if any(otro.casefold() == clave for otro in existentes):
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre

    def clean_descripcion(self):
        return validar_descripcion(self.cleaned_data['descripcion'])

    def clean_orden(self):
        orden = self.cleaned_data['orden']
        if orden < 0:
            raise forms.ValidationError('El orden no puede ser negativo.')
        if orden > 999:
            raise forms.ValidationError('El orden no puede ser mayor a 999.')
        return orden
    def clean_activa(self):
        """Una categoría no puede desactivarse si tiene servicios activos."""
        activa = self.cleaned_data['activa']
        if not activa and self.instance.pk:
            activos = self.instance.servicios.filter(activo=True).count()
            if activos:
                raise forms.ValidationError(
                    f'No se puede desactivar: la categoría tiene {activos} '
                    'servicio(s) activo(s). Desactívelos primero.'
                )
        return activa   


# ---------------------------------------------------------------------------
# Formulario de Servicio
# ---------------------------------------------------------------------------
class ServicioForm(EstiloCamposMixin, forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'categoria', 'destacado', 'activo']
        field_classes = {'categoria': CategoriaChoiceField}
        widgets = {
            'nombre': forms.TextInput(
                attrs={'placeholder': 'Ej.: Control de accesos y seguridad'}
            ),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'descripcion': 'Opcional. Si la escribe, mínimo 10 caracteres.',
        }
        error_messages = {
            'nombre': {
                'required': 'El nombre es obligatorio.',
                'max_length': 'El nombre no puede superar los 150 caracteres.',
            },
            'descripcion': {
                'max_length': 'La descripción no puede superar los 500 caracteres.',
            },
            'categoria': {
                'required': 'Debe seleccionar una categoría.',
                'invalid_choice': 'Seleccione una categoría válida de la lista.',
            },
        }

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data['nombre'])

    def clean_descripcion(self):
        texto = self.cleaned_data['descripcion'].strip()
        if not texto:  # es opcional
            return ''
        return validar_descripcion(texto)

    def clean_categoria(self):
        categoria = self.cleaned_data['categoria']
        es_la_actual = (
            self.instance.pk is not None
            and self.instance.categoria_id == categoria.pk
        )
        # Una categoría inactiva solo se acepta si el servicio ya pertenecía a ella
        if not categoria.activa and not es_la_actual:
            raise forms.ValidationError(
                'La categoría seleccionada está inactiva. Elija una categoría activa.'
            )
        return categoria

    def clean(self):
        """Regla que depende de dos campos: nombre único dentro de su categoría."""
        datos = super().clean()
        if datos.get('destacado') and not datos.get('activo'):
            self.add_error(
                'destacado',
                'Un servicio inactivo no puede ser destacado. '
                'Márquelo como activo o quite «destacado».',
            )
        nombre = datos.get('nombre')
        categoria = datos.get('categoria')
        if nombre and categoria:
            existentes = (
                Servicio.objects.filter(categoria=categoria)
                .exclude(pk=self.instance.pk)
                .values_list('nombre', flat=True)
            )
            if any(otro.casefold() == nombre.casefold() for otro in existentes):
                self.add_error(
                    'nombre',
                    f'Ya existe un servicio con ese nombre en la categoría «{categoria.nombre}».',
                )
        return datos