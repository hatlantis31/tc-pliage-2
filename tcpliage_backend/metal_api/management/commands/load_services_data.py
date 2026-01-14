from django.core.management.base import BaseCommand
from metal_api.models import Service, ServiceCharacteristic


class Command(BaseCommand):
    help = 'Load initial services data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading services data...')

        # Create services
        services_data = [
            {
                'id': 'urgence',
                'titre': "Fabrication d'Urgence",
                'description': "Service disponible 24h/24 et 7j/7 pour répondre à vos besoins urgents en fabrication métallique.",
                'caracteristiques': [
                    "Intervention rapide en 24h",
                    "Disponibilité 7j/7, 24h/24",
                    "Livraison express possible",
                    "Solutions adaptées aux chantiers"
                ]
            },
            {
                'id': 'sur-mesure',
                'titre': "Pièces Sur Mesure",
                'description': "Fabrication de pièces métalliques personnalisées selon vos plans et spécifications exactes.",
                'caracteristiques': [
                    "Travail selon plans ou croquis",
                    "Haute précision de fabrication",
                    "Large choix de matériaux",
                    "Conseil technique personnalisé"
                ]
            },
            {
                'id': 'couvertines',
                'titre': "Couvertines",
                'description': "Fabrication de couvertines métalliques pour la protection des acrotères et murets.",
                'caracteristiques': [
                    "Protection efficace contre les infiltrations",
                    "Finitions soignées et esthétiques",
                    "Adaptation à toutes dimensions",
                    "Différentes finitions disponibles"
                ]
            },
            {
                'id': 'habillages',
                'titre': "Habillages Métalliques",
                'description': "Solutions d'habillage en métal pour façades, murs et éléments architecturaux.",
                'caracteristiques': [
                    "Design contemporain",
                    "Solutions durables et résistantes",
                    "Multiples finitions possibles",
                    "Installation simple sur chantier"
                ]
            },
            {
                'id': 'quincaillerie',
                'titre': "Quincaillerie Spéciale",
                'description': "Fabrication de quincaillerie métallique sur mesure pour vos projets spécifiques.",
                'caracteristiques': [
                    "Pièces sur mesure",
                    "Haute résistance",
                    "Finitions au choix",
                    "Adaptation à vos contraintes"
                ]
            }
        ]

        for service_data in services_data:
            caracteristiques = service_data.pop('caracteristiques')
            service, created = Service.objects.update_or_create(
                id=service_data['id'],
                defaults=service_data
            )

            # Clear existing characteristics and create new ones
            ServiceCharacteristic.objects.filter(service=service).delete()
            for i, description in enumerate(caracteristiques):
                ServiceCharacteristic.objects.create(
                    service=service,
                    description=description,
                    order=i+1
                )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully loaded {len(services_data)} services with their characteristics'))
