# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from metal_api import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin  # Add this import
from metal_api.views import root
# Create a router and register viewsets

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('api/', include('metal_api.urls')),
    path('', root),
    # Add additional endpoints if needed
]

# Add this for serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)