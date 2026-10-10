from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('salir/', LogoutView.as_view(), name='salir'),   # cierre de sesión (POST)
    path('', include('servicios.urls')),
]