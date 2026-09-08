<script>
  import { enhance } from '$app/forms';
  let { form } = $props();
  let loading = $state(false);
</script>

<svelte:head>
  <title>Créer un compte — TC Pliage</title>
</svelte:head>

<div class="relative min-h-[calc(100vh-4rem)] grid lg:grid-cols-2 overflow-hidden">

  <!-- Left side — visual panel -->
  <div class="hidden lg:block relative overflow-hidden">
    <img src="/gallery/production1.jpg" alt="" class="absolute inset-0 w-full h-full object-cover">
    <div class="absolute inset-0 bg-gradient-to-br from-zinc-950/90 via-zinc-950/70 to-red-950/50"></div>
    <div class="relative h-full flex flex-col justify-between p-12 z-10">
      <a href="/" class="flex items-center gap-2 text-zinc-300 hover:text-zinc-100 transition-colors text-sm">
        <i class="fas fa-arrow-left text-xs"></i>
        Retour au site
      </a>
      <div>
        <p class="text-red-400 text-xs font-semibold uppercase tracking-[0.2em] mb-3">Programme fidélité</p>
        <h2 class="text-4xl font-bold text-white leading-tight mb-4">Plus vous commandez,<br>plus vous économisez.</h2>
        <p class="text-zinc-300 text-base leading-relaxed max-w-md mb-8">
          Créez votre compte gratuitement pour sauvegarder vos pièces, suivre vos devis et débloquer des remises automatiques.
        </p>
        <div class="space-y-2">
          {#each [
            ['fas fa-history',  'Historique complet de vos demandes'],
            ['fas fa-percent',  'Remises fidélité automatiques (jusqu\'à −10%)'],
            ['fas fa-bolt',     'Pré-remplissage du formulaire de devis']
          ] as [icon, text]}
            <div class="flex items-center gap-3 text-zinc-300 text-sm">
              <div class="w-7 h-7 rounded-lg bg-red-600/20 border border-red-600/30 flex items-center justify-center flex-shrink-0">
                <i class="{icon} text-red-400 text-xs"></i>
              </div>
              {text}
            </div>
          {/each}
        </div>
      </div>
      <p class="text-xs text-zinc-500">© TC Pliage — Fabrication métallique sur mesure</p>
    </div>
  </div>

  <!-- Right side — form -->
  <div class="flex items-center justify-center px-4 py-16 bg-zinc-950 overflow-y-auto">
  <div class="w-full max-w-md">

    <div class="text-center mb-8">
      <a href="/">
        <img src="/logo.jpg" alt="TC Pliage" class="h-10 w-auto mx-auto mb-5 brightness-0 invert opacity-80">
      </a>
      <h1 class="text-2xl font-bold text-zinc-100 tracking-tight">Créer un compte</h1>
      <p class="text-zinc-500 text-sm mt-1">Suivez vos demandes et bénéficiez de remises fidélité</p>
    </div>

    <!-- Tier teaser -->
    <div class="grid grid-cols-3 gap-2 mb-6">
      {#each [
        ['Bronze', '0 €', '0%',  'bg-amber-900/30 border-amber-800/50 text-amber-400'],
        ['Argent', '500 €', '−5%', 'bg-zinc-800/60 border-zinc-600/50 text-zinc-300'],
        ['Or',     '2 000 €', '−10%', 'bg-yellow-900/30 border-yellow-700/50 text-yellow-400']
      ] as [tier, from, disc, cls]}
        <div class="border rounded-xl px-3 py-2.5 text-center {cls}">
          <p class="font-semibold text-xs">{tier}</p>
          <p class="text-xs opacity-70 mt-0.5">dès {from}</p>
          <p class="font-bold text-sm mt-1">{disc}</p>
        </div>
      {/each}
    </div>

    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl shadow-black/50">

      {#if form?.error}
        <div class="flex items-start gap-3 bg-red-950/40 border border-red-800/50 rounded-xl px-4 py-3 mb-6">
          <i class="fas fa-exclamation-circle text-red-400 mt-0.5 flex-shrink-0"></i>
          <p class="text-red-300 text-sm">{form.error}</p>
        </div>
      {/if}

      <form method="POST" use:enhance={() => {
        loading = true;
        return async ({ update }) => { loading = false; update(); };
      }} class="space-y-5">

        <div>
          <label for="name" class="block text-sm font-medium text-zinc-300 mb-2">Nom complet</label>
          <input id="name" name="name" type="text" required
            value={form?.name ?? ''}
            placeholder="Jean Dupont"
            autocomplete="name"
            class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-zinc-300 mb-2">Adresse email</label>
          <input id="email" name="email" type="email" required
            value={form?.email ?? ''}
            placeholder="votre@email.fr"
            autocomplete="email"
            class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-zinc-300 mb-2">
            Mot de passe
            <span class="text-zinc-600 font-normal ml-1">(8 caractères minimum)</span>
          </label>
          <input id="password" name="password" type="password" required minlength="8"
            placeholder="••••••••"
            autocomplete="new-password"
            class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
        </div>

        <button type="submit" disabled={loading}
          class="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg shadow-red-900/30 text-sm">
          {#if loading}
            <i class="fas fa-spinner fa-spin"></i> Création…
          {:else}
            <i class="fas fa-user-plus"></i> Créer mon compte
          {/if}
        </button>
      </form>
    </div>

    <p class="text-center text-sm text-zinc-500 mt-5">
      Déjà un compte ?
      <a href="/auth/login" class="text-red-400 hover:text-red-300 font-medium transition-colors">Se connecter</a>
    </p>
  </div>
  </div>
</div>
