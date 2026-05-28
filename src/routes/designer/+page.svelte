<script>
  // ─── Catalog ─────────────────────────────────────────────────────────────
  const materials = {
    acier:      { label: 'Acier',             price: 1.5, density: 7.85 },
    galvanise:  { label: 'Acier galvanisé',   price: 1.8, density: 7.85 },
    aluminium:  { label: 'Aluminium',         price: 4.0, density: 2.70 },
    inox:       { label: 'Inox',              price: 6.0, density: 7.90 }
  };

  const opPrices = { pli: 3, pli_ecrase: 5, retour: 2, poincon: 1.5, decoupe: 4 };
  const BASE_COST = 25;
  const MIN_COST = 30;

  // ─── State ───────────────────────────────────────────────────────────────
  let design = $state({
    material: 'acier',
    thickness: 1.5,
    length: 500,
    width: 200,
    operations: []
  });

  let nextOpId = 1;

  function addOp(type) {
    const half = Math.round(design.length / 2);
    const defaults = {
      pli:        { type, position: half, angle: 90, direction: 'up' },
      pli_ecrase: { type, position: half, direction: 'up' },
      retour:     { type, side: 'end', length: 15, direction: 'up' },
      poincon:    { type, position: half, diameter: 8 },
      decoupe:    { type, position: half, notchWidth: 30, notchDepth: 15, side: 'top' }
    };
    design.operations = [...design.operations, { id: nextOpId++, ...defaults[type] }];
  }

  function removeOp(id) {
    design.operations = design.operations.filter(o => o.id !== id);
  }

  function clearAll() {
    if (confirm('Effacer toutes les opérations ?')) {
      design.operations = [];
    }
  }

  // ─── Geometry (side profile) ────────────────────────────────────────────
  // Trace centerline as polyline. Angle 0 = right; "up" rotates CCW (negative in SVG).
  let geometry = $derived.by(() => {
    const bends = design.operations
      .filter(o => o.type === 'pli' || o.type === 'pli_ecrase')
      .slice()
      .sort((a, b) => a.position - b.position);

    let x = 0, y = 0, angle = 0;
    const points = [{ x, y }];
    const segments = [];
    let lastPos = 0;

    for (const bend of bends) {
      const len = Math.max(0, bend.position - lastPos);
      const sx = x, sy = y, sa = angle;
      x += len * Math.cos(angle);
      y += len * Math.sin(angle);
      points.push({ x, y });
      segments.push({ startPos: lastPos, endPos: bend.position, sx, sy, angle: sa });

      const deg = bend.type === 'pli_ecrase' ? 180 : bend.angle;
      const sign = bend.direction === 'up' ? -1 : 1;
      angle += sign * deg * Math.PI / 180;
      lastPos = bend.position;
    }
    const finalLen = Math.max(0, design.length - lastPos);
    const sx = x, sy = y, sa = angle;
    x += finalLen * Math.cos(angle);
    y += finalLen * Math.sin(angle);
    points.push({ x, y });
    segments.push({ startPos: lastPos, endPos: design.length, sx, sy, angle: sa });

    return { points, segments };
  });

  function pointAt(position) {
    const seg = geometry.segments.find(s => position >= s.startPos && position <= s.endPos)
              ?? geometry.segments[geometry.segments.length - 1];
    const along = position - seg.startPos;
    return {
      x: seg.sx + along * Math.cos(seg.angle),
      y: seg.sy + along * Math.sin(seg.angle),
      angle: seg.angle
    };
  }

  let viewBox = $derived.by(() => {
    const xs = geometry.points.map(p => p.x);
    const ys = geometry.points.map(p => p.y);
    const pad = Math.max(60, design.thickness * 5);
    const minX = Math.min(...xs) - pad;
    const maxX = Math.max(...xs) + pad;
    const minY = Math.min(...ys) - pad;
    const maxY = Math.max(...ys) + pad;
    return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`;
  });

  let pathD = $derived(
    geometry.points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ')
  );

  // ─── Pricing ─────────────────────────────────────────────────────────────
  let pricing = $derived.by(() => {
    const m = materials[design.material];
    const volumeCm3 = (design.length * design.width * design.thickness) / 1000;
    const weightKg = (volumeCm3 * m.density) / 1000;
    const materialCost = weightKg * m.price;
    const opsCost = design.operations.reduce((s, op) => s + (opPrices[op.type] || 0), 0);
    const subtotal = BASE_COST + materialCost + opsCost;
    const total = Math.max(MIN_COST, subtotal);
    return { weightKg, materialCost, opsCost, base: BASE_COST, total };
  });

  // ─── Quote submission ────────────────────────────────────────────────────
  let showQuote = $state(false);
  let quote = $state({ nom: '', email: '', telephone: '', notes: '' });
  let quoteStatus = $state(null); // null | sending | success | error
  let quoteError = $state('');

  function opSummary(op) {
    if (op.type === 'pli')        return `Pli ${op.angle}° ${op.direction === 'up' ? '↑' : '↓'} à ${op.position} mm`;
    if (op.type === 'pli_ecrase') return `Pli écrasé ${op.direction === 'up' ? '↑' : '↓'} à ${op.position} mm`;
    if (op.type === 'retour')     return `Retour ${op.length} mm côté ${op.side === 'start' ? 'début' : 'fin'} ${op.direction === 'up' ? '↑' : '↓'}`;
    if (op.type === 'poincon')    return `Poinçon Ø${op.diameter} mm à ${op.position} mm`;
    if (op.type === 'decoupe')    return `Découpe ${op.notchWidth}×${op.notchDepth} mm à ${op.position} mm (${op.side === 'top' ? 'haut' : 'bas'})`;
    return '';
  }

  async function submitQuote(e) {
    e.preventDefault();
    if (!quote.nom.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(quote.email)) return;
    quoteStatus = 'sending';
    quoteError = '';

    const opsLines = design.operations.length
      ? design.operations.map(o => '• ' + opSummary(o)).join('<br>')
      : '<em>(aucune opération)</em>';

    const message = `
<strong>Demande de devis depuis le designer</strong><br><br>
<strong>Client</strong><br>
Nom : ${quote.nom}<br>
Email : ${quote.email}<br>
Téléphone : ${quote.telephone || '—'}<br><br>
<strong>Notes</strong><br>
${quote.notes ? quote.notes.replace(/\n/g, '<br>') : '—'}<br><br>
<strong>Pièce</strong><br>
Matériau : ${materials[design.material].label}<br>
Épaisseur : ${design.thickness} mm<br>
Longueur développée : ${design.length} mm<br>
Largeur : ${design.width} mm<br>
Poids estimé : ${pricing.weightKg.toFixed(2)} kg<br><br>
<strong>Opérations (${design.operations.length})</strong><br>
${opsLines}
`.trim();

    try {
      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          replyTo: quote.email,
          subject: `Devis designer — ${materials[design.material].label} ${design.length}×${design.width}×${design.thickness}mm`,
          message,
          estimatedCost: pricing.total.toFixed(2),
          designData: JSON.stringify(design, null, 2),
          submittedAt: new Date().toISOString()
        })
      });
      if (!res.ok) throw new Error('failed');
      quoteStatus = 'success';
    } catch {
      quoteStatus = 'error';
      quoteError = 'L\'envoi a échoué. Merci de nous contacter directement par téléphone.';
    }
  }

  function resetQuote() {
    showQuote = false;
    quoteStatus = null;
    quote = { nom: '', email: '', telephone: '', notes: '' };
  }
</script>

<svelte:head>
  <title>Designer — TC Pliage</title>
</svelte:head>

<!-- Header -->
<section class="border-b border-zinc-800 bg-zinc-950">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
    <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-3">
      <span class="w-8 h-px bg-red-500"></span>
      Outil de conception
    </span>
    <h1 class="text-3xl sm:text-4xl font-bold text-zinc-100">Concevoir une pièce</h1>
    <p class="text-zinc-400 mt-2 max-w-2xl text-sm">
      Dessinez votre pièce en 2D, ajoutez vos plis et perçages, et obtenez une estimation immédiate.
    </p>
  </div>
</section>

<!-- Main grid -->
<section class="py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-5 gap-6">

    <!-- LEFT: Preview + price (sticky on desktop) -->
    <div class="lg:col-span-2 space-y-4 lg:sticky lg:top-20 self-start">

      <!-- SVG preview -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-zinc-500 uppercase tracking-wider">Vue de côté</span>
          <span class="text-xs text-zinc-500">{design.operations.length} opération{design.operations.length > 1 ? 's' : ''}</span>
        </div>
        <div class="bg-zinc-950 border border-zinc-800 rounded-lg aspect-square overflow-hidden">
          <svg {viewBox} preserveAspectRatio="xMidYMid meet" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <!-- grid -->
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#27272a" stroke-width="0.5"/>
              </pattern>
            </defs>
            <rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#grid)"/>

            <!-- metal body -->
            <path
              d={pathD}
              fill="none"
              stroke="#a1a1aa"
              stroke-width={design.thickness * 4}
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <path
              d={pathD}
              fill="none"
              stroke="#71717a"
              stroke-width={design.thickness * 4}
              stroke-linejoin="round"
              stroke-linecap="round"
              stroke-dasharray="0"
              opacity="0.4"
            />

            <!-- bend markers -->
            {#each design.operations.filter(o => o.type === 'pli' || o.type === 'pli_ecrase') as op}
              {@const p = pointAt(op.position)}
              <g transform="translate({p.x.toFixed(2)} {p.y.toFixed(2)})">
                <circle r={design.thickness * 2.5} fill="#dc2626" opacity="0.8"/>
                <circle r={design.thickness * 1} fill="#fff"/>
              </g>
            {/each}

            <!-- holes (poinçonnage) -->
            {#each design.operations.filter(o => o.type === 'poincon') as op}
              {@const p = pointAt(op.position)}
              <g transform="translate({p.x.toFixed(2)} {p.y.toFixed(2)}) rotate({(p.angle * 180 / Math.PI).toFixed(2)})">
                <rect
                  x={-op.diameter / 2}
                  y={-design.thickness * 2.5}
                  width={op.diameter}
                  height={design.thickness * 5}
                  fill="#09090b"
                  stroke="#fbbf24"
                  stroke-width="1"
                />
              </g>
            {/each}

            <!-- notches (découpe) -->
            {#each design.operations.filter(o => o.type === 'decoupe') as op}
              {@const p = pointAt(op.position)}
              <g transform="translate({p.x.toFixed(2)} {p.y.toFixed(2)}) rotate({(p.angle * 180 / Math.PI).toFixed(2)})">
                <rect
                  x={-op.notchWidth / 2}
                  y={op.side === 'top' ? -design.thickness * 2 - op.notchDepth : design.thickness * 2}
                  width={op.notchWidth}
                  height={op.notchDepth}
                  fill="#09090b"
                  stroke="#f87171"
                  stroke-width="1"
                  stroke-dasharray="3,2"
                />
              </g>
            {/each}

            <!-- start/end markers -->
            {#if geometry.points.length}
              <circle cx={geometry.points[0].x} cy={geometry.points[0].y} r="6" fill="#22c55e"/>
              <circle cx={geometry.points.at(-1).x} cy={geometry.points.at(-1).y} r="6" fill="#3b82f6"/>
            {/if}
          </svg>
        </div>
        <div class="flex items-center gap-4 mt-3 text-xs text-zinc-500">
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500"></span>Début</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-blue-500"></span>Fin</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-600"></span>Pli</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 bg-amber-400"></span>Perçage</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 border border-red-400"></span>Découpe</span>
        </div>
      </div>

      <!-- Price card -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <div class="flex items-baseline justify-between mb-4">
          <span class="text-zinc-400 text-sm uppercase tracking-wider">Estimation</span>
          <span class="text-3xl font-extrabold text-red-500">{pricing.total.toFixed(2)} €</span>
        </div>
        <div class="space-y-1.5 text-sm">
          <div class="flex justify-between text-zinc-400">
            <span>Matière ({pricing.weightKg.toFixed(2)} kg)</span>
            <span>{pricing.materialCost.toFixed(2)} €</span>
          </div>
          <div class="flex justify-between text-zinc-400">
            <span>Opérations ({design.operations.length})</span>
            <span>{pricing.opsCost.toFixed(2)} €</span>
          </div>
          <div class="flex justify-between text-zinc-400">
            <span>Frais fixes</span>
            <span>{pricing.base.toFixed(2)} €</span>
          </div>
        </div>
        <button
          onclick={() => showQuote = true}
          class="w-full mt-4 bg-red-600 hover:bg-red-500 text-white font-semibold py-3 rounded transition-colors flex items-center justify-center gap-2"
        >
          <i class="fas fa-paper-plane text-sm"></i>
          Demander un devis
        </button>
        <p class="text-xs text-zinc-500 mt-2 text-center">Estimation indicative. Devis définitif sous 24h.</p>
      </div>
    </div>

    <!-- RIGHT: form controls -->
    <div class="lg:col-span-3 space-y-6">

      <!-- Material & dimensions -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 class="text-zinc-100 font-semibold mb-4 flex items-center gap-2">
          <i class="fas fa-cube text-red-500 text-sm"></i>
          Matériau & dimensions
        </h2>

        <div class="space-y-4">
          <div>
            <label class="block text-sm text-zinc-400 mb-2">Matériau</label>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {#each Object.entries(materials) as [key, m]}
                <button
                  type="button"
                  onclick={() => design.material = key}
                  class="px-3 py-2.5 text-sm font-medium rounded border transition-colors
                    {design.material === key
                      ? 'bg-red-600/15 border-red-600 text-red-400'
                      : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-600'}"
                >
                  {m.label}
                </button>
              {/each}
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label for="length" class="block text-xs text-zinc-500 mb-1">Longueur (mm)</label>
              <input
                id="length"
                type="number"
                min="50"
                max="3000"
                step="10"
                bind:value={design.length}
                class="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:outline-none focus:border-red-600 text-sm"
              >
            </div>
            <div>
              <label for="width" class="block text-xs text-zinc-500 mb-1">Largeur (mm)</label>
              <input
                id="width"
                type="number"
                min="20"
                max="1500"
                step="10"
                bind:value={design.width}
                class="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:outline-none focus:border-red-600 text-sm"
              >
            </div>
            <div>
              <label for="thickness" class="block text-xs text-zinc-500 mb-1">Épaisseur (mm)</label>
              <input
                id="thickness"
                type="number"
                min="0.5"
                max="10"
                step="0.1"
                bind:value={design.thickness}
                class="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-zinc-100 focus:outline-none focus:border-red-600 text-sm"
              >
            </div>
          </div>
          <p class="text-xs text-zinc-500">La largeur n'apparaît pas dans la vue de côté (profondeur perpendiculaire).</p>
        </div>
      </div>

      <!-- Add operation buttons -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-zinc-100 font-semibold flex items-center gap-2">
            <i class="fas fa-plus-circle text-red-500 text-sm"></i>
            Ajouter une opération
          </h2>
          {#if design.operations.length > 0}
            <button
              onclick={clearAll}
              class="text-xs text-zinc-500 hover:text-red-400 transition-colors"
            >
              Tout effacer
            </button>
          {/if}
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {#each [
            ['pli',        'Pli',          'fa-angle-up'],
            ['pli_ecrase', 'Pli écrasé',   'fa-compress'],
            ['retour',     'Retour',       'fa-undo'],
            ['poincon',    'Perçage',      'fa-circle'],
            ['decoupe',    'Découpe',      'fa-cut']
          ] as [type, label, icon]}
            <button
              type="button"
              onclick={() => addOp(type)}
              class="flex flex-col items-center gap-1.5 px-3 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-300 hover:text-zinc-100 text-xs font-medium transition-colors"
            >
              <i class="fas {icon} text-base text-red-500"></i>
              {label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Operations list -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <h2 class="text-zinc-100 font-semibold mb-4 flex items-center gap-2">
          <i class="fas fa-list text-red-500 text-sm"></i>
          Opérations ({design.operations.length})
        </h2>

        {#if design.operations.length === 0}
          <p class="text-zinc-500 text-sm text-center py-6">
            Aucune opération. Ajoutez un pli ou un perçage pour commencer.
          </p>
        {:else}
          <div class="space-y-3">
            {#each design.operations as op (op.id)}
              <div class="bg-zinc-800/50 border border-zinc-700 rounded-lg p-3">
                <div class="flex items-start justify-between gap-3 mb-2">
                  <span class="text-zinc-100 text-sm font-medium">{opSummary(op)}</span>
                  <button
                    onclick={() => removeOp(op.id)}
                    class="text-zinc-500 hover:text-red-500 transition-colors flex-shrink-0"
                    aria-label="Supprimer"
                  >
                    <i class="fas fa-trash text-xs"></i>
                  </button>
                </div>

                <!-- Inline editors -->
                {#if op.type === 'pli'}
                  <div class="grid grid-cols-3 gap-2 mt-2">
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Position (mm)
                      <input type="number" min="0" max={design.length} step="5" bind:value={op.position}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Angle (°)
                      <input type="number" min="10" max="180" step="5" bind:value={op.angle}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Direction
                      <select bind:value={op.direction}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                        <option value="up">Haut ↑</option>
                        <option value="down">Bas ↓</option>
                      </select>
                    </label>
                  </div>
                {:else if op.type === 'pli_ecrase'}
                  <div class="grid grid-cols-2 gap-2 mt-2">
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Position (mm)
                      <input type="number" min="0" max={design.length} step="5" bind:value={op.position}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Direction
                      <select bind:value={op.direction}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                        <option value="up">Haut ↑</option>
                        <option value="down">Bas ↓</option>
                      </select>
                    </label>
                  </div>
                {:else if op.type === 'retour'}
                  <div class="grid grid-cols-3 gap-2 mt-2">
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Côté
                      <select bind:value={op.side}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                        <option value="start">Début</option>
                        <option value="end">Fin</option>
                      </select>
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Longueur (mm)
                      <input type="number" min="5" max="100" step="1" bind:value={op.length}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Direction
                      <select bind:value={op.direction}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                        <option value="up">Haut ↑</option>
                        <option value="down">Bas ↓</option>
                      </select>
                    </label>
                  </div>
                {:else if op.type === 'poincon'}
                  <div class="grid grid-cols-2 gap-2 mt-2">
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Position (mm)
                      <input type="number" min="0" max={design.length} step="5" bind:value={op.position}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Ø (mm)
                      <input type="number" min="2" max="50" step="0.5" bind:value={op.diameter}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                  </div>
                {:else if op.type === 'decoupe'}
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Position (mm)
                      <input type="number" min="0" max={design.length} step="5" bind:value={op.position}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Largeur
                      <input type="number" min="5" max="200" step="1" bind:value={op.notchWidth}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Profondeur
                      <input type="number" min="2" max="100" step="1" bind:value={op.notchDepth}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                    </label>
                    <label class="text-xs text-zinc-400 flex flex-col gap-1">
                      Côté
                      <select bind:value={op.side}
                        class="bg-zinc-900 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600">
                        <option value="top">Haut</option>
                        <option value="bottom">Bas</option>
                      </select>
                    </label>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
</section>

<!-- Quote modal -->
{#if showQuote}
  <div
    role="dialog"
    aria-modal="true"
    aria-label="Demander un devis"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-zinc-950/80 backdrop-blur-sm"
    onclick={(e) => { if (e.target === e.currentTarget) resetQuote(); }}
    onkeydown={(e) => { if (e.key === 'Escape') resetQuote(); }}
    tabindex="-1"
  >
    <div class="bg-zinc-900 border border-zinc-700 rounded-2xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">

      {#if quoteStatus === 'success'}
        <div class="text-center py-6">
          <div class="w-14 h-14 bg-green-600/20 border border-green-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-check text-green-400 text-xl"></i>
          </div>
          <h3 class="text-zinc-100 font-semibold text-lg mb-2">Demande envoyée !</h3>
          <p class="text-zinc-400 text-sm mb-6">Nous vous répondrons sous 24h avec un devis définitif.</p>
          <button
            onclick={resetQuote}
            class="bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-2.5 rounded transition-colors"
          >
            Fermer
          </button>
        </div>
      {:else}
        <div class="flex items-start justify-between mb-5">
          <div>
            <h3 class="text-zinc-100 font-semibold text-lg">Demander un devis</h3>
            <p class="text-zinc-400 text-sm mt-1">Estimation : <span class="text-red-500 font-semibold">{pricing.total.toFixed(2)} €</span></p>
          </div>
          <button
            onclick={resetQuote}
            class="text-zinc-500 hover:text-zinc-300 transition-colors"
            aria-label="Fermer"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>

        <form onsubmit={submitQuote} class="space-y-4">
          <div>
            <label for="q-nom" class="block text-sm text-zinc-300 mb-1.5">Nom <span class="text-red-500">*</span></label>
            <input
              id="q-nom"
              type="text"
              bind:value={quote.nom}
              required
              class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 text-sm"
            >
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label for="q-email" class="block text-sm text-zinc-300 mb-1.5">Email <span class="text-red-500">*</span></label>
              <input
                id="q-email"
                type="email"
                bind:value={quote.email}
                required
                class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 text-sm"
              >
            </div>
            <div>
              <label for="q-tel" class="block text-sm text-zinc-300 mb-1.5">Téléphone</label>
              <input
                id="q-tel"
                type="tel"
                bind:value={quote.telephone}
                class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 text-sm"
              >
            </div>
          </div>
          <div>
            <label for="q-notes" class="block text-sm text-zinc-300 mb-1.5">Notes (optionnel)</label>
            <textarea
              id="q-notes"
              bind:value={quote.notes}
              rows="3"
              placeholder="Quantité, contraintes particulières, délai souhaité…"
              class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 text-sm resize-none"
            ></textarea>
          </div>

          {#if quoteStatus === 'error'}
            <p class="text-red-400 text-sm bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
              <i class="fas fa-exclamation-circle mr-2"></i>{quoteError}
            </p>
          {/if}

          <div class="flex gap-3 pt-2">
            <button
              type="button"
              onclick={resetQuote}
              class="flex-1 border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 font-medium px-4 py-2.5 rounded transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={quoteStatus === 'sending'}
              class="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold px-4 py-2.5 rounded transition-colors flex items-center justify-center gap-2"
            >
              {#if quoteStatus === 'sending'}
                <i class="fas fa-spinner fa-spin"></i> Envoi…
              {:else}
                <i class="fas fa-paper-plane text-sm"></i> Envoyer
              {/if}
            </button>
          </div>
        </form>
      {/if}
    </div>
  </div>
{/if}
