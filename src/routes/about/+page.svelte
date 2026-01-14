<script>
  import { onMount } from 'svelte';
  
  // Company timeline
  const timelineEvents = [
    {
      year: 1988,
      title: "Débuts dans l'Industrie Métallique",
      description: "Notre fondateur commence sa carrière dans l'industrie de la métallurgie, acquérant une solide expérience technique."
    },
    {
      year: 2016,
      title: "Création de TC PLIAGE",
      description: "Fondation de notre entreprise familiale spécialisée dans la fabrication de pièces métalliques à Portet-Sur-Garonne."
    },
    {
      year: 2018,
      title: "Développement du Service d'Urgence",
      description: "Mise en place de notre service de fabrication express 24h/24 pour répondre aux besoins urgents des chantiers."
    },
    {
      year: 2020,
      title: "Acquisition d'Équipements Dernière Génération",
      description: "Investissement dans des machines à commande numérique pour augmenter notre précision et notre capacité de production."
    },
    {
      year: 2023,
      title: "Extension de l'Atelier",
      description: "Agrandissement de nos installations pour mieux répondre à la demande croissante et améliorer nos délais de production."
    }
  ];
  
  // Team members
  const teamMembers = [
    {
      name: "Thomas Durand",
      position: "Fondateur & Directeur",
      bio: "Fort de plus de 30 ans d'expérience dans l'industrie métallique, Thomas a fondé TC PLIAGE avec la vision d'offrir un service réactif et de qualité.",
      image: "/team/director.jpg"
    },
    {
      name: "Sophie Martin",
      position: "Responsable Production",
      bio: "Sophie supervise tous les aspects de la production, garantissant la qualité et le respect des délais pour chaque commande.",
      image: "/team/production.jpg"
    },
    {
      name: "Jean Leclerc",
      position: "Expert Technique",
      bio: "Jean apporte son expertise technique pour résoudre les défis les plus complexes et assurer la faisabilité de chaque projet.",
      image: "/team/technical.jpg"
    },
    {
      name: "Marie Dubois",
      position: "Service Client",
      bio: "Marie est le premier point de contact pour nos clients, coordonnant les demandes et assurant un suivi personnalisé.",
      image: "/team/customer-service.jpg"
    }
  ];
  
  // Values
  const values = [
    {
      title: "Réactivité",
      description: "Nous nous engageons à répondre rapidement à vos besoins, particulièrement dans les situations d'urgence.",
      icon: "bolt"
    },
    {
      title: "Excellence",
      description: "La qualité et la précision sont au cœur de notre travail, dans chaque pièce que nous fabriquons.",
      icon: "award"
    },
    {
      title: "Innovation",
      description: "Nous investissons continuellement dans les technologies et techniques les plus récentes.",
      icon: "lightbulb"
    },
    {
      title: "Proximité",
      description: "Nous cultivons des relations de confiance avec nos clients pour mieux comprendre et satisfaire leurs besoins.",
      icon: "handshake"
    }
  ];
  
  // Gallery images
  const galleryImages = [
    "/gallery/workshop1.jpg",
    "/gallery/production1.jpg",
    "/gallery/machine1.jpg",
    "/gallery/team1.jpg",
    "/gallery/product1.jpg",
    "/gallery/workshop2.jpg"
  ];
  
  // Counter for animation
  let counters = {
    years: 0,
    clients: 0,
    projects: 0,
    team: 0
  };
  
  // Target values for counters
  const targetCounters = {
    years: 7,
    clients: 500,
    projects: 2000,
    team: 12
  };
  
  onMount(() => {
    // Animate counters
    const duration = 2000;
    const step = 20;
    
    for (const key in targetCounters) {
      const target = targetCounters[key];
      const increment = target / (duration / step);
      
      let current = 0;
      const interval = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(interval);
        }
        counters[key] = Math.floor(current);
      }, step);
    }
  });
</script>

<!-- Hero Section -->
<section class="hero is-medium">
  <div class="hero-body">
    <div class="container">
      <div class="columns is-vcentered">
        <div class="column is-6">
          <h1 class="title is-1 hero-title">
            À Propos de<br>
            <span class="company-name">TC<span class="has-text-danger">PLIAGE</span></span>
          </h1>
          <div class="subtitle-line"></div>
          <p class="hero-description mb-5">
            Votre partenaire de confiance pour la fabrication métallique d'urgence. 
            Depuis 2016, notre équipe met son expertise au service de vos projets 
            les plus exigeants, avec une réactivité et une qualité constantes.
          </p>
          <div class="buttons">
            <a href="#our-story" class="button is-danger is-medium">
              <span>Notre Histoire</span>
              <span class="icon">
                <i class="fas fa-chevron-down"></i>
              </span>
            </a>
            <a href="/contact" class="button is-outlined is-medium">
              <span class="nous-contact-bt">Nous Contacter</span>
            </a>
          </div>
        </div>
        <div class="column is-6">
          <figure class="image about-image-container">
            <img src="/about/company-photo.jpg" alt="TC PLIAGE atelier" class="about-image">
          </figure>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Stats Banner -->
<section class="section stats-banner">
  <div class="container">
    <div class="columns is-multiline">
      <div class="column is-3-desktop is-6-tablet">
        <div class="stat-item">
          <div class="stat-number">+<span class="counter">{counters.years}</span></div>
          <div class="stat-label">Années d'Expérience</div>
        </div>
      </div>
      <div class="column is-3-desktop is-6-tablet">
        <div class="stat-item">
          <div class="stat-number">+<span class="counter">{counters.clients}</span></div>
          <div class="stat-label">Clients Satisfaits</div>
        </div>
      </div>
      <div class="column is-3-desktop is-6-tablet">
        <div class="stat-item">
          <div class="stat-number">+<span class="counter">{counters.projects}</span></div>
          <div class="stat-label">Projets Réalisés</div>
        </div>
      </div>
      <div class="column is-3-desktop is-6-tablet">
        <div class="stat-item">
          <div class="stat-number"><span class="counter">{counters.team}</span></div>
          <div class="stat-label">Membres d'Équipe</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Our Story Section -->
<section class="section our-story" id="our-story">
  <div class="container">
    <div class="columns">
      <div class="column is-10 is-offset-1">
        <h2 class="title is-2 has-text-centered section-title">Notre Histoire</h2>
        <div class="subtitle-line centered"></div>
        <p class="section-subtitle has-text-centered">
          Un parcours marqué par la passion du métal et l'excellence technique
        </p>
        
        <div class="timeline mt-6">
          {#each timelineEvents as event, index}
            <div class="timeline-item">
              <div class="timeline-year">
                <span>{event.year}</span>
              </div>
              <div class="timeline-content">
                <h3 class="title is-4">{event.title}</h3>
                <p>{event.description}</p>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Values Section -->
<section class="section values-section">
  <div class="container">
    <h2 class="title is-2 has-text-centered section-title">Nos Valeurs</h2>
    <div class="subtitle-line centered"></div>
    <p class="section-subtitle has-text-centered">
      Les principes qui guident nos actions au quotidien
    </p>
    
    <div class="columns is-multiline mt-6">
      {#each values as value}
        <div class="column is-3-desktop is-6-tablet">
          <div class="value-card">
            <div class="value-icon">
              <span class="icon">
                <i class="fas fa-{value.icon}"></i>
              </span>
            </div>
            <h3 class="title is-4">{value.title}</h3>
            <p>{value.description}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Mission Section -->
<section class="section mission-section">
  <div class="container">
    <div class="columns is-vcentered">
      <div class="column is-6">
        <h2 class="title is-2 section-title">Notre Mission</h2>
        <div class="subtitle-line"></div>
        <p class="section-subtitle">
          Conjuguer réactivité et qualité pour vos projets métalliques
        </p>
        
        <div class="content mission-content">
          <p>
            La mission de TC PLIAGE est d'offrir des solutions de fabrication métallique 
            réactives et de haute qualité, répondant aux besoins urgents des professionnels 
            du bâtiment et de l'industrie.
          </p>
          <p>
            Nous nous engageons à:
          </p>
          <ul>
            <li><strong>Répondre aux urgences</strong> avec un service disponible 24h/24 et 7j/7</li>
            <li><strong>Garantir la qualité</strong> de chaque pièce sortant de notre atelier</li>
            <li><strong>Adapter nos services</strong> aux exigences spécifiques de chaque projet</li>
            <li><strong>Innover constamment</strong> pour améliorer nos processus et nos produits</li>
          </ul>
          <p>
            Cette mission guide chacune de nos actions et nous pousse à constamment élever 
            nos standards pour satisfaire et dépasser les attentes de nos clients.
          </p>
        </div>
      </div>
      <div class="column is-6">
        <figure class="image mission-image-container">
          <img src="/about/mission-image.jpg" alt="Notre mission" class="mission-image">
        </figure>
      </div>
    </div>
  </div>
</section>

<!-- Team Section -->
<section class="section team-section">
  <div class="container">
    <h2 class="title is-2 has-text-centered section-title">Notre Équipe</h2>
    <div class="subtitle-line centered"></div>
    <p class="section-subtitle has-text-centered">
      Des professionnels passionnés à votre service
    </p>
    
    <div class="columns is-multiline mt-6">
      {#each teamMembers as member}
        <div class="column is-3-desktop is-6-tablet">
          <div class="team-card">
            <div class="team-photo-container">
              <img src={member.image} alt={member.name} class="team-photo">
              <div class="team-overlay"></div>
            </div>
            <div class="team-info">
              <h3 class="title is-4">{member.name}</h3>
              <p class="team-position">{member.position}</p>
              <p class="team-bio">{member.bio}</p>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Workshop Gallery -->
<section class="section gallery-section">
  <div class="container">
    <h2 class="title is-2 has-text-centered section-title">Notre Atelier</h2>
    <div class="subtitle-line centered"></div>
    <p class="section-subtitle has-text-centered">
      Découvrez notre environnement de travail et nos équipements
    </p>
    
    <div class="columns is-multiline mt-6">
      {#each galleryImages as image, index}
        <div class="column is-4-desktop is-6-tablet">
          <div class="gallery-item">
            <a href={image} target="_blank" class="gallery-link">
              <img src={image} alt="Atelier TC PLIAGE" loading="lazy">
              <div class="gallery-overlay">
                <span class="icon">
                  <i class="fas fa-search-plus"></i>
                </span>
              </div>
            </a>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="section cta-section">
  <div class="container">
    <div class="cta-content">
      <h2 class="title is-2 has-text-white">Prêt à Collaborer avec Nous ?</h2>
      <p class="subtitle is-4 has-text-white">
        Confiez-nous vos projets de fabrication métallique et bénéficiez de notre expertise
      </p>
      <div class="buttons is-centered mt-6">
        <a href="/contact" class="button is-danger is-large">
          <span>Contactez-nous</span>
          <span class="icon">
            <i class="fas fa-arrow-right"></i>
          </span>
        </a>
        <a href="/services" class="button is-white is-outlined is-large">
          <span>Découvrir nos Services</span>
        </a>
      </div>
    </div>
  </div>
</section>

<style>
  /* Hero Section */
  .hero.is-medium {
    background: linear-gradient(135deg, var(--bg-white), var(--bg-light)) !important;
    padding: 6rem 1.5rem !important;
    position: relative;
    overflow: hidden;
  }
  
  .hero.is-medium::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 20% 80%, rgba(229, 57, 53, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, rgba(46, 64, 87, 0.1) 0%, transparent 50%);
    z-index: 1;
  }
  
  .hero-body {
    position: relative;
    z-index: 2;
  }
  
  .hero-title {
    font-size: 3.5rem !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    margin-bottom: 1.5rem !important;
    color: var(--dark) !important;
  }
  
  .company-name {
    display: inline-block;
    background: linear-gradient(135deg, var(--secondary), var(--primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 900 !important;
  }
  
  .subtitle-line {
    width: 80px;
    height: 4px;
    background: linear-gradient(to right, var(--primary), var(--secondary));
    margin: 1rem 0 1.5rem;
    border-radius: 2px;
  }
  
  .subtitle-line.centered {
    margin: 1rem auto 1.5rem;
  }
  
  .hero-description {
    font-size: 1.25rem !important;
    line-height: 1.6 !important;
    color: var(--text-light) !important;
    max-width: 600px;
  }
  
  .nous-contact-bt {
    font-weight: 600 !important;
    color: var(--dark) !important;
    transition: all var(--transition-normal);
  }

  .about-image-container {
    position: relative;
    border-radius: var(--radius-lg) !important;
    overflow: hidden;
    box-shadow: var(--shadow-lg) !important;
    transform: rotate(2deg);
    transition: all var(--transition-normal);
  }
  
  .about-image-container:hover {
    transform: rotate(0deg) scale(1.02);
    box-shadow: var(--shadow-xl) !important;
  }
  
  .about-image {
    width: 100%;
    height: auto;
    transition: all var(--transition-slow);
  }
  
  /* Stats Banner */
  .stats-banner {
    background: linear-gradient(135deg, var(--secondary), var(--secondary-dark)) !important;
    color: white !important;
    padding: 4rem 1.5rem !important;
    position: relative;
    overflow: hidden;
  }
  
  .stats-banner::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="60" r="1" fill="rgba(255,255,255,0.05)"/><circle cx="70" cy="30" r="1.5" fill="rgba(255,255,255,0.05)"/></svg>');
    z-index: 1;
  }
  
  .stats-banner .container {
    position: relative;
    z-index: 2;
  }
  
  .stat-item {
    text-align: center;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(255, 255, 255, 0.2);
    transition: all var(--transition-normal);
    backdrop-filter: blur(10px);
  }
  
  .stat-item:hover {
    transform: translateY(-5px);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: var(--shadow-lg);
  }
  
  .stat-number {
    font-size: 3rem !important;
    font-weight: 800 !important;
    color: white !important;
    margin-bottom: 0.5rem !important;
    display: block;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  }
  
  .stat-label {
    font-size: 1rem !important;
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .counter {
    display: inline-block;
  }
  
  /* Our Story Section */
  .our-story {
    padding: 6rem 1.5rem !important;
    background: linear-gradient(to bottom, var(--bg-white), var(--bg-light)) !important;
  }
  
  .section-title {
    position: relative;
    display: inline-block;
    margin-bottom: 1rem !important;
  }
  
  .section-subtitle {
    font-size: 1.2rem !important;
    color: var(--text-light) !important;
    margin-bottom: 3rem !important;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }
  
  .timeline {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .timeline::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(to bottom, var(--primary), var(--secondary));
    transform: translateX(-50%);
    border-radius: 2px;
  }
  
  .timeline-item {
    display: flex;
    margin-bottom: 4rem;
    position: relative;
    align-items: center;
  }
  
  .timeline-item:nth-child(even) {
    flex-direction: row-reverse;
  }
  
  .timeline-year {
    flex: 0 0 120px;
    text-align: center;
    position: relative;
    z-index: 2;
  }
  
  .timeline-year span {
    display: inline-block;
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 50px;
    font-weight: 700;
    font-size: 1.1rem;
    box-shadow: var(--shadow-md);
    border: 4px solid white;
  }
  
  .timeline-content {
    flex: 1;
    background: white;
    padding: 2rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
    margin: 0 2rem;
    border: 1px solid var(--border-light);
    position: relative;
    transition: all var(--transition-normal);
  }
  
  .timeline-content:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
  }
  
  .timeline-content h3 {
    color: var(--dark) !important;
    margin-bottom: 1rem !important;
    font-size: 1.3rem !important;
  }
  
  .timeline-content p {
    color: var(--text-light) !important;
    line-height: 1.6;
    margin: 0 !important;
  }
  
  /* Arrow for timeline content */
  .timeline-item:nth-child(odd) .timeline-content::before {
    content: '';
    position: absolute;
    right: -10px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-left: 10px solid white;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
  }
  
  .timeline-item:nth-child(even) .timeline-content::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 50%;
    transform: translateY(-50%);
    width: 0;
    height: 0;
    border-right: 10px solid white;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
  }
  
  /* Values Section */
  .values-section {
    padding: 6rem 1.5rem !important;
    background: linear-gradient(135deg, var(--bg-light), white) !important;
    position: relative;
    overflow: hidden;
  }
  
  .values-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 80% 20%, rgba(229, 57, 53, 0.05) 0%, transparent 50%),
      radial-gradient(circle at 20% 80%, rgba(33, 150, 243, 0.05) 0%, transparent 50%);
    z-index: 1;
  }
  
  .values-section .container {
    position: relative;
    z-index: 2;
  }
  
  .value-card {
    background: linear-gradient(135deg, white, var(--bg-light));
    padding: 2.5rem 2rem !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
    text-align: center;
    height: 100%;
    transition: all var(--transition-normal);
    border: 1px solid var(--border-light);
    position: relative;
    overflow: hidden;
  }
  
  .value-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(to right, var(--primary), var(--info));
    transform: scaleX(0);
    transition: transform var(--transition-normal);
  }
  
  .value-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-lg) !important;
  }
  
  .value-card:hover::before {
    transform: scaleX(1);
  }
  
  .value-icon {
    margin-bottom: 1.5rem;
    color: var(--primary) !important;
    transition: all var(--transition-normal);
  }
  
  .value-card:hover .value-icon {
    transform: scale(1.1);
    color: var(--secondary) !important;
  }
  
  .value-card h3 {
    margin-bottom: 1rem !important;
    color: var(--dark) !important;
    font-size: 1.4rem !important;
  }
  
  .value-card p {
    color: var(--text-light) !important;
    line-height: 1.6;
    margin: 0 !important;
  }
  
  /* Mission Section */
  .mission-section {
    padding: 6rem 1.5rem !important;
    background: linear-gradient(to right, var(--bg-white), var(--bg-light)) !important;
  }
  
  .mission-content {
    background: white;
    padding: 2rem;
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border-left: 4px solid var(--primary);
  }
  
  .mission-content p {
    margin-bottom: 1.5rem !important;
    line-height: 1.7;
    color: var(--text) !important;
  }
  
  .mission-content ul {
    margin: 1.5rem 0 !important;
    padding-left: 0 !important;
    list-style: none !important;
  }
  
  .mission-content li {
    display: flex;
    align-items: flex-start;
    margin-bottom: 1rem;
    padding: 0.75rem 1rem;
    background-color: rgba(229, 57, 53, 0.05);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--primary);
  }
  
  .mission-content li::before {
    content: '✓';
    color: var(--primary);
    font-weight: bold;
    margin-right: 0.75rem;
    flex-shrink: 0;
  }
  
  .mission-image-container {
    position: relative;
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-lg);
    transform: rotate(-2deg);
    transition: all var(--transition-normal);
  }
  
  .mission-image-container:hover {
    transform: rotate(0deg) scale(1.02);
    box-shadow: var(--shadow-xl);
  }
  
  .mission-image {
    width: 100%;
    height: auto;
    transition: all var(--transition-slow);
  }
  
  /* Team Section */
  .team-section {
    padding: 6rem 1.5rem !important;
    background: linear-gradient(135deg, var(--bg-light), white) !important;
    position: relative;
    overflow: hidden;
  }
  
  .team-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(229, 57, 53, 0.03) 0%, transparent 50%),
      radial-gradient(circle at 90% 80%, rgba(46, 64, 87, 0.03) 0%, transparent 50%);
    z-index: 1;
  }
  
  .team-section .container {
    position: relative;
    z-index: 2;
  }
  
  .team-card {
    background: linear-gradient(135deg, white, var(--bg-light));
    border-radius: var(--radius-lg) !important;
    overflow: hidden;
    box-shadow: var(--shadow-md) !important;
    transition: all var(--transition-normal);
    height: 100%;
    border: 1px solid var(--border-light);
  }
  
  .team-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-lg) !important;
  }
  
  .team-photo-container {
    position: relative;
    height: 250px;
    overflow: hidden;
  }
  
  .team-photo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-slow);
  }
  
  .team-card:hover .team-photo {
    transform: scale(1.05);
  }
  
  .team-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.3) 0%, transparent 60%);
    opacity: 0;
    transition: opacity var(--transition-normal);
  }
  
  .team-card:hover .team-overlay {
    opacity: 1;
  }
  
  .team-info {
    padding: 1.5rem !important;
    text-align: center;
  }
  
  .team-info h3 {
    margin-bottom: 0.5rem !important;
    color: var(--dark) !important;
    font-size: 1.3rem !important;
  }
  
  .team-position {
    color: var(--primary) !important;
    font-weight: 600 !important;
    margin-bottom: 1rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.9rem !important;
  }
  
  .team-bio {
    color: var(--text-light) !important;
    line-height: 1.6;
    font-size: 0.95rem !important;
    margin: 0 !important;
  }
  
  /* Gallery Section */
  .gallery-section {
    padding: 6rem 1.5rem !important;
    background: linear-gradient(to bottom, var(--bg-white), var(--bg-light)) !important;
  }
  
  .gallery-item {
    position: relative;
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
    transition: all var(--transition-normal);
    height: 200px;
    margin-bottom: 1.5rem;
  }
  
  .gallery-item:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
  }
  
  .gallery-link {
    display: block;
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    text-decoration: none;
  }
  
  .gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform var(--transition-slow);
  }
  
  .gallery-item:hover img {
    transform: scale(1.1);
  }
  
  .gallery-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(229, 57, 53, 0.8), rgba(46, 64, 87, 0.8));
    opacity: 0;
    transition: opacity var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.5rem;
  }
  
  .gallery-item:hover .gallery-overlay {
    opacity: 1;
  }
  
  /* CTA Section */
  .cta-section {
    background: linear-gradient(135deg, var(--secondary), var(--secondary-dark)) !important;
    color: white !important;
    padding: 6rem 1.5rem !important;
    position: relative;
    overflow: hidden;
  }
  
  .cta-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="60" r="1" fill="rgba(255,255,255,0.05)"/><circle cx="70" cy="30" r="1.5" fill="rgba(255,255,255,0.05)"/></svg>');
    z-index: 1;
  }
  
  .cta-content {
    text-align: center;
    position: relative;
    z-index: 2;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .cta-section .title {
    color: white !important;
    margin-bottom: 1rem !important;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  }
  
  .cta-section .subtitle {
    color: rgba(255, 255, 255, 0.9) !important;
    margin-bottom: 2rem !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
  }
  
  .cta-section .button.is-danger {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 1rem 2rem !important;
  }
  
  .cta-section .button.is-white.is-outlined {
    background-color: transparent !important;
    border-color: white !important;
    color: white !important;
    font-size: 1.1rem !important;
    padding: 1rem 2rem !important;
  }
  
  .cta-section .button.is-white.is-outlined:hover {
    background-color: white !important;
    color: var(--secondary) !important;
  }
  
  /* Responsive Design */
  @media screen and (max-width: 768px) {
    .hero-title {
      font-size: 2.5rem !important;
    }
    
    .hero-description {
      font-size: 1.1rem !important;
    }
    
    .about-image-container,
    .mission-image-container {
      transform: none;
      margin-bottom: 2rem;
    }
    
    .stats-banner {
      padding: 3rem 1rem !important;
    }
    
    .stat-number {
      font-size: 2.5rem !important;
    }
    
    .timeline::before {
      left: 20px;
    }
    
    .timeline-item {
      flex-direction: column !important;
      align-items: flex-start;
      padding-left: 60px;
    }
    
    .timeline-item:nth-child(even) {
      flex-direction: column !important;
    }
    
    .timeline-year {
      position: absolute;
      left: 0;
      top: 0;
    }
    
    .timeline-year span {
      padding: 0.75rem 1rem;
      font-size: 1rem;
    }
    
    .timeline-content {
      margin: 0;
      margin-top: 1rem;
    }
    
    .timeline-content::before {
      display: none;
    }
    
    .team-photo-container {
      height: 200px;
    }
    
    .gallery-item {
      height: 180px;
    }
    
    .value-card {
      padding: 2rem 1.5rem !important;
      margin-bottom: 1.5rem;
    }
    
    .mission-content {
      padding: 1.5rem;
    }
    
    .cta-section {
      padding: 4rem 1rem !important;
    }
    
    .cta-section .button {
      font-size: 1rem !important;
      padding: 0.75rem 1.5rem !important;
      margin: 0.5rem;
    }
  }
  
  /* Animation delays for staggered appearance */
  .value-card:nth-child(1) {
    animation-delay: 0s;
  }
  
  .value-card:nth-child(2) {
    animation-delay: 0.1s;
  }
  
  .value-card:nth-child(3) {
    animation-delay: 0.2s;
  }
  
  .value-card:nth-child(4) {
    animation-delay: 0.3s;
  }
  
  .team-card:nth-child(1) {
    animation-delay: 0s;
  }
  
  .team-card:nth-child(2) {
    animation-delay: 0.1s;
  }
  
  .team-card:nth-child(3) {
    animation-delay: 0.2s;
  }
  
  .team-card:nth-child(4) {
    animation-delay: 0.3s;
  }
  
  .gallery-item:nth-child(1) {
    animation-delay: 0s;
  }
  
  .gallery-item:nth-child(2) {
    animation-delay: 0.1s;
  }
  
  .gallery-item:nth-child(3) {
    animation-delay: 0.2s;
  }
  
  .gallery-item:nth-child(4) {
    animation-delay: 0.3s;
  }
  
  .gallery-item:nth-child(5) {
    animation-delay: 0.4s;
  }
  
  .gallery-item:nth-child(6) {
    animation-delay: 0.5s;
  }
  
  /* Add slide-up animation to elements */
  .value-card,
  .team-card,
  .gallery-item {
    animation: slideUp 0.6s ease-out both;
  }
</style>