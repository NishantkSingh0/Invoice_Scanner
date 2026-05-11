from django.contrib import admin
from django.urls import path
from .views import render, login, verify_token, render_csv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Render/', render),
    path('Render-CSV/', render_csv),
    path('login/', login),
    path('verify-token/', verify_token),
]