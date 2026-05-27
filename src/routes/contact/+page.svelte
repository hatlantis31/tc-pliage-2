<script>
  import ContactForm from '$lib/components/ContactForm.svelte';

  let activeTab = $state('form');

  const hours = [
    { day: 'Lundi', hours: '5h – 19h' },
    { day: 'Mardi', hours: '5h – 19h' },
    { day: 'Mercredi', hours: '5h – 19h' },
    { day: 'Jeudi', hours: '5h – 19h' },
    { day: 'Vendredi', hours: '5h – 19h' },
    { day: 'Samedi', hours: 'Sur rendez-vous' },
    { day: 'Dimanche', hours: 'Urgences uniquement' }
  ];

  const faqs = [
    {
      q: "Quel est votre délai de fabrication en urgence ?",
      a: "Pour les commandes urgentes, nous garantissons une fabrication en 24h. Notre équipe est mobilisée pour traiter les demandes d'urgence en priorité."
    },
    {
      q: "Quels types de métaux travaillez-vous ?",
      a: "Nous travaillons principalement l'acier, l'aluminium, l'inox et le cuivre. Nos machines s'adaptent à toutes les épaisseurs selon vos besoins."
    },
    {
      q: "Comment obtenir un devis ?",
      a: "Contactez-nous par téléphone, email ou via notre formulaire en ligne. Pour les pièces complexes, notre outil de dessin en ligne est également disponible."
    },
    {
      q: "Livrez-vous dans toute la France ?",
      a: "Oui, nous livrons partout en France. Pour les commandes urgentes, nous proposons un service de livraison express."
    }
  ];
</script>

<svelte:head>
  <title>Contact — TC Pliage</title>
</svelte:head>

<!-- Hero -->
<section class="relative py-24 overflow-hidden">
  <div class="absolute inset-0">
    <img src="/contact/contact_hero.jpg" alt="" class="w-full h-full object-cover">
    <div class="absolute inset-0 bg-zinc-950/80"></div>
  </div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-4">
      <span class="w-8 h-px bg-red-500"></span>
      Parlons de votre projet
    </span>
    <h1 class="text-5xl sm:text-6xl font-extrabold text-zinc-100 mb-4">Contactez-nous</h1>
    <p class="text-lg text-zinc-300 max-w-xl leading-relaxed">
      Notre équipe est à votre écoute pour répondre à tous vos besoins en fabrication métallique.
    </p>
  </div>
</section>

<!-- Contact option cards -->
<section class="py-16">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center hover:border-red-800/60 transition-colors">
        <div class="w-12 h-12 bg-red-600/10 border border-red-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fas fa-phone-alt text-red-500"></i>
        </div>
        <h3 class="text-zinc-100 font-semibold text-lg mb-2">Service d'Urgence</h3>
        <p class="text-zinc-400 text-sm mb-5 leading-relaxed">Disponible 24h/24 et 7j/7 pour tous vos besoins urgents.</p>
        <a
          href="tel:0123456790"
          class="flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-5 py-2.5 rounded transition-colors text-sm"
        >
          <i class="fas fa-phone text-xs"></i>
          01 23 45 67 90
        </a>
      </div>

      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center hover:border-zinc-600 transition-colors">
        <div class="w-12 h-12 bg-zinc-800 border border-zinc-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fas fa-envelope text-zinc-400"></i>
        </div>
        <h3 class="text-zinc-100 font-semibold text-lg mb-2">Email & Devis</h3>
        <p class="text-zinc-400 text-sm mb-5 leading-relaxed">Pour les demandes de devis et renseignements généraux.</p>
        <a
          href="mailto:contact@tcpliage.fr"
          class="flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold px-5 py-2.5 rounded transition-colors text-sm"
        >
          <i class="fas fa-envelope text-xs"></i>
          contact@tcpliage.fr
        </a>
      </div>

      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center hover:border-zinc-600 transition-colors">
        <div class="w-12 h-12 bg-zinc-800 border border-zinc-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fas fa-map-marker-alt text-zinc-400"></i>
        </div>
        <h3 class="text-zinc-100 font-semibold text-lg mb-2">Visitez l'Atelier</h3>
        <p class="text-zinc-400 text-sm mb-5 leading-relaxed">3 Av. du Bois Vert, Portet-Sur-Garonne</p>
        <a
          href="https://maps.google.com?q=3+Avenue+du+Bois+Vert,+Portet-Sur-Garonne"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-semibold px-5 py-2.5 rounded transition-colors text-sm"
        >
          <i class="fas fa-directions text-xs"></i>
          Itinéraire
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Tabs: form / info -->
<section class="pb-16">
  <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">

    <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 mb-8 max-w-sm">
      <button
        onclick={() => activeTab = 'form'}
        class="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded text-sm font-medium transition-colors
          {activeTab === 'form' ? 'bg-red-600 text-white' : 'text-zinc-400 hover:text-zinc-100'}"
      >
        <i class="fas fa-paper-plane text-xs"></i>
        Formulaire
      </button>
      <button
        onclick={() => activeTab = 'info'}
        class="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded text-sm font-medium transition-colors
          {activeTab === 'info' ? 'bg-red-600 text-white' : 'text-zinc-400 hover:text-zinc-100'}"
      >
        <i class="fas fa-info-circle text-xs"></i>
        Informations
      </button>
    </div>

    {#if activeTab === 'form'}
      <div class="max-w-2xl">
        <h2 class="text-2xl font-bold text-zinc-100 mb-6">Envoyez-nous un Message</h2>
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 sm:p-8">
          <ContactForm />
        </div>
      </div>

    {:else}
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">

        <div class="space-y-6">
          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h3 class="text-zinc-100 font-semibold text-lg mb-5">Coordonnées</h3>
            <div class="space-y-4">
              <div class="flex gap-3 items-start text-sm">
                <i class="fas fa-map-marker-alt text-red-500 mt-0.5 flex-shrink-0 w-4"></i>
                <span class="text-zinc-300">3 Avenue du Bois Vert, Portet-Sur-Garonne, France</span>
              </div>
              <div class="flex gap-3 items-start text-sm">
                <i class="fas fa-phone text-red-500 mt-0.5 flex-shrink-0 w-4"></i>
                <div>
                  <a href="tel:0123456789" class="text-zinc-300 hover:text-zinc-100 transition-colors block">Standard : 01 23 45 67 89</a>
                  <a href="tel:0123456790" class="text-red-500 hover:text-red-400 font-medium transition-colors block">Urgence : 01 23 45 67 90</a>
                </div>
              </div>
              <div class="flex gap-3 items-start text-sm">
                <i class="fas fa-envelope text-red-500 mt-0.5 flex-shrink-0 w-4"></i>
                <a href="mailto:contact@tcpliage.fr" class="text-zinc-300 hover:text-zinc-100 transition-colors">contact@tcpliage.fr</a>
              </div>
            </div>
          </div>

          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
            <h3 class="text-zinc-100 font-semibold text-lg mb-5">Horaires d'Ouverture</h3>
            <div class="space-y-1">
              {#each hours as { day, hours: h }}
                <div class="flex justify-between text-sm py-2 border-b border-zinc-800 last:border-0">
                  <span class="text-zinc-300 font-medium">{day}</span>
                  <span class="text-zinc-400">{h}</span>
                </div>
              {/each}
            </div>
            <p class="mt-4 text-xs text-amber-500/80 flex gap-2 items-start">
              <i class="fas fa-exclamation-triangle mt-0.5 flex-shrink-0"></i>
              Service d'urgence disponible 24h/24 et 7j/7 en dehors des heures d'ouverture.
            </p>
          </div>
        </div>

        <div class="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <iframe
            width="100%"
            height="400"
            style="border:0"
            loading="lazy"
            allowfullscreen
            referrerpolicy="no-referrer-when-downgrade"
            title="Localisation TC Pliage"
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2889.9371526429886!2d1.4033!3d43.5356!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x12aebb7baf3310a3%3A0x1d4f860e16ef5296!2s3%20Av.%20du%20Bois%20Vert%2C%2031120%20Portet-sur-Garonne!5e0!3m2!1sfr!2sfr!4v1650000000000!5m2!1sfr!2sfr"
          ></iframe>
          <div class="p-4 flex gap-3">
            <a
              href="https://maps.google.com?q=3+Avenue+du+Bois+Vert,+Portet-Sur-Garonne"
              target="_blank"
              rel="noopener noreferrer"
              class="flex-1 flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-sm font-medium px-4 py-2.5 rounded transition-colors"
            >
              <i class="fas fa-directions"></i>
              Itinéraire
            </a>
            <a
              href="tel:0123456789"
              class="flex-1 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white text-sm font-medium px-4 py-2.5 rounded transition-colors"
            >
              <i class="fas fa-phone"></i>
              Appeler
            </a>
          </div>
        </div>
      </div>
    {/if}
  </div>
</section>

<!-- FAQ -->
<section class="py-16 bg-zinc-900/40">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-10">
      <span class="text-red-500 text-sm font-semibold uppercase tracking-widest">Aide</span>
      <h2 class="text-3xl font-bold text-zinc-100 mt-2">Questions Fréquentes</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      {#each faqs as faq}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-6 hover:border-zinc-600 transition-colors">
          <h3 class="text-zinc-100 font-semibold text-base mb-3">{faq.q}</h3>
          <p class="text-zinc-400 text-sm leading-relaxed">{faq.a}</p>
        </div>
      {/each}
    </div>

    <div class="text-center mt-8">
      <p class="text-zinc-400 text-sm mb-4">Vous avez d'autres questions ?</p>
      <a
        href="tel:0123456789"
        class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded transition-colors"
      >
        <i class="fas fa-phone text-sm"></i>
        Contactez-nous directement
      </a>
    </div>
  </div>
</section>
