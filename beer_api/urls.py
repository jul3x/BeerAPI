from django.urls import path
from .check import views


urlpatterns = [
    path('check/', views.check),
]
