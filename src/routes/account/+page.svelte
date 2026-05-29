<script>
  let { data } = $props();

  const { user, totalSpend, tier, quotes } = data;

  const MATERIALS = {
    acier: 'Acier', galvanise: 'Acier galvanisé', aluminium: 'Aluminium', inox: 'Inox'
  };

  const STATUS = {
    pending:   { label: 'En attente',  cls: 'bg-amber-950/40 border-amber-700/40 text-amber-300' },
    validated: { label: 'Validé',      cls: 'bg-green-950/40 border-green-700/40 text-green-300' },
    cancelled: { label: 'Annulé',      cls: 'bg-zinc-800/60 border-zinc-700 text-zinc-500' }
  };

  const TIER_STYLES = {
    Bronze: 'bg-amber-950/40 border-amber-700/40 text-amber-300',
    Argent: 'bg-zinc-800/60 border-zinc-600 text-zinc-200',
    Or:     'bg-yellow-950/40 border-yellow-600/40 text-yellow-300'
  };

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  const progress = tier.nextThreshold
    ? Math.min(100, (totalSpend / tier.nextThreshold) * 100)
    : 100;
</script>

<svelte:head>
  <title>Mon compte — TC Pliage</title>
</svelte:head>

<!-- Header banner -->
<section class="relative border-b border-zinc-800/60 overflow-hidden">
  <div class="absolute inset-0 bg-gradient-to-br from-zinc-950 via-zinc-950 to-red-950/20 pointer-events-none"></div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex flex-wrap items-start justify-between gap-6">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 bg-red-600/15 border border-red-600/25 rounded-2xl flex items-center justify-center flex-shrink-0">
          <i class="fas fa-user text-red-400 text-xl"></i>
        </div>
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-zinc-100 tracking-tight">{user.name}</h1>
          <p class="text-zinc-500 text-sm mt-0.5">{user.email} · Membre depuis {formatDate(user.created_at)}</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="px-3 py-1.5 border rounded-xl text-sm font-semibold {TIER_STYLES[tier.name]}">
          {#if tier.name === 'Or'}<i class="fas fa-crown text-xs mr-1.5"></i>{/if}
          {tier.name}
          {#if tier.discount > 0}<span class="ml-1 opacity-80">−{tier.discount * 100}%</span>{/if}
        </span>
        <form method="POST" action="/auth/logout">
          <button type="submit"
            class="px-4 py-2 border border-zinc-700 hover:border-zinc-500 text-zinc-400 hover:text-zinc-200 rounded-xl text-sm transition-all">
            <i class="fas fa-sign-out-alt mr-1.5"></i>Déconnexion
          </button>
        </form>
      </div>
    </div>
  </div>
</section>

<section class="py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">

    <!-- Stats + tier progress -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Total spend -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
        <p class="text-xs text-zinc-500 uppercase tracking-wider mb-1">Dépenses cumulées</p>
        <p class="text-3xl font-bold text-zinc-100 tabular-nums">{totalSpend.toFixed(2)} <span class="text-xl text-zinc-400">€</span></p>
        <p class="text-xs text-zinc-600 mt-1">{quotes.filter(q => q.status !== 'cancelled').length} demande{quotes.length > 1 ? 's' : ''}</p>
      </div>

      <!-- Current tier -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
        <p class="text-xs text-zinc-500 uppercase tracking-wider mb-1">Niveau fidélité</p>
        <p class="text-3xl font-bold {tier.name === 'Or' ? 'text-yellow-400' : tier.name === 'Argent' ? 'text-zinc-200' : 'text-amber-400'}">{tier.name}</p>
        {#if tier.discount > 0}
          <p class="text-xs text-zinc-400 mt-1">Remise de <span class="font-semibold text-red-400">{tier.discount * 100}%</span> appliquée sur tous vos devis</p>
        {:else}
          <p class="text-xs text-zinc-600 mt-1">Atteignez 500 € pour bénéficier de −5%</p>
        {/if}
      </div>

      <!-- Discount saved -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
        <p class="text-xs text-zinc-500 uppercase tracking-wider mb-1">Économies réalisées</p>
        <p class="text-3xl font-bold text-green-400 tabular-nums">
          {(totalSpend * tier.discount / (1 - tier.discount)).toFixed(2)} <span class="text-xl text-green-600">€</span>
        </p>
        <p class="text-xs text-zinc-600 mt-1">grâce à votre remise {tier.name}</p>
      </div>
    </div>

    <!-- Tier progression -->
    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-zinc-200">Progression fidélité</h2>
        {#if tier.next}
          <span class="text-xs text-zinc-500">{totalSpend.toFixed(0)} € / {tier.nextThreshold} €</span>
        {:else}
          <span class="text-xs text-yellow-400">Niveau maximum atteint ✦</span>
        {/if}
      </div>
      <div class="flex items-center gap-3 mb-4">
        {#each [
          ['Bronze', '0 €',     'text-amber-400',  totalSpend >= 0],
          ['Argent', '500 €',   'text-zinc-300',   totalSpend >= 500],
          ['Or',     '2 000 €', 'text-yellow-400', totalSpend >= 2000]
        ] as [name, from, col, reached], i}
          <div class="flex flex-col items-center gap-1 flex-shrink-0">
            <div class="w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all {
              reached ? 'border-current bg-current/10 ' + col : 'border-zinc-700 text-zinc-600'
            }">
              {#if name === 'Or'}
                <i class="fas fa-crown text-xs {reached ? col : 'text-zinc-600'}"></i>
              {:else}
                <i class="fas fa-circle text-xs {reached ? col : 'text-zinc-600'}"></i>
              {/if}
            </div>
            <p class="text-xs {reached ? col : 'text-zinc-600'} font-medium">{name}</p>
            <p class="text-xs text-zinc-700">{from}</p>
          </div>
          {#if i < 2}
            <div class="flex-1 h-1.5 rounded-full overflow-hidden bg-zinc-800">
              {#if i === 0}
                <div class="h-full bg-gradient-to-r from-amber-600 to-zinc-400 rounded-full transition-all duration-500"
                  style="width: {totalSpend >= 500 ? 100 : Math.min(100, (totalSpend / 500) * 100)}%"></div>
              {:else}
                <div class="h-full bg-gradient-to-r from-zinc-400 to-yellow-500 rounded-full transition-all duration-500"
                  style="width: {totalSpend >= 2000 ? 100 : totalSpend < 500 ? 0 : Math.min(100, ((totalSpend - 500) / 1500) * 100)}%"></div>
              {/if}
            </div>
          {/if}
        {/each}
      </div>
      {#if tier.next}
        <p class="text-xs text-zinc-500">
          Encore <span class="text-zinc-300 font-semibold">{(tier.nextThreshold - totalSpend).toFixed(0)} €</span> pour atteindre le niveau
          <span class="font-semibold {tier.next === 'Or' ? 'text-yellow-400' : 'text-zinc-300'}">{tier.next}</span>
          {#if tier.next === 'Argent'}et bénéficier de <span class="text-red-400 font-semibold">−5%</span>{:else}et bénéficier de <span class="text-red-400 font-semibold">−10%</span>{/if}
        </p>
      {/if}
    </div>

    <!-- Quote history -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-zinc-100">Mes demandes</h2>
        <a href="/designer"
          class="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-red-900/30">
          <i class="fas fa-plus text-xs"></i>
          Nouvelle pièce
        </a>
      </div>

      {#if quotes.length === 0}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center">
          <div class="w-14 h-14 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-draw-polygon text-zinc-600 text-xl"></i>
          </div>
          <p class="text-zinc-400 font-medium mb-2">Aucune demande pour l'instant</p>
          <p class="text-zinc-600 text-sm mb-6">Concevez votre première pièce et demandez un devis.</p>
          <a href="/designer"
            class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded-xl transition-all">
            <i class="fas fa-draw-polygon"></i>
            Accéder au designer
          </a>
        </div>
      {:else}
        <div class="space-y-3">
          {#each quotes as q}
            {@const st = STATUS[q.status] ?? STATUS.pending}
            <div class="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-2xl p-5 transition-all">
              <div class="flex flex-wrap items-start justify-between gap-4">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-3 mb-2">
                    <span class="text-xs font-mono text-zinc-600">#{String(q.id).padStart(4, '0')}</span>
                    <span class="border text-xs px-2 py-0.5 rounded-lg {st.cls}">{st.label}</span>
                  </div>
                  <p class="text-zinc-100 font-semibold">
                    {MATERIALS[q.material] ?? q.material}
                    <span class="text-zinc-500 font-normal text-sm ml-1">
                      {q.total_length} × {q.width} × {q.thickness} mm
                    </span>
                  </p>
                  <div class="flex items-center gap-4 mt-2 text-xs text-zinc-600">
                    <span><i class="fas fa-angle-up mr-1"></i>{q.bends_count} pli{q.bends_count > 1 ? 's' : ''}</span>
                    {#if q.extras_count > 0}
                      <span><i class="fas fa-circle mr-1"></i>{q.extras_count} opération{q.extras_count > 1 ? 's' : ''}</span>
                    {/if}
                    {#if q.notes}
                      <span class="truncate max-w-xs"><i class="fas fa-comment mr-1"></i>{q.notes}</span>
                    {/if}
                  </div>
                </div>
                <div class="text-right flex-shrink-0">
                  <p class="text-xl font-bold text-zinc-100 tabular-nums">{q.estimated_cost.toFixed(2)} €</p>
                  <p class="text-xs text-zinc-600 mt-1">{formatDate(q.created_at)}</p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</section>
