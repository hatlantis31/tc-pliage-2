from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'materials', views.MaterialViewSet)
router.register(r'shape-templates', views.ShapeTemplateViewSet)
router.register(r'coatings', views.CoatingViewSet)
router.register(r'colors', views.ColorViewSet)
router.register(r'metal-designs', views.MetalDesignViewSet,
                basename='metal-designs')
router.register(r'services', views.ServiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Frontend-specific endpoints
    path('metal-piece/', views.metal_piece_view, name='metal-piece'),
    path('materials-list/', views.materials_list_view, name='materials-list'),
    path('shapes-list/', views.shape_templates_list_view, name='shapes-list'),
    path('finishes-for-material/', views.finishes_for_material,
         name='finishes-for-material'),
]
