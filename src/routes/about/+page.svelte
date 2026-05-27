<script>
  import { onMount } from 'svelte';

  let counters = $state({ years: 0, clients: 0, projects: 0, team: 0 });

  onMount(() => {
    const targets = { years: 7, clients: 500, projects: 2000, team: 12 };
    const duration = 1800;
    const step = 16;
    for (const [key, target] of Object.entries(targets)) {
      let current = 0;
      const inc = target / (duration / step);
      const id = setInterval(() => {
        current = Math.min(current + inc, target);
        counters[key] = Math.floor(current);
        if (current >= target) clearInterval(id);
      }, step);
    }
  });

  const timeline = [
    {
      year: 1988,
      title: "Débuts dans la métallurgie",
      desc: "Notre fondateur débute sa carrière dans l'industrie métallurgique, acquérant une solide expertise technique."
    },
    {
      year: 2016,
      title: "Création de TC PLIAGE",
      desc: "Fondation de l'entreprise à Portet-Sur-Garonne, spécialisée en fabrication de pièces métalliques."
    },
    {
      year: 2018,
      title: "Service d'urgence 24/7",
      desc: "Lancement de notre service de fabrication express pour répondre aux chantiers en urgence."
    },
    {
      year: 2020,
      title: "Nouvelles machines CNC",
      desc: "Investissement dans des équipements dernière génération pour plus de précision et de capacité."
    },
    {
      year: 2023,
      title: "Extension de l'atelier",
      desc: "Agrandissement de nos locaux pour répondre à la demande croissante de nos clients."
    }
  ];

  const values = [
    { title: "Réactivité", desc: "Disponible 24h/24, 7j/7 pour toutes vos urgences.", icon: "fas fa-bolt" },
    { title: "Excellence", desc: "Qualité et précision garanties à chaque fabrication.", icon: "fas fa-award" },
    { title: "Innovation", desc: "Équipements CNC de dernière génération.", icon: "fas fa-microchip" },
    { title: "Proximité", desc: "Un suivi personnalisé pour chaque client.", icon: "fas fa-handshake" }
  ];

  const team = [
    {
      name: "Thomas Durand",
      role: "Fondateur & Directeur",
      bio: "30 ans d'expérience dans l'industrie métallique.",
      img: "/team/director.jpg"
    },
    {
      name: "Sophie Martin",
      role: "Responsable Production",
      bio: "Supervise la qualité et les délais de chaque commande.",
      img: "/team/production.jpg"
    },
    {
      name: "Jean Leclerc",
      role: "Expert Technique",
      bio: "Résout les défis les plus complexes avec expertise.",
      img: "/team/technical.jpg"
    },
    {
      name: "Marie Dubois",
      role: "Service Client",
      bio: "Votre premier contact pour un suivi personnalisé.",
      img: "/team/customer-service.jpg"
    }
  ];

  const gallery = [
    "/gallery/workshop1.jpg",
    "/gallery/production1.jpg",
    "/gallery/machine1.jpg",
    "/gallery/team1.jpg",
    "/gallery/product1.jpg",
    "/gallery/workshop2.jpg"
  ];
</script>

<svelte:head>
  <title>À Propos — TC Pliage</title>
</svelte:head>

<!-- Hero -->
<section class="relative py-28 overflow-hidden">
  <div class="absolute inset-0">
    <img src="/about/company-photo.jpg" alt="" class="w-full h-full object-cover">
    <div class="absolute inset-0 bg-zinc-950/80"></div>
  </div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-4">
      <span class="w-8 h-px bg-red-500"></span>
      Notre histoire
    </span>
    <h1 class="text-5xl sm:text-6xl font-extrabold text-zinc-100 mb-4">
      À Propos de<br><span class="text-red-500">TC PLIAGE</span>
    </h1>
    <p class="text-lg text-zinc-300 max-w-2xl leading-relaxed">
      Depuis 2016, votre partenaire de confiance pour la fabrication métallique d'urgence et sur mesure.
    </p>
    <div class="flex flex-wrap gap-4 mt-8">
      <a
        href="#notre-histoire"
        class="bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded transition-colors"
      >
        Notre Histoire
      </a>
      <a
        href="/contact"
        class="border border-zinc-600 hover:border-zinc-400 text-zinc-300 hover:text-zinc-100 font-semibold px-6 py-3 rounded transition-colors"
      >
        Nous Contacter
      </a>
    </div>
  </div>
</section>

<!-- Stats -->
<section class="bg-zinc-900 border-y border-zinc-800 py-12">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-8">
      {#each [
        [counters.years, '+', "Années d'expérience"],
        [counters.clients, '+', "Clients satisfaits"],
        [counters.projects, '+', "Projets réalisés"],
        [counters.team, '', "Membres d'équipe"]
      ] as [val, pfx, label]}
        <div class="text-center">
          <div class="text-4xl font-extrabold text-red-500 mb-1">{pfx}{val}</div>
          <div class="text-zinc-400 text-sm uppercase tracking-wide">{label}</div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Timeline -->
<section class="py-20" id="notre-histoire">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Depuis 1988</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Notre Histoire</h2>
      <p class="text-zinc-400 mt-4">Un parcours marqué par la passion du métal et l'excellence technique.</p>
    </div>

    <div class="space-y-0">
      {#each timeline as event, i}
        <div class="flex gap-6">
          <div class="flex flex-col items-center">
            <div class="w-14 h-14 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold text-xs text-center leading-tight">
              {event.year}
            </div>
            {#if i < timeline.length - 1}
              <div class="w-px flex-1 bg-zinc-800 my-1" style="min-height: 2rem;"></div>
            {/if}
          </div>
          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex-1 mb-4 hover:border-zinc-600 transition-colors">
            <h3 class="text-zinc-100 font-semibold text-base mb-1">{event.title}</h3>
            <p class="text-zinc-400 text-sm leading-relaxed">{event.desc}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Values -->
<section class="py-20 bg-zinc-900/40">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Ce qui nous guide</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Nos Valeurs</h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each values as v}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center hover:border-zinc-600 transition-colors">
          <div class="w-12 h-12 bg-red-600/10 border border-red-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="{v.icon} text-red-500"></i>
          </div>
          <h3 class="text-zinc-100 font-semibold text-lg mb-2">{v.title}</h3>
          <p class="text-zinc-400 text-sm leading-relaxed">{v.desc}</p>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Mission -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
      <div>
        <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Notre raison d'être</span>
        <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2 mb-6">Notre Mission</h2>
        <p class="text-zinc-400 leading-relaxed mb-6">
          La mission de TC PLIAGE est d'offrir des solutions de fabrication métallique réactives et de haute qualité, répondant aux besoins urgents des professionnels du bâtiment et de l'industrie.
        </p>
        <ul class="space-y-3">
          {#each [
            "Répondre aux urgences 24h/24, 7j/7",
            "Garantir la qualité de chaque pièce fabriquée",
            "Adapter nos services aux exigences de chaque projet",
            "Innover pour améliorer continuellement nos procédés"
          ] as item}
            <li class="flex gap-3 items-start text-zinc-300 text-sm">
              <i class="fas fa-check text-red-500 mt-0.5 flex-shrink-0"></i>
              {item}
            </li>
          {/each}
        </ul>
      </div>
      <div class="rounded-xl overflow-hidden">
        <img src="/about/mission-image.jpg" alt="Mission TC Pliage" class="w-full h-80 object-cover">
      </div>
    </div>
  </div>
</section>

<!-- Team -->
<section class="py-20 bg-zinc-900/40">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Les experts</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Notre Équipe</h2>
      <p class="text-zinc-400 mt-4">Des professionnels passionnés à votre service.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each team as member}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-zinc-600 transition-colors group">
          <div class="h-48 overflow-hidden">
            <img
              src={member.img}
              alt={member.name}
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            >
          </div>
          <div class="p-5">
            <h3 class="text-zinc-100 font-semibold text-base">{member.name}</h3>
            <p class="text-red-500 text-xs font-medium uppercase tracking-wide mt-0.5 mb-2">{member.role}</p>
            <p class="text-zinc-400 text-sm leading-relaxed">{member.bio}</p>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Gallery -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Nos installations</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Notre Atelier</h2>
    </div>
    <div class="grid grid-cols-2 lg:grid-cols-3 gap-3">
      {#each gallery as img}
        <a href={img} target="_blank" class="block rounded-xl overflow-hidden aspect-video group relative">
          <img
            src={img}
            alt="Atelier TC Pliage"
            loading="lazy"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          >
          <div class="absolute inset-0 bg-zinc-950/0 group-hover:bg-zinc-950/40 transition-colors flex items-center justify-center">
            <i class="fas fa-search-plus text-white text-xl opacity-0 group-hover:opacity-100 transition-opacity"></i>
          </div>
        </a>
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
        <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mb-4">Prêt à Collaborer avec Nous ?</h2>
        <p class="text-zinc-400 text-lg mb-8 max-w-xl mx-auto">
          Confiez-nous vos projets de fabrication métallique et bénéficiez de notre expertise.
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <a
            href="/contact"
            class="bg-red-600 hover:bg-red-500 text-white font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            Contactez-nous
          </a>
          <a
            href="/services"
            class="border border-zinc-600 hover:border-zinc-400 text-zinc-300 hover:text-zinc-100 font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            Découvrir nos Services
          </a>
        </div>
      </div>
    </div>
  </div>
</section>
