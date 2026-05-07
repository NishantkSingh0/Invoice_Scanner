from django.contrib import admin
from django.urls import path
from .views import render, login, verify_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Render/', render),
    path('login/', login),
    path('verify-token/', verify_token),
]