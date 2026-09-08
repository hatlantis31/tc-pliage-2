<script>
  import { enhance } from '$app/forms';
  let { data } = $props();

  let tab = $state('quotes');
  let search = $state('');

  const MATERIALS = { acier: 'Acier', galvanise: 'Galvanisé', aluminium: 'Aluminium', inox: 'Inox' };
  const STATUS = {
    pending:   { label: 'En attente', cls: 'bg-amber-950/40 border-amber-700/40 text-amber-300' },
    validated: { label: 'Validé',     cls: 'bg-green-950/40 border-green-700/40 text-green-300' },
    cancelled: { label: 'Annulé',     cls: 'bg-zinc-800/60 border-zinc-700 text-zinc-500' }
  };
  const TIER_CLS = {
    Bronze: 'bg-amber-900/30 border-amber-700/40 text-amber-300',
    Argent: 'bg-zinc-700/50 border-zinc-500/40 text-zinc-200',
    Or:     'bg-yellow-900/30 border-yellow-600/40 text-yellow-300'
  };

  function formatDate(iso) {
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit'
    });
  }

  let filteredQuotes = $derived(
    !search.trim() ? data.quotes : data.quotes.filter(q =>
      [q.email, q.nom, q.material, String(q.id)].some(f =>
        f?.toLowerCase().includes(search.toLowerCase())
      )
    )
  );

  let filteredUsers = $derived(
    !search.trim() ? data.users : data.users.filter(u =>
      [u.email, u.name].some(f => f?.toLowerCase().includes(search.toLowerCase()))
    )
  );

  function findUser(id) { return data.users.find(u => u.id === id); }
</script>

<svelte:head>
  <title>Admin — TC Pliage</title>
</svelte:head>

<!-- Banner -->
<section class="relative border-b border-zinc-800/60 overflow-hidden">
  <img src="/gallery/machine1.jpg" alt="" class="absolute inset-0 w-full h-full object-cover opacity-15">
  <div class="absolute inset-0 bg-gradient-to-br from-zinc-950 via-zinc-950/95 to-amber-950/30"></div>
  <div class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber-600/40 to-transparent"></div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 bg-amber-600/15 border border-amber-600/30 rounded-2xl flex items-center justify-center flex-shrink-0">
        <i class="fas fa-shield-halved text-amber-400 text-lg"></i>
      </div>
      <div>
        <p class="text-amber-400/80 text-xs font-semibold uppercase tracking-[0.15em] mb-1">Espace administrateur</p>
        <h1 class="text-2xl sm:text-3xl font-bold text-zinc-100 tracking-tight">Tableau de bord</h1>
      </div>
    </div>
  </div>
</section>

<section class="py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">

    <!-- Stats grid -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {#each [
        ['Clients',          data.stats.totalUsers,    'fa-users',          'red'],
        ['Demandes totales', data.stats.totalQuotes,   'fa-file-invoice',   'blue'],
        ['En attente',       data.stats.pendingQuotes, 'fa-clock',          'amber'],
        ['CA validé',        `${data.stats.revenue.toFixed(0)} €`, 'fa-euro-sign', 'green']
      ] as [label, val, icon, color]}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
          <div class="flex items-start justify-between mb-3">
            <p class="text-xs text-zinc-500 uppercase tracking-wider">{label}</p>
            <div class="w-8 h-8 rounded-lg flex items-center justify-center
              {color === 'red'   ? 'bg-red-600/15 text-red-400' :
               color === 'blue'  ? 'bg-blue-600/15 text-blue-400' :
               color === 'amber' ? 'bg-amber-600/15 text-amber-400' :
                                   'bg-green-600/15 text-green-400'}">
              <i class="fas {icon} text-sm"></i>
            </div>
          </div>
          <p class="text-2xl font-bold text-zinc-100 tabular-nums">{val}</p>
        </div>
      {/each}
    </div>

    <!-- Tabs + search -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-xl p-1">
        <button onclick={() => tab = 'quotes'}
          class="px-4 py-2 rounded-lg text-sm font-medium transition-all
            {tab === 'quotes' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}">
          <i class="fas fa-file-invoice mr-1.5 text-xs"></i>
          Demandes ({data.quotes.length})
        </button>
        <button onclick={() => tab = 'users'}
          class="px-4 py-2 rounded-lg text-sm font-medium transition-all
            {tab === 'users' ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-500 hover:text-zinc-300'}">
          <i class="fas fa-users mr-1.5 text-xs"></i>
          Clients ({data.users.length})
        </button>
      </div>
      <div class="relative flex-1 max-w-xs">
        <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600 text-xs"></i>
        <input bind:value={search} type="search" placeholder="Rechercher…"
          class="w-full bg-zinc-900 border border-zinc-800 rounded-xl pl-9 pr-4 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-600 transition-all">
      </div>
    </div>

    <!-- Quotes tab -->
    {#if tab === 'quotes'}
      {#if filteredQuotes.length === 0}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center">
          <p class="text-zinc-500">Aucune demande.</p>
        </div>
      {:else}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-zinc-800/40 border-b border-zinc-800">
                <tr class="text-left text-xs text-zinc-500 uppercase tracking-wider">
                  <th class="px-4 py-3 font-semibold">N°</th>
                  <th class="px-4 py-3 font-semibold">Client</th>
                  <th class="px-4 py-3 font-semibold">Pièce</th>
                  <th class="px-4 py-3 font-semibold text-right">Montant</th>
                  <th class="px-4 py-3 font-semibold">Date</th>
                  <th class="px-4 py-3 font-semibold">Statut</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-zinc-800">
                {#each filteredQuotes as q}
                  <tr class="hover:bg-zinc-800/30 transition-colors">
                    <td class="px-4 py-3 font-mono text-xs text-zinc-500">#{String(q.id).padStart(4, '0')}</td>
                    <td class="px-4 py-3">
                      <p class="text-zinc-100 font-medium">{q.nom}</p>
                      <p class="text-zinc-500 text-xs">{q.email}</p>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-zinc-200">{MATERIALS[q.material] ?? q.material}</p>
                      <p class="text-zinc-500 text-xs">{q.total_length}×{q.width}×{q.thickness} mm · {q.bends_count} pli{q.bends_count > 1 ? 's' : ''}</p>
                    </td>
                    <td class="px-4 py-3 text-right tabular-nums font-semibold text-zinc-100">
                      {q.estimated_cost.toFixed(2)} €
                    </td>
                    <td class="px-4 py-3 text-zinc-400 text-xs whitespace-nowrap">{formatDate(q.created_at)}</td>
                    <td class="px-4 py-3">
                      <form method="POST" action="?/updateStatus" use:enhance class="inline-flex">
                        <input type="hidden" name="id" value={q.id}>
                        <select name="status" value={q.status}
                          onchange={(e) => e.target.form.requestSubmit()}
                          class="border text-xs px-2 py-1 rounded-lg font-semibold cursor-pointer focus:outline-none {STATUS[q.status]?.cls ?? STATUS.pending.cls}">
                          {#each Object.entries(STATUS) as [val, { label }]}
                            <option value={val} class="bg-zinc-900 text-zinc-100">{label}</option>
                          {/each}
                        </select>
                      </form>
                    </td>
                  </tr>
                  {#if q.notes}
                    <tr class="bg-zinc-950/40">
                      <td></td>
                      <td colspan="5" class="px-4 pb-3 text-xs text-zinc-500">
                        <i class="fas fa-comment text-[10px] mr-1.5"></i>
                        {q.notes}
                      </td>
                    </tr>
                  {/if}
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    {/if}

    <!-- Users tab -->
    {#if tab === 'users'}
      {#if filteredUsers.length === 0}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center">
          <p class="text-zinc-500">Aucun client.</p>
        </div>
      {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {#each filteredUsers as u}
            <div class="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-2xl p-5 transition-all">
              <div class="flex items-start justify-between gap-3 mb-4">
                <div class="flex items-center gap-3 min-w-0">
                  <div class="w-10 h-10 rounded-full bg-red-600/15 border border-red-600/25 flex items-center justify-center flex-shrink-0">
                    <span class="font-bold text-red-400">{u.name.charAt(0).toUpperCase()}</span>
                  </div>
                  <div class="min-w-0">
                    <p class="font-semibold text-zinc-100 truncate flex items-center gap-2">
                      {u.name}
                      {#if u.is_admin}
                        <i class="fas fa-shield-halved text-amber-400 text-xs" title="Administrateur"></i>
                      {/if}
                    </p>
                    <p class="text-xs text-zinc-500 truncate">{u.email}</p>
                  </div>
                </div>
                <span class="text-xs px-2 py-0.5 rounded-lg border font-semibold flex-shrink-0 {TIER_CLS[u.tier]}">
                  {u.tier}
                </span>
              </div>

              <div class="grid grid-cols-2 gap-3 text-xs">
                <div class="bg-zinc-800/40 rounded-xl p-3">
                  <p class="text-zinc-500 uppercase tracking-wider text-[10px] mb-0.5">Dépensé</p>
                  <p class="text-zinc-100 font-bold tabular-nums">{u.totalSpend.toFixed(0)} €</p>
                </div>
                <div class="bg-zinc-800/40 rounded-xl p-3">
                  <p class="text-zinc-500 uppercase tracking-wider text-[10px] mb-0.5">Demandes</p>
                  <p class="text-zinc-100 font-bold tabular-nums">{u.quoteCount}</p>
                </div>
              </div>

              <p class="text-xs text-zinc-600 mt-3">
                Inscrit le {new Date(u.created_at).toLocaleDateString('fr-FR')}
                {#if u.lastQuote}
                  · Dernière demande {new Date(u.lastQuote).toLocaleDateString('fr-FR')}
                {/if}
              </p>
            </div>
          {/each}
        </div>
      {/if}
    {/if}

  </div>
</section>
