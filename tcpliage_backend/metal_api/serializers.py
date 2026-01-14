# metal_designer/serializers.py
from rest_framework import serializers
from .models import Material, ShapeTemplate, Coating, Color, MetalDesign, ServiceCharacteristic, Service


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Material model."""
    class Meta:
        model = Material
        fields = '__all__'


class ShapeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ShapeTemplate model."""
    class Meta:
        model = ShapeTemplate
        fields = '__all__'


class ColorSerializer(serializers.ModelSerializer):
    """Serializer for Color model."""
    class Meta:
        model = Color
        fields = '__all__'


class CoatingSerializer(serializers.ModelSerializer):
    """Serializer for Coating model."""
    compatible_materials = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Coating
        fields = '__all__'


class MetalDesignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new metal design."""
    material_id = serializers.CharField(write_only=True)
    shape_template_id = serializers.CharField(write_only=True)
    coating_id = serializers.CharField(
        write_only=True, required=False, allow_null=True)
    color_id = serializers.CharField(
        write_only=True, required=False, allow_null=True)

    class Meta:
        model = MetalDesign
        fields = [
            'material_id', 'shape_template_id', 'shape_dimensions',
            'cutouts', 'coating_id', 'color_id', 'notes'
        ]

    def create(self, validated_data):
        material_id = validated_data.pop('material_id')
        shape_template_id = validated_data.pop('shape_template_id')
        coating_id = validated_data.pop('coating_id', None)
        color_id = validated_data.pop('color_id', None)

        # Get related objects
        material = Material.objects.get(id=material_id)
        shape_template = ShapeTemplate.objects.get(id=shape_template_id)
        coating = Coating.objects.get(id=coating_id) if coating_id else None
        color = Color.objects.get(id=color_id) if color_id else None

        # Create the design
        design = MetalDesign.objects.create(
            material=material,
            shape_template=shape_template,
            coating=coating,
            color=color,
            **validated_data
        )

        # Associate with the current user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            design.user = request.user
            design.save()

        return design


class ServiceCharacteristicSerializer(serializers.ModelSerializer):
    """Serializer for service characteristics."""
    class Meta:
        model = ServiceCharacteristic
        fields = ['description', 'order']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for services."""
    caracteristiques = ServiceCharacteristicSerializer(
        many=True, read_only=True)
    image = serializers.SerializerMethodField()  # This will now return the full URL

    class Meta:
        model = Service
        fields = ['id', 'titre', 'description', 'image', 'caracteristiques']
    
    def get_image(self, obj):
        """Return the full image URL or None."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    class Meta:
        model = Service
        fields = ['id', 'titre', 'description', 'image', 'caracteristiques']
        
        
class MetalDesignDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving metal design details."""
    material = MaterialSerializer(read_only=True)
    shape_template = ShapeTemplateSerializer(read_only=True)
    coating = CoatingSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    dimensions_display = serializers.ReadOnlyField(
        source='get_dimensions_display')
    cutout_count = serializers.ReadOnlyField()

    class Meta:
        model = MetalDesign
        fields = '__all__'
