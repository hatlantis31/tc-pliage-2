<script>
  const services = [
    {
      id: 'urgence',
      title: "Fabrication d'Urgence",
      desc: "Service disponible 24h/24 et 7j/7 pour répondre à vos besoins urgents en fabrication métallique. Nous garantissons une intervention rapide pour ne jamais bloquer vos chantiers.",
      img: '/services/emergency.jpg',
      icon: "fas fa-bolt",
      features: [
        "Intervention rapide en 24h",
        "Disponibilité 7j/7, 24h/24",
        "Livraison express possible",
        "Solutions adaptées aux chantiers"
      ]
    },
    {
      id: 'sur-mesure',
      title: "Pièces Sur Mesure",
      desc: "Fabrication de pièces métalliques personnalisées selon vos plans et spécifications exactes. Précision et qualité pour chaque commande, quelle que soit la complexité.",
      img: '/services/sur-mesure.jpg',
      icon: "fas fa-cogs",
      features: [
        "Travail selon plans ou croquis",
        "Haute précision de fabrication",
        "Large choix de matériaux",
        "Conseil technique personnalisé"
      ]
    },
    {
      id: 'couvertines',
      title: "Couvertines",
      desc: "Fabrication de couvertines métalliques pour la protection des acrotères et murets. Des finitions soignées pour assurer étanchéité et esthétique.",
      img: '/services/couvertines.jpg',
      icon: "fas fa-home",
      features: [
        "Protection contre les infiltrations",
        "Finitions soignées et esthétiques",
        "Adaptation à toutes dimensions",
        "Différentes finitions disponibles"
      ]
    },
    {
      id: 'habillages',
      title: "Habillages Métalliques",
      desc: "Solutions d'habillage en métal pour façades, murs et éléments architecturaux. Design contemporain et durabilité pour vos projets les plus exigeants.",
      img: '/services/habillages.jpg',
      icon: "fas fa-building",
      features: [
        "Design contemporain",
        "Solutions durables et résistantes",
        "Multiples finitions possibles",
        "Installation simple sur chantier"
      ]
    },
    {
      id: 'quincaillerie',
      title: "Quincaillerie Spéciale",
      desc: "Fabrication de quincaillerie métallique sur mesure pour vos projets spécifiques. Des pièces robustes adaptées à vos contraintes techniques et esthétiques.",
      img: '/services/quincaillerie.jpg',
      icon: "fas fa-wrench",
      features: [
        "Pièces entièrement sur mesure",
        "Haute résistance et durabilité",
        "Finitions au choix",
        "Adaptation à vos contraintes"
      ]
    }
  ];
</script>

<svelte:head>
  <title>Services — TC Pliage</title>
</svelte:head>

<!-- Hero -->
<section class="relative py-24 overflow-hidden">
  <div class="absolute inset-0">
    <img src="/services-hero.jpg" alt="" class="w-full h-full object-cover">
    <div class="absolute inset-0 bg-zinc-950/80"></div>
  </div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-4">
      <span class="w-8 h-px bg-red-500"></span>
      Ce que nous proposons
    </span>
    <h1 class="text-5xl sm:text-6xl font-extrabold text-zinc-100 mb-4">Nos Services</h1>
    <p class="text-lg text-zinc-300 max-w-2xl leading-relaxed">
      Solutions métalliques sur mesure pour tous vos projets. De l'urgence à la finition, nous couvrons l'ensemble de vos besoins.
    </p>
  </div>
</section>

<!-- Services list -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Expertise métallique</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Tout ce dont vous avez besoin</h2>
      <p class="text-zinc-400 mt-4 max-w-xl mx-auto">
        Découvrez notre gamme complète de services de fabrication métallique.
      </p>
    </div>

    <div class="space-y-8">
      {#each services as service, i}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden hover:border-zinc-600 transition-colors group">
          <div class="grid grid-cols-1 lg:grid-cols-2 {i % 2 !== 0 ? 'lg:grid-flow-dense' : ''}">

            <!-- Image -->
            <div class="h-64 lg:h-auto overflow-hidden {i % 2 !== 0 ? 'lg:col-start-2' : ''}">
              <img
                src={service.img}
                alt={service.title}
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              >
            </div>

            <!-- Content -->
            <div class="p-8 flex flex-col justify-center {i % 2 !== 0 ? 'lg:col-start-1 lg:row-start-1' : ''}">
              <div class="w-12 h-12 bg-red-600/10 border border-red-600/20 rounded-lg flex items-center justify-center mb-4 group-hover:bg-red-600 group-hover:border-red-600 transition-colors">
                <i class="{service.icon} text-red-500 group-hover:text-white transition-colors"></i>
              </div>
              <h3 class="text-2xl font-bold text-zinc-100 mb-3">{service.title}</h3>
              <p class="text-zinc-400 leading-relaxed mb-6">{service.desc}</p>
              <ul class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
                {#each service.features as feat}
                  <li class="flex gap-2 items-center text-zinc-300 text-sm">
                    <i class="fas fa-check text-red-500 flex-shrink-0 text-xs"></i>
                    {feat}
                  </li>
                {/each}
              </ul>
              <a
                href="/contact?service={service.id}"
                class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-5 py-2.5 rounded transition-colors self-start"
              >
                Demander un Devis
                <i class="fas fa-arrow-right text-sm"></i>
              </a>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- CTA -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="bg-zinc-900 border border-zinc-700 rounded-2xl p-8 sm:p-12 text-center relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-red-950/20 to-transparent pointer-events-none"></div>
      <div class="relative">
        <h2 class="text-3xl font-bold text-zinc-100 mb-4">Vous avez un projet ?</h2>
        <p class="text-zinc-400 text-lg mb-8 max-w-xl mx-auto">
          Contactez-nous pour obtenir un devis personnalisé. Notre équipe vous répond rapidement.
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <a
            href="/contact"
            class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            Demander un Devis
            <i class="fas fa-arrow-right"></i>
          </a>
          <a
            href="tel:0123456790"
            class="inline-flex items-center gap-2 border border-zinc-600 hover:border-zinc-400 text-zinc-300 hover:text-zinc-100 font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            <i class="fas fa-phone"></i>
            Appeler directement
          </a>
        </div>
      </div>
    </div>
  </div>
</section>
