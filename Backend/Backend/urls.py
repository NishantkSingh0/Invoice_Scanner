from django.contrib import admin
from django.urls import path
from .views import render

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Render/', render),
]