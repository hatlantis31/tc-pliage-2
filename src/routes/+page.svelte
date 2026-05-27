<script>
  import { onMount } from 'svelte';

  const services = [
    {
      title: "Fabrication d'Urgence",
      desc: "Intervention en 24h pour tous vos besoins urgents de fabrication métallique. Disponible 24h/24 et 7j/7.",
      icon: "fas fa-bolt",
      href: "/services"
    },
    {
      title: "Pièces Sur Mesure",
      desc: "Découpe et pliage de métal selon vos plans et spécifications exactes. Large choix de matériaux.",
      icon: "fas fa-cogs",
      href: "/services"
    },
    {
      title: "Couvertines & Habillages",
      desc: "Protection et finition esthétique pour toitures, acrotères et façades. Multiples finitions disponibles.",
      icon: "fas fa-building",
      href: "/services"
    }
  ];

  const values = [
    { title: "Réactivité", desc: "Réponse dans les 24h, service d'urgence 24h/24 et 7j/7.", icon: "fas fa-bolt" },
    { title: "Précision", desc: "Fabrication haute précision, conforme à vos plans et croquis.", icon: "fas fa-drafting-compass" },
    { title: "Qualité", desc: "Pièces durables fabriquées avec des matériaux certifiés.", icon: "fas fa-award" },
    { title: "Proximité", desc: "Un interlocuteur dédié et un suivi personnalisé à chaque commande.", icon: "fas fa-handshake" }
  ];

  let counters = $state({ years: 0, clients: 0, projects: 0 });

  onMount(() => {
    const targets = { years: 7, clients: 500, projects: 2000 };
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
</script>

<svelte:head>
  <title>TC Pliage — Fabrication Métallique d'Urgence</title>
</svelte:head>

<!-- Hero -->
<section class="relative min-h-[85vh] flex items-center">
  <div class="absolute inset-0">
    <img src="/hero-background.jpg" alt="" class="w-full h-full object-cover">
    <div class="absolute inset-0 bg-zinc-950/75"></div>
  </div>

  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
    <div class="max-w-2xl">
      <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-4">
        <span class="w-8 h-px bg-red-500"></span>
        Disponible 24h/24 — 7j/7
      </span>
      <h1 class="text-5xl sm:text-6xl font-extrabold text-zinc-100 leading-tight mb-6">
        Fabrication<br>
        <span class="text-red-500">Métallique</span><br>
        Sur Mesure
      </h1>
      <p class="text-lg text-zinc-300 mb-8 leading-relaxed max-w-lg">
        Spécialiste de la découpe et du pliage de métal pour vos chantiers.
        Intervention d'urgence en 24h, qualité garantie.
      </p>
      <div class="flex flex-wrap gap-4">
        <a
          href="/contact"
          class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded transition-colors"
        >
          Demander un Devis
          <i class="fas fa-arrow-right text-sm"></i>
        </a>
        <a
          href="/services"
          class="inline-flex items-center gap-2 border border-zinc-600 hover:border-zinc-400 text-zinc-300 hover:text-zinc-100 font-semibold px-6 py-3 rounded transition-colors"
        >
          Nos Services
        </a>
      </div>
    </div>

    <!-- Emergency phone badge -->
    <div class="mt-12 inline-flex items-center gap-3 bg-zinc-900/80 border border-zinc-700 rounded-lg px-5 py-3">
      <div class="w-8 h-8 bg-red-600 rounded-full flex items-center justify-center flex-shrink-0">
        <i class="fas fa-phone text-white text-xs"></i>
      </div>
      <div>
        <p class="text-zinc-400 text-xs">Service d'urgence</p>
        <a href="tel:0123456790" class="text-zinc-100 font-semibold hover:text-red-400 transition-colors">
          01 23 45 67 90
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Stats -->
<section class="bg-zinc-900 border-y border-zinc-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-8">
      <div class="text-center">
        <div class="text-4xl font-extrabold text-red-500 mb-1">+{counters.years}</div>
        <div class="text-zinc-400 text-sm uppercase tracking-wide">Années d'expérience</div>
      </div>
      <div class="text-center">
        <div class="text-4xl font-extrabold text-red-500 mb-1">+{counters.clients}</div>
        <div class="text-zinc-400 text-sm uppercase tracking-wide">Clients satisfaits</div>
      </div>
      <div class="text-center">
        <div class="text-4xl font-extrabold text-red-500 mb-1">+{counters.projects}</div>
        <div class="text-zinc-400 text-sm uppercase tracking-wide">Projets réalisés</div>
      </div>
      <div class="text-center">
        <div class="text-4xl font-extrabold text-red-500 mb-1">24/7</div>
        <div class="text-zinc-400 text-sm uppercase tracking-wide">Disponibilité</div>
      </div>
    </div>
  </div>
</section>

<!-- Services preview -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Ce que nous faisons</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Nos Services</h2>
      <p class="text-zinc-400 mt-4 max-w-xl mx-auto">
        De la fabrication d'urgence aux pièces sur mesure, nous couvrons tous vos besoins en métallurgie.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      {#each services as s}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-600 transition-colors group">
          <div class="w-12 h-12 bg-red-950/40 border border-red-900/40 rounded-lg flex items-center justify-center mb-4 group-hover:bg-red-600 group-hover:border-red-600 transition-colors">
            <i class="{s.icon} text-red-400 group-hover:text-white transition-colors"></i>
          </div>
          <h3 class="text-zinc-100 font-semibold text-lg mb-2">{s.title}</h3>
          <p class="text-zinc-400 text-sm leading-relaxed mb-4">{s.desc}</p>
          <a
            href={s.href}
            class="text-red-500 hover:text-red-400 text-sm font-medium inline-flex items-center gap-1 transition-colors"
          >
            En savoir plus <i class="fas fa-arrow-right text-xs"></i>
          </a>
        </div>
      {/each}
    </div>

    <div class="text-center mt-8">
      <a
        href="/services"
        class="inline-flex items-center gap-2 border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 font-medium px-6 py-3 rounded transition-colors"
      >
        Voir tous nos services <i class="fas fa-arrow-right text-sm"></i>
      </a>
    </div>
  </div>
</section>

<!-- Values -->
<section class="py-20 bg-zinc-900/40">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Pourquoi nous choisir</span>
      <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mt-2">Nos Engagements</h2>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      {#each values as v}
        <div class="text-center p-6">
          <div class="w-14 h-14 bg-red-600/10 border border-red-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="{v.icon} text-red-500 text-lg"></i>
          </div>
          <h3 class="text-zinc-100 font-semibold text-lg mb-2">{v.title}</h3>
          <p class="text-zinc-400 text-sm leading-relaxed">{v.desc}</p>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- CTA banner -->
<section class="py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="bg-zinc-900 border border-zinc-700 rounded-2xl p-8 sm:p-12 text-center relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-red-950/20 to-transparent pointer-events-none"></div>
      <div class="relative">
        <h2 class="text-3xl sm:text-4xl font-bold text-zinc-100 mb-4">
          Besoin d'une fabrication urgente ?
        </h2>
        <p class="text-zinc-400 text-lg mb-8 max-w-xl mx-auto">
          Notre équipe est disponible 24h/24 pour répondre à vos demandes les plus urgentes.
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <a
            href="/contact"
            class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            Nous Contacter
          </a>
          <a
            href="tel:0123456790"
            class="inline-flex items-center gap-2 border border-zinc-600 hover:border-zinc-400 text-zinc-300 hover:text-zinc-100 font-semibold px-8 py-4 rounded text-lg transition-colors"
          >
            <i class="fas fa-phone"></i>
            01 23 45 67 90
          </a>
        </div>
      </div>
    </div>
  </div>
</section>
