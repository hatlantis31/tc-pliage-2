# metal_designer/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
import uuid
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Material, ShapeTemplate, Coating, Color, MetalDesign, ServiceCharacteristic, Service
from .serializers import (
    MaterialSerializer, ShapeTemplateSerializer, CoatingSerializer,
    ColorSerializer, MetalDesignCreateSerializer, MetalDesignDetailSerializer, 
    ServiceCharacteristicSerializer, ServiceSerializer
)

@csrf_exempt
def root(request):
    return HttpResponse("OK", content_type="text/plain")

@api_view(['GET'])
def shape_templates_list_view(request):
    """Return shape templates in the format expected by the frontend."""
    shapes = ShapeTemplate.objects.all()
    data = []

    for shape in shapes:
        data.append({
            'id': shape.id,
            'name': shape.name,
            'description': shape.description,
            'previewUrl': f'/images/shapes/{shape.id}.svg'
        })

    return Response(data)


@api_view(['GET'])
def materials_list_view(request):
    """Return materials in the format expected by the frontend."""
    materials = Material.objects.all()
    data = []

    for material in materials:
        data.append({
            'id': material.id,
            'name': material.name,
            'description': material.description,
            'density': material.density,
            'maxThickness': material.max_thickness,
            'minThickness': material.min_thickness,
            'image': request.build_absolute_uri(material.image.url) if material.image else f'/images/materials/{material.id}.jpg'
        })

    return Response(data)


@api_view(['GET'])
def finishes_for_material(request):
    """Return finishes for a material in the format expected by the frontend."""
    material_id = request.query_params.get('materialId')
    if not material_id:
        return Response({"error": "Material ID is required"}, status=400)

    # Common finish for all materials
    common_finishes = [{
        'id': 'none',
        'name': 'No Finish',
        'description': 'Raw metal without any coating or treatment',
        'compatibleWith': ['steel', 'aluminum', 'copper', 'brass']
    }]

    # Get compatible coatings
    coatings = Coating.objects.filter(compatible_materials__id=material_id)
    material_finishes = []

    for coating in coatings:
        compatible_materials = [
            m.id for m in coating.compatible_materials.all()]
        material_finishes.append({
            'id': coating.id,
            'name': coating.name,
            'description': coating.description,
            'compatibleWith': compatible_materials
        })

    return Response(common_finishes + material_finishes)


@api_view(['POST'])
def metal_piece_view(request):
    """Handle metal piece design submissions from the frontend."""
    data = request.data

    try:
        # Map frontend fields to backend models
        material_id = data.get('material')
        part_type = data.get('partType')

        # Get related objects
        try:
            material = Material.objects.get(id=material_id)
            shape_template = ShapeTemplate.objects.get(id=part_type)
        except (Material.DoesNotExist, ShapeTemplate.DoesNotExist) as e:
            return Response({
                'success': False,
                'error': 'Invalid material or shape template',
                'message': str(e)
            }, status=400)

        # Handle coating and color
        coating = None
        color = None
        if data.get('finish') and data.get('finish') != 'none':
            try:
                coating = Coating.objects.get(id=data.get('finish'))
            except Coating.DoesNotExist:
                pass

        if data.get('finishColor'):
            # Try to find a matching color or create a new one
            color_hex = data.get('finishColor')
            try:
                color = Color.objects.get(hex_code=color_hex)
            except Color.DoesNotExist:
                # Create a new color entry
                color = Color.objects.create(
                    id=f"custom-{uuid.uuid4().hex[:6]}",
                    name=f"Custom {color_hex}",
                    hex_code=color_hex
                )

        # Create the design
        design = MetalDesign.objects.create(
            material=material,
            shape_template=shape_template,
            shape_dimensions=data.get('dimensions', {}),
            cutouts=data.get('holes', []),
            coating=coating,
            color=color,
            notes=data.get('notes', ''),
            user=request.user if request.user.is_authenticated else None,
            status='pending'
        )

        # Generate a reference number
        ref_number = f"TCP-{timezone.now().strftime('%y%m%d')}-{design.id.hex[:6].upper()}"

        # Calculate estimated price based on material, dimensions, and features
        thickness = data.get('thickness', 2)
        dimensions = data.get('dimensions', {})
        holes = data.get('holes', [])

        # Base material cost calculation (simplistic approach)
        base_price = 15  # Fixed cost

        # Add material cost based on dimensions and thickness
        volume = 0
        if part_type == 'rectangle' and 'width' in dimensions and 'height' in dimensions:
            volume = dimensions['width'] * dimensions['height'] * \
                thickness / 1000  # volume in cm³
        elif part_type == 'circle' and 'diameter' in dimensions:
            radius = dimensions['diameter'] / 2
            volume = 3.14159 * radius * radius * thickness / 1000
        elif part_type == 'lShape' and all(k in dimensions for k in ['width', 'height', 'legWidth']):
            # L-shape area calculation
            width, height, leg_width = dimensions['width'], dimensions['height'], dimensions['legWidth']
            volume = ((width * leg_width) + (height * leg_width) -
                      (leg_width * leg_width)) * thickness / 1000

        # Material cost based on volume and material density
        material_cost = volume * material.density * \
            float(material.price_per_kg) / 1000

        # Add cost for holes
        hole_cost = len(holes) * 2  # $2 per hole

        # Add finish multiplier
        finish_multiplier = 1.0
        if coating:
            finish_multiplier = coating.price_factor

        total_cost = (base_price + material_cost +
                      hole_cost) * finish_multiplier

        # Ensure minimum price
        final_price = max(20, total_cost)

        # Calculate production time (days)
        production_time = 1  # Base time
        if coating:
            production_time += 0.5  # Additional time for coating
        if len(holes) > 0:
            # Time for holes, max 0.5 days
            production_time += min(0.5, len(holes) * 0.1)

        # Update the design with calculated values
        design.quoted_price = final_price
        design.estimated_production_time = production_time
        design.quoted_at = timezone.now()
        design.save()

        # Return response format matching frontend expectations
        return Response({
            'success': True,
            'message': 'Design submitted successfully',
            'referenceNumber': ref_number,
            'estimatedCost': float(design.quoted_price),
            'estimatedProductionDays': design.estimated_production_time,
            'design': data
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': 'Error processing design submission',
            'message': str(e)
        }, status=500)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing company services."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing materials."""
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class ShapeTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing shape templates."""
    queryset = ShapeTemplate.objects.all()
    serializer_class = ShapeTemplateSerializer


class CoatingViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing coatings."""
    queryset = Coating.objects.all()
    serializer_class = CoatingSerializer

    @action(detail=False, methods=['get'])
    def for_material(self, request):
        """List coatings compatible with a specific material."""
        material_id = request.query_params.get('material_id')
        if not material_id:
            return Response(
                {"error": "Material ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        coatings = Coating.objects.filter(compatible_materials__id=material_id)
        serializer = self.get_serializer(coatings, many=True)
        return Response(serializer.data)


class ColorViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing colors."""
    queryset = Color.objects.all()
    serializer_class = ColorSerializer


class MetalDesignViewSet(viewsets.ModelViewSet):
    """API endpoint for creating and managing metal designs."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Limit designs to the current user if authenticated."""
        user = self.request.user
        if user.is_authenticated:
            return MetalDesign.objects.filter(user=user)
        return MetalDesign.objects.none()

    def get_serializer_class(self):
        """Use different serializers for create and retrieve operations."""
        if self.action == 'create':
            return MetalDesignCreateSerializer
        return MetalDesignDetailSerializer

    def perform_create(self, serializer):
        """Set the user on design creation if authenticated."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
