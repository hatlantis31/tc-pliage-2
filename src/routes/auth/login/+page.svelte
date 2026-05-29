<script>
  import { enhance } from '$app/forms';
  let { form } = $props();
  let loading = $state(false);
</script>

<svelte:head>
  <title>Connexion — TC Pliage</title>
</svelte:head>

<div class="relative min-h-[calc(100vh-4rem)] grid lg:grid-cols-2 overflow-hidden">

  <!-- Left side — visual panel -->
  <div class="hidden lg:block relative overflow-hidden">
    <img src="/gallery/workshop1.jpg" alt="" class="absolute inset-0 w-full h-full object-cover">
    <div class="absolute inset-0 bg-gradient-to-br from-zinc-950/90 via-zinc-950/70 to-red-950/50"></div>
    <div class="relative h-full flex flex-col justify-between p-12 z-10">
      <a href="/" class="flex items-center gap-2 text-zinc-300 hover:text-zinc-100 transition-colors text-sm">
        <i class="fas fa-arrow-left text-xs"></i>
        Retour au site
      </a>
      <div>
        <p class="text-red-400 text-xs font-semibold uppercase tracking-[0.2em] mb-3">Espace client</p>
        <h2 class="text-4xl font-bold text-white leading-tight mb-4">Suivez vos demandes,<br>de A à Z.</h2>
        <p class="text-zinc-300 text-base leading-relaxed max-w-md">
          Pilotez l'historique de vos devis, accédez à vos remises fidélité et obtenez vos pièces sur mesure plus vite.
        </p>
        <div class="flex items-center gap-3 mt-8">
          <span class="px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-700 text-zinc-300 text-xs">Bronze 0%</span>
          <span class="px-3 py-1.5 rounded-xl bg-zinc-800/80 border border-zinc-600 text-zinc-200 text-xs">Argent −5%</span>
          <span class="px-3 py-1.5 rounded-xl bg-yellow-950/60 border border-yellow-700/50 text-yellow-300 text-xs">
            <i class="fas fa-crown text-[10px] mr-1"></i>Or −10%
          </span>
        </div>
      </div>
      <p class="text-xs text-zinc-500">© TC Pliage — Fabrication métallique sur mesure</p>
    </div>
  </div>

  <!-- Right side — form -->
  <div class="flex items-center justify-center px-4 py-16 bg-zinc-950">
  <div class="w-full max-w-md">

    <!-- Logo / brand -->
    <div class="text-center mb-8">
      <a href="/">
        <img src="/logo.jpg" alt="TC Pliage" class="h-10 w-auto mx-auto mb-5 brightness-0 invert opacity-80">
      </a>
      <h1 class="text-2xl font-bold text-zinc-100 tracking-tight">Connexion</h1>
      <p class="text-zinc-500 text-sm mt-1">Accédez à votre espace client TC Pliage</p>
    </div>

    <!-- Card -->
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
          <label for="email" class="block text-sm font-medium text-zinc-300 mb-2">Adresse email</label>
          <input id="email" name="email" type="email" required
            value={form?.email ?? ''}
            placeholder="votre@email.fr"
            autocomplete="email"
            class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-zinc-300 mb-2">Mot de passe</label>
          <input id="password" name="password" type="password" required
            placeholder="••••••••"
            autocomplete="current-password"
            class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
        </div>

        <button type="submit" disabled={loading}
          class="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg shadow-red-900/30 text-sm">
          {#if loading}
            <i class="fas fa-spinner fa-spin"></i> Connexion…
          {:else}
            <i class="fas fa-sign-in-alt"></i> Se connecter
          {/if}
        </button>
      </form>
    </div>

    <p class="text-center text-sm text-zinc-500 mt-5">
      Pas encore de compte ?
      <a href="/auth/register" class="text-red-400 hover:text-red-300 font-medium transition-colors">Créer un compte</a>
    </p>
  </div>
  </div>
</div>
