# Vita Gestión

Sitio web de promoción con catálogo de servicios y panel de gestión para **Vita Gestión · administración de comunidades**.
Proyecto de la Evaluación Sumativa 4 de Programación Backend (Django 4.2 + SQLite).

## Qué incluye

- Portada con el contenido institucional de Vita Gestión.
- Catálogo público de servicios, con buscador y filtro por categoría.
- Panel de gestión (CRUD de categorías y servicios) protegido por login y permisos.
- Administrador de Django con ambos modelos registrados.
- Modelo relacional: una **Categoría** tiene muchos **Servicios**.

## Instalación

Requiere Python 3.11.

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_datos
python manage.py createsuperuser
python manage.py crear_perfiles --usuario gestor
python manage.py runserver
```

Abrir http://127.0.0.1:8000/

## Comandos propios

- `python manage.py cargar_datos`: carga las 2 categorías y los 16 servicios de la presentación. Se puede repetir sin duplicar.
- `python manage.py crear_perfiles`: crea el grupo «Gestores de contenido» con sus permisos. Con `--usuario NOMBRE` crea también un usuario gestor y pide la contraseña por consola.

## Rutas principales

| Ruta | Acceso |
| --- | --- |
| `/` y `/catalogo/` | Público |
| `/panel/servicios/` y `/panel/categorias/` | Login y permisos |
| `/admin/` | Staff |

## Pruebas

```bash
python manage.py test servicios
```

## Integrantes

René Arancibia
Gustavo Barrientos
Bella Marin

