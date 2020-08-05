from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .check import views

urlpatterns = [
    path('check/', views.check),
    path('check/clear', views.clear_database),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

