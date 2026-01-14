<script>
  // Hardcoded services data
  import ServiceCard from '$lib/components/ServiceCard.svelte';
  const services = [
    {
    id: 'urgence',
    titre: "Fabrication d'Urgence",
    description: "Service disponible 24h/24 et 7j/7 pour répondre à vos besoins urgents en fabrication métallique.",
    image: '/services/emergency.jpg',  // Fixed
    caracteristiques: [
      { description: "Intervention rapide en 24h", order: 1 },
      { description: "Disponibilité 7j/7, 24h/24", order: 2 },
      { description: "Livraison express possible", order: 3 },
      { description: "Solutions adaptées aux chantiers", order: 4 }
    ]
  },
  {
    id: 'sur-mesure',
    titre: "Pièces Sur Mesure",
    description: "Fabrication de pièces métalliques personnalisées selon vos plans et spécifications exactes.",
    image: '/services/sur-mesure.jpg',  // OK
    caracteristiques: [
      { description: "Travail selon plans ou croquis", order: 1 },
      { description: "Haute précision de fabrication", order: 2 },
      { description: "Large choix de matériaux", order: 3 },
      { description: "Conseil technique personnalisé", order: 4 }
    ]
  },
  {
    id: 'couvertines',
    titre: "Couvertines",
    description: "Fabrication de couvertines métalliques pour la protection des acrotères et murets.",
    image: '/services/couvertines.jpg',  // OK
    caracteristiques: [
      { description: "Protection efficace contre les infiltrations", order: 1 },
      { description: "Finitions soignées et esthétiques", order: 2 },
      { description: "Adaptation à toutes dimensions", order: 3 },
      { description: "Différentes finitions disponibles", order: 4 }
    ]
  },
  {
    id: 'habillages',
    titre: "Habillages Métalliques",
    description: "Solutions d'habillage en métal pour façades, murs et éléments architecturaux.",
    image: '/services/habillages.jpg',  // OK
    caracteristiques: [
      { description: "Design contemporain", order: 1 },
      { description: "Solutions durables et résistantes", order: 2 },
      { description: "Multiples finitions possibles", order: 3 },
      { description: "Installation simple sur chantier", order: 4 }
    ]
  },
  {
    id: 'quincaillerie',
    titre: "Quincaillerie Spéciale",
    description: "Fabrication de quincaillerie métallique sur mesure pour vos projets spécifiques.",
    image: '/services/quincaillerie.jpg',  // OK
    caracteristiques: [
      { description: "Pièces sur mesure", order: 1 },
      { description: "Haute résistance", order: 2 },
      { description: "Finitions au choix", order: 3 },
      { description: "Adaptation à vos contraintes", order: 4 }
    ]
  }
  ];
</script>

<section class="hero is-medium is-dark">
  <div class="hero-body">
    <div class="container">
      <h1 class="title is-1">Nos Services</h1>
      <h2 class="subtitle">Solutions métalliques sur mesure pour tous vos projets</h2>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="content mb-6">
      <h2 class="title is-2 has-text-centered">Expertise Métallique à Votre Service</h2>
      <p class="subtitle has-text-centered">
        Découvrez notre gamme complète de services de fabrication métallique
      </p>
    </div>

    {#each services as service}
      <div class="service-card-container">
        <ServiceCard {service} />
      </div>
    {/each}

    <div class="has-text-centered mt-6">
      <a href="/contact" class="button is-danger is-large">
        <span>Demander un Devis</span>
        <span class="icon">
          <i class="fas fa-arrow-right"></i>
        </span>
      </a>
    </div>
  </div>
</section>

<style>
  /* Hero Section */

  .hero.is-medium.is-dark {
    background-image: url('/home-hero.jpg')!important;
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    padding: 8rem 1.5rem !important;
    position: relative;
    overflow: hidden;
  }

  .hero.is-medium.is-dark::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(167, 93, 91, 0.8), rgba(46, 64, 87, 0.8));
    z-index: 1;
  }

  .hero.is-medium.is-dark .hero-body {
    position: relative;
    z-index: 2;
  }

  .hero.is-medium.is-dark .title {
    color: white !important;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    margin-bottom: 1rem !important;
  }

  .hero.is-medium.is-dark .subtitle {
    color: rgba(255, 255, 255, 0.9) !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    font-size: 1.3rem !important;
    font-weight: 300 !important;
  }

  /* Main Services Section */
  .section {
    padding: 5rem 1.5rem !important;
    background: linear-gradient(to bottom, var(--bg-white), var(--bg-light)) !important;
    position: relative;
  }

  .section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
      radial-gradient(circle at 20% 80%, rgba(229, 57, 53, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(33, 150, 243, 0.03) 0%, transparent 50%);
    z-index: 1;
  }

  .section .container {
    position: relative;
    z-index: 2;
  }

  .section .title.is-2 {
    margin-bottom: 1rem !important;
    position: relative;
    display: inline-block;
  }

  .section .title.is-2::after {
    content: '';
    position: absolute;
    bottom: -0.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 80px;
    height: 4px;
    background: linear-gradient(to right, var(--primary), var(--secondary));
    border-radius: 2px;
  }

  .section .subtitle {
    color: var(--text-light) !important;
    font-size: 1.2rem !important;
    margin-bottom: 3rem !important;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  /* Loading States */
  .py-6 {
    padding: 3rem 0 !important;
  }

  .progress.is-danger {
    background-color: rgba(229, 57, 53, 0.2) !important;
  }

  .progress.is-danger::-webkit-progress-value {
    background-color: var(--primary) !important;
  }

  .progress.is-danger::-moz-progress-bar {
    background-color: var(--primary) !important;
  }

  /* Notification Messages */
  .notification.is-danger {
    background-color: rgba(244, 67, 54, 0.1) !important;
    border: 1px solid rgba(244, 67, 54, 0.3) !important;
    color: #C62828 !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 2rem !important;
  }

  .notification.is-warning {
    background-color: rgba(255, 152, 0, 0.1) !important;
    border: 1px solid rgba(255, 152, 0, 0.3) !important;
    color: #E65100 !important;
    border-radius: var(--radius-md) !important;
    margin-bottom: 2rem !important;
  }

  /* CTA Button */
  .has-text-centered.mt-6 {
    margin-top: 4rem !important;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, rgba(229, 57, 53, 0.05), rgba(33, 150, 243, 0.05));
    border-radius: var(--radius-xl);
    border: 2px solid rgba(229, 57, 53, 0.1);
  }

  .button.is-danger.is-large {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    font-size: 1.25rem !important;
    padding: 1.25rem 2.5rem !important;
    border-radius: var(--radius-md) !important;
    font-weight: 700 !important;
    transition: all var(--transition-normal) !important;
    box-shadow: var(--shadow-md) !important;
  }

  .button.is-danger.is-large:hover {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg) !important;
  }

  .button.is-danger.is-large .icon {
    margin-left: 0.75rem !important;
    transition: transform var(--transition-normal);
  }

  .button.is-danger.is-large:hover .icon {
    transform: translateX(3px);
  }

  /* Service Cards Enhancement */
  .service-card-container {
    margin-bottom: 3rem;
  }

  /* Animation for service cards */
  .service-card-container:nth-child(1) {
    animation: slideUp 0.6s ease-out;
  }

  .service-card-container:nth-child(2) {
    animation: slideUp 0.6s ease-out 0.1s both;
  }

  .service-card-container:nth-child(3) {
    animation: slideUp 0.6s ease-out 0.2s both;
  }

  .service-card-container:nth-child(4) {
    animation: slideUp 0.6s ease-out 0.3s both;
  }

  .service-card-container:nth-child(5) {
    animation: slideUp 0.6s ease-out 0.4s both;
  }

  /* Empty state styling */
  .notification.is-warning p {
    margin: 0 !important;
    font-size: 1.1rem;
    text-align: center;
  }

  /* Loading text styling */
  .has-text-centered p {
    font-size: 1.1rem;
    color: var(--text-light);
    margin-bottom: 1rem !important;
  }

  /* Responsive adjustments */
  @media screen and (max-width: 768px) {
    .hero.is-medium.is-dark {
      padding: 5rem 1rem !important;
      background-attachment: scroll;
    }

    .hero.is-medium.is-dark .title {
      font-size: 2.5rem !important;
    }

    .hero.is-medium.is-dark .subtitle {
      font-size: 1.1rem !important;
    }

    .section {
      padding: 3rem 1rem !important;
    }

    .section .title.is-2 {
      font-size: 2rem !important;
    }

    .section .subtitle {
      font-size: 1.1rem !important;
    }

    .has-text-centered.mt-6 {
      padding: 2rem 1rem;
      margin-top: 2rem !important;
    }

    .button.is-danger.is-large {
      font-size: 1.1rem !important;
      padding: 1rem 2rem !important;
      width: 100%;
    }
  }

  /* Page transition effects */
  .section {
    animation: fadeIn 0.8s ease-out;
  }

  .hero.is-medium.is-dark {
    animation: slideDown 0.8s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Focus improvements for accessibility */
  .button:focus {
    outline: 3px solid rgba(229, 57, 53, 0.4) !important;
    outline-offset: 2px !important;
  }

  /* Print styles */
  @media print {
    .hero.is-medium.is-dark {
      background: var(--secondary) !important;
      color: white !important;
      padding: 2rem !important;
    }

    .section::before {
      display: none;
    }

    .button {
      display: none !important;
    }
  }
</style>