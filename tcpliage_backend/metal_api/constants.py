# metal_api/constants.py
MATERIALS = {
    'acier': {
        'name': 'Acier',
        'price_multiplier': 1.0,
        'min_thickness': 0.5,
        'max_thickness': 10.0,
    },
    'aluminium': {
        'name': 'Aluminium',
        'price_multiplier': 1.5,
        'min_thickness': 0.3,
        'max_thickness': 8.0,
    },
    'inox': {
        'name': 'Inox',
        'price_multiplier': 2.0,
        'min_thickness': 0.4,
        'max_thickness': 6.0,
    }
}

SHAPES = {
    'rectangle': {
        'name': 'Rectangle',
        'preview_url': '/static/shapes/rectangle.svg',
        'dimensions': {
            'length': {'label': 'Longueur', 'min': 10, 'max': 1000, 'step': 1},
            'width': {'label': 'Largeur', 'min': 10, 'max': 1000, 'step': 1}
        }
    },
    'circle': {
        'name': 'Cercle',
        'preview_url': '/static/shapes/circle.svg',
        'dimensions': {
            'diameter': {'label': 'Diamètre', 'min': 10, 'max': 1000, 'step': 1}
        }
    }
}
