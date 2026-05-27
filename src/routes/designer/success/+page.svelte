<svelte:head>
  <title>Confirmation — TC Pliage</title>
</svelte:head>

<section class="min-h-[60vh] flex items-center justify-center py-20">
  <div class="max-w-xl mx-auto px-4 text-center">
    <div class="w-16 h-16 bg-green-600/20 border border-green-600/30 rounded-full flex items-center justify-center mx-auto mb-6">
      <i class="fas fa-check text-green-400 text-2xl"></i>
    </div>
    <h1 class="text-3xl font-bold text-zinc-100 mb-4">Demande envoyée !</h1>
    <p class="text-zinc-400 leading-relaxed mb-8">
      Votre demande a bien été reçue. Notre équipe vous contactera dans les plus brefs délais.
    </p>
    <div class="flex flex-wrap justify-center gap-4">
      <a
        href="/"
        class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded transition-colors"
      >
        Retour à l'accueil
      </a>
      <a
        href="/contact"
        class="inline-flex items-center gap-2 border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 font-semibold px-6 py-3 rounded transition-colors"
      >
        Nous Contacter
      </a>
    </div>
  </div>
</section>
