<script>
  const materials = {
    acier:     { label: 'Acier',           price: 1.5, density: 7.85 },
    galvanise: { label: 'Acier galvanisé', price: 1.8, density: 7.85 },
    aluminium: { label: 'Aluminium',       price: 4.0, density: 2.70 },
    inox:      { label: 'Inox',            price: 6.0, density: 7.90 }
  };

  const BASE_COST = 25;
  const MIN_COST  = 30;
  const opPrices  = { pli: 3, pli_ecrase: 5, poincon: 1.5, decoupe: 4 };

  let _id = 0;
  const uid = () => ++_id;

  // ── Wizard step ───────────────────────────────────────────
  let step = $state(1);

  // ── Base design ───────────────────────────────────────────
  let design = $state({ material: 'acier', thickness: 1.5, width: 200 });

  // ── Profile: segments + bends between them ────────────────
  let segments = $state([{ id: uid(), length: 200 }]);
  let bends    = $state([]); // bends[i] sits between segments[i] and segments[i+1]

  // ── Extras placed on the unfolded view (x, y from top-left) ──
  let extras = $state([]);

  // ── Side-profile zoom ─────────────────────────────────────
  let zoom = $state(1);

  // ── Profile mutation ──────────────────────────────────────
  function addRight() {
    bends    = [...bends,    { id: uid(), type: 'pli', angle: 90, direction: 'up' }];
    segments = [...segments, { id: uid(), length: 100 }];
  }
  function addLeft() {
    segments = [{ id: uid(), length: 100 }, ...segments];
    bends    = [{ id: uid(), type: 'pli', angle: 90, direction: 'up' }, ...bends];
  }
  function addRetourRight() {
    bends    = [...bends,    { id: uid(), type: 'pli_ecrase', direction: 'up' }];
    segments = [...segments, { id: uid(), length: 15 }];
  }
  function addRetourLeft() {
    segments = [{ id: uid(), length: 15 }, ...segments];
    bends    = [{ id: uid(), type: 'pli_ecrase', direction: 'up' }, ...bends];
  }
  function removeSegment(idx) {
    if (segments.length === 1) return;
    const ns = [...segments];
    const nb = [...bends];
    ns.splice(idx, 1);
    const bi = idx < bends.length ? idx : idx - 1;
    if (bi >= 0) nb.splice(bi, 1);
    segments = ns;
    bends    = nb;
  }
  function removeBend(idx) {
    const ns = [...segments];
    const nb = [...bends];
    ns[idx] = { ...ns[idx], length: ns[idx].length + ns[idx + 1].length };
    ns.splice(idx + 1, 1);
    nb.splice(idx, 1);
    segments = ns;
    bends    = nb;
  }

  // ── Extras ────────────────────────────────────────────────
  function addExtra(type) {
    const cx = Math.round(totalLength / 2);
    const cy = Math.round(design.width / 2);
    extras = [
      ...extras,
      type === 'poincon'
        ? { id: uid(), type, x: cx, y: cy, diameter: 8 }
        : { id: uid(), type, x: cx - 15, y: cy - 7.5, w: 30, h: 15 }
    ];
  }
  function removeExtra(id) {
    extras = extras.filter(e => e.id !== id);
  }

  // ── Side-profile geometry ─────────────────────────────────
  // pli_ecrase: 180° turn + small perpendicular offset so the doubled-back
  // segment is visible parallel to the previous one (looks like a "retour").
  let geometry = $derived.by(() => {
    let x = 0, y = 0, a = 0;
    const points  = [{ x, y }];
    const segData = [];
    const t = Math.max(2, design.thickness * 2);

    for (let i = 0; i < segments.length; i++) {
      const sx = x, sy = y, sa = a;
      x += segments[i].length * Math.cos(a);
      y += segments[i].length * Math.sin(a);
      points.push({ x, y });
      segData.push({ sx, sy, angle: sa, length: segments[i].length });

      if (i < bends.length) {
        const b = bends[i];
        if (b.type === 'pli_ecrase') {
          // 180° turn
          a += Math.PI;
          // perpendicular nudge so doubled-back stub is visible
          const nx = Math.cos(a + (b.direction === 'up' ? -Math.PI / 2 : Math.PI / 2));
          const ny = Math.sin(a + (b.direction === 'up' ? -Math.PI / 2 : Math.PI / 2));
          x += nx * t;
          y += ny * t;
        } else {
          const deg = b.angle || 90;
          a += (b.direction === 'up' ? -1 : 1) * deg * Math.PI / 180;
        }
      }
    }
    return { points, segData };
  });

  let bounds = $derived.by(() => {
    const xs = geometry.points.map(p => p.x);
    const ys = geometry.points.map(p => p.y);
    return {
      minX: Math.min(...xs), maxX: Math.max(...xs),
      minY: Math.min(...ys), maxY: Math.max(...ys)
    };
  });

  let viewBox = $derived.by(() => {
    const pad = Math.max(60, design.thickness * 5);
    const w0  = (bounds.maxX - bounds.minX) + pad * 2;
    const h0  = (bounds.maxY - bounds.minY) + pad * 2;
    const w   = w0 / zoom;
    const h   = h0 / zoom;
    const cx  = (bounds.minX + bounds.maxX) / 2;
    const cy  = (bounds.minY + bounds.maxY) / 2;
    return `${cx - w / 2} ${cy - h / 2} ${w} ${h}`;
  });

  let pathD = $derived(
    geometry.points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ')
  );

  // ── Pricing ───────────────────────────────────────────────
  let totalLength = $derived(segments.reduce((s, seg) => s + (Number(seg.length) || 0), 0));

  let pricing = $derived.by(() => {
    const m   = materials[design.material];
    const vol = (totalLength * design.width * design.thickness) / 1000;
    const kg  = (vol * m.density) / 1000;
    const mat = kg * m.price;
    const ops = bends.reduce( (s, b) => s + (opPrices[b.type] || 0), 0)
              + extras.reduce((s, e) => s + (opPrices[e.type] || 0), 0);
    return { kg, mat, ops, total: Math.max(MIN_COST, BASE_COST + mat + ops) };
  });

  // ── Quote ─────────────────────────────────────────────────
  let quote       = $state({ nom: '', email: '', telephone: '', notes: '' });
  let quoteStatus = $state(null);
  let quoteError  = $state('');

  async function submitQuote(ev) {
    ev.preventDefault();
    if (!quote.nom.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(quote.email)) return;
    quoteStatus = 'sending';
    quoteError  = '';

    const lines = [];
    for (let i = 0; i < segments.length; i++) {
      lines.push(`Segment ${i + 1} : ${segments[i].length} mm`);
      if (i < bends.length) {
        const b = bends[i];
        lines.push(`  → ${b.type === 'pli_ecrase' ? 'Pli écrasé (180°)' : `Pli ${b.angle}°`} ${b.direction === 'up' ? '↑' : '↓'}`);
      }
    }
    for (const e of extras) {
      lines.push(e.type === 'poincon'
        ? `Perçage Ø${e.diameter} mm — (${e.x}, ${e.y}) mm depuis coin haut-gauche`
        : `Découpe ${e.w}×${e.h} mm — coin (${e.x}, ${e.y}) mm depuis coin haut-gauche`);
    }

    const message = `
<strong>Devis designer — TC Pliage</strong><br><br>
Nom : ${quote.nom}<br>
Email : ${quote.email}<br>
Téléphone : ${quote.telephone || '—'}<br>
Notes : ${quote.notes ? quote.notes.replace(/\n/g, '<br>') : '—'}<br><br>
<strong>Pièce</strong><br>
${materials[design.material].label} — ép. ${design.thickness} mm — larg. ${design.width} mm<br>
Longueur développée : ${totalLength} mm — Poids estimé : ${pricing.kg.toFixed(3)} kg — Plis : ${bends.length}<br><br>
<strong>Profil & opérations</strong><br>
<pre style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px">${lines.join('\n')}</pre>
`.trim();

    try {
      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          replyTo:       quote.email,
          subject:       `Devis — ${materials[design.material].label} ${totalLength}×${design.width}×${design.thickness} mm`,
          message,
          estimatedCost: pricing.total.toFixed(2),
          designData:    JSON.stringify({ design, segments, bends, extras }, null, 2),
          submittedAt:   new Date().toISOString()
        })
      });
      if (!res.ok) throw new Error();
      quoteStatus = 'success';
    } catch {
      quoteStatus = 'error';
      quoteError  = "L'envoi a échoué. Merci de nous contacter directement par téléphone.";
    }
  }

  const STEPS = [
    { n: 1, icon: 'fa-cube',         label: 'Matériau'    },
    { n: 2, icon: 'fa-draw-polygon', label: 'Profil'      },
    { n: 3, icon: 'fa-ruler-combined', label: 'Profondeur' },
    { n: 4, icon: 'fa-wrench',       label: 'Opérations'  },
    { n: 5, icon: 'fa-paper-plane',  label: 'Devis'       }
  ];

  const inp  = 'bg-zinc-800 border border-zinc-700 rounded px-2 py-1.5 text-zinc-100 text-sm focus:outline-none focus:border-red-600';
  const inp2 = 'bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-zinc-300 text-xs focus:outline-none focus:border-red-600';
</script>

<svelte:head>
  <title>Designer — TC Pliage</title>
</svelte:head>

<section class="border-b border-zinc-800 bg-zinc-950">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
    <span class="inline-flex items-center gap-2 text-red-500 text-sm font-semibold uppercase tracking-widest mb-3">
      <span class="w-8 h-px bg-red-500"></span>
      Outil de conception
    </span>
    <h1 class="text-3xl sm:text-4xl font-bold text-zinc-100">Concevoir une pièce</h1>
    <p class="text-zinc-400 mt-2 text-sm max-w-2xl">
      Dessinez votre profil en ajoutant des points de gauche à droite, choisissez la profondeur, puis placez perçages et découpes sur la pièce dépliée.
    </p>
  </div>
</section>

<section class="py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-5 gap-6">

    <!-- ── LEFT: sticky preview + price ───────────────────── -->
    <div class="lg:col-span-2 space-y-4 lg:sticky lg:top-20 self-start">

      <!-- Side-profile preview -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-zinc-500 uppercase tracking-wider">Vue de côté</span>
          <div class="flex items-center gap-1">
            <button
              onclick={() => zoom = Math.max(0.25, +(zoom / 1.25).toFixed(2))}
              class="w-7 h-7 flex items-center justify-center bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-zinc-400 hover:text-zinc-200 transition-colors"
              aria-label="Dézoomer"
            >
              <i class="fas fa-search-minus text-xs"></i>
            </button>
            <span class="text-xs text-zinc-500 w-11 text-center tabular-nums">{Math.round(zoom * 100)}%</span>
            <button
              onclick={() => zoom = Math.min(8, +(zoom * 1.25).toFixed(2))}
              class="w-7 h-7 flex items-center justify-center bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-zinc-400 hover:text-zinc-200 transition-colors"
              aria-label="Zoomer"
            >
              <i class="fas fa-search-plus text-xs"></i>
            </button>
            <button
              onclick={() => zoom = 1}
              class="ml-1 px-2 h-7 flex items-center bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded text-xs text-zinc-400 hover:text-zinc-200 transition-colors"
              aria-label="Réinitialiser le zoom"
            >
              <i class="fas fa-expand text-xs"></i>
            </button>
          </div>
        </div>
        <div class="bg-zinc-950 border border-zinc-800 rounded-lg aspect-square overflow-hidden">
          <svg {viewBox} preserveAspectRatio="xMidYMid meet" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#27272a" stroke-width="0.5"/>
              </pattern>
            </defs>
            <rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#grid)"/>

            <path d={pathD} fill="none" stroke="#a1a1aa"
              stroke-width={design.thickness * 4}
              stroke-linejoin="round" stroke-linecap="round"/>

            {#each bends as bend, i}
              <circle
                cx={geometry.points[i + 1].x}
                cy={geometry.points[i + 1].y}
                r={design.thickness * 2.5}
                fill={bend.type === 'pli_ecrase' ? '#f97316' : '#dc2626'}
                opacity="0.85"
              />
              <circle
                cx={geometry.points[i + 1].x}
                cy={geometry.points[i + 1].y}
                r={design.thickness * 1}
                fill="#fff"
              />
            {/each}

            {#if geometry.points.length}
              <circle cx={geometry.points[0].x} cy={geometry.points[0].y} r={Math.max(4, design.thickness * 2)} fill="#22c55e"/>
              <circle cx={geometry.points.at(-1).x} cy={geometry.points.at(-1).y} r={Math.max(4, design.thickness * 2)} fill="#3b82f6"/>
            {/if}
          </svg>
        </div>
        <div class="flex items-center flex-wrap gap-4 mt-3 text-xs text-zinc-500">
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500"></span>Début</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-blue-500"></span>Fin</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-red-600"></span>Pli</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-orange-500"></span>Pli écrasé</span>
        </div>
      </div>

      <!-- Price card -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <div class="flex items-baseline justify-between mb-4">
          <span class="text-zinc-400 text-sm uppercase tracking-wider">Estimation</span>
          <span class="text-3xl font-extrabold text-red-500">{pricing.total.toFixed(2)} €</span>
        </div>
        <div class="space-y-1.5 text-sm text-zinc-400">
          <div class="flex justify-between">
            <span>Matière ({pricing.kg.toFixed(3)} kg)</span>
            <span>{pricing.mat.toFixed(2)} €</span>
          </div>
          <div class="flex justify-between">
            <span>Opérations ({bends.length + extras.length})</span>
            <span>{pricing.ops.toFixed(2)} €</span>
          </div>
          <div class="flex justify-between">
            <span>Frais fixes</span>
            <span>{BASE_COST.toFixed(2)} €</span>
          </div>
          <div class="flex justify-between text-zinc-500 text-xs pt-1 border-t border-zinc-800">
            <span>Longueur développée</span>
            <span>{totalLength} mm</span>
          </div>
          <div class="flex justify-between text-zinc-500 text-xs">
            <span>Profondeur (largeur)</span>
            <span>{design.width} mm</span>
          </div>
        </div>
        <button
          onclick={() => step = 5}
          class="w-full mt-4 bg-red-600 hover:bg-red-500 text-white font-semibold py-3 rounded transition-colors flex items-center justify-center gap-2"
        >
          <i class="fas fa-paper-plane text-sm"></i>
          Demander un devis
        </button>
        <p class="text-xs text-zinc-500 mt-2 text-center">Estimation indicative. Devis définitif sous 24 h.</p>
      </div>
    </div>

    <!-- ── RIGHT: step wizard ──────────────────────────────── -->
    <div class="lg:col-span-3">

      <!-- Step indicator -->
      <div class="flex items-center gap-1 mb-6 overflow-x-auto pb-1">
        {#each STEPS as s, idx}
          <button
            onclick={() => step = s.n}
            class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap
              {step === s.n
                ? 'bg-red-600/15 border border-red-600/60 text-red-400'
                : 'text-zinc-500 hover:text-zinc-300 border border-transparent hover:border-zinc-700'}"
          >
            <i class="fas {s.icon} text-xs"></i>
            <span class="hidden sm:inline">{s.label}</span>
            <span class="sm:hidden">{s.n}</span>
          </button>
          {#if idx < STEPS.length - 1}
            <span class="w-3 h-px bg-zinc-800 flex-shrink-0"></span>
          {/if}
        {/each}
      </div>

      <!-- ── Step 1: Matériau ───────────────────────────────── -->
      {#if step === 1}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-5">
          <h2 class="text-zinc-100 font-semibold flex items-center gap-2">
            <i class="fas fa-cube text-red-500 text-sm"></i>
            Matériau & épaisseur
          </h2>
          <div>
            <p class="text-sm text-zinc-400 mb-2">Matériau</p>
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
            <p class="text-xs text-zinc-600 mt-2">
              Prix : {materials[design.material].price} €/kg · Densité : {materials[design.material].density} g/cm³
            </p>
          </div>
          <div>
            <label for="thickness" class="block text-xs text-zinc-500 mb-1">Épaisseur (mm)</label>
            <input id="thickness" type="number" min="0.5" max="10" step="0.1"
              bind:value={design.thickness}
              class="{inp} w-full sm:w-48">
          </div>
        </div>
      {/if}

      <!-- ── Step 2: Profil ─────────────────────────────────── -->
      {#if step === 2}
        <div class="space-y-4">
          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <h2 class="text-zinc-100 font-semibold flex items-center gap-2 mb-4">
              <i class="fas fa-draw-polygon text-red-500 text-sm"></i>
              Dessiner le profil
            </h2>
            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-2">
                <p class="text-xs text-zinc-500 uppercase tracking-wider">Gauche</p>
                <button onclick={addLeft}
                  class="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-300 hover:text-zinc-100 text-sm font-medium transition-colors">
                  <i class="fas fa-arrow-left text-red-500"></i>
                  Ajouter un point
                </button>
                <button onclick={addRetourLeft}
                  class="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-400 hover:text-zinc-200 text-xs font-medium transition-colors">
                  <i class="fas fa-arrow-left text-orange-500"></i>
                  Retour (pli écrasé)
                </button>
              </div>
              <div class="space-y-2">
                <p class="text-xs text-zinc-500 uppercase tracking-wider text-right">Droite</p>
                <button onclick={addRight}
                  class="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-300 hover:text-zinc-100 text-sm font-medium transition-colors">
                  Ajouter un point
                  <i class="fas fa-arrow-right text-red-500"></i>
                </button>
                <button onclick={addRetourRight}
                  class="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-400 hover:text-zinc-200 text-xs font-medium transition-colors">
                  Retour (pli écrasé)
                  <i class="fas fa-arrow-right text-orange-500"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <p class="text-xs text-zinc-500 uppercase tracking-wider mb-3">
              Profil — {segments.length} segment{segments.length > 1 ? 's' : ''}, {bends.length} pli{bends.length > 1 ? 's' : ''}
            </p>
            <div class="space-y-2">
              {#each segments as seg, i (seg.id)}
                <div class="flex items-center gap-3 bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-2.5">
                  <span class="text-xs text-zinc-500 w-14 flex-shrink-0">Seg. {i + 1}</span>
                  <div class="flex items-center gap-2 flex-1">
                    <input type="number" min="5" max="3000" step="5"
                      bind:value={seg.length} class="w-24 {inp}">
                    <span class="text-zinc-500 text-xs">mm</span>
                  </div>
                  <button
                    onclick={() => removeSegment(i)}
                    disabled={segments.length === 1}
                    title="Supprimer ce segment"
                    class="text-zinc-600 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                  >
                    <i class="fas fa-times text-xs"></i>
                  </button>
                </div>
                {#if i < bends.length}
                  {@const bend = bends[i]}
                  <div class="flex items-center gap-2 ml-5 bg-zinc-950/60 border border-zinc-800 rounded-lg px-3 py-2">
                    <i class="fas fa-angle-right text-red-500 text-xs flex-shrink-0"></i>
                    <select bind:value={bend.type} class="{inp2}">
                      <option value="pli">Pli</option>
                      <option value="pli_ecrase">Pli écrasé (180°)</option>
                    </select>
                    {#if bend.type === 'pli'}
                      <div class="flex items-center gap-1">
                        <input type="number" min="10" max="175" step="5"
                          bind:value={bend.angle} class="w-14 {inp2}">
                        <span class="text-zinc-600 text-xs">°</span>
                      </div>
                    {/if}
                    <select bind:value={bend.direction} class="{inp2}">
                      <option value="up">↑ Haut</option>
                      <option value="down">↓ Bas</option>
                    </select>
                    <button
                      onclick={() => removeBend(i)}
                      title="Supprimer ce pli"
                      class="ml-auto text-zinc-700 hover:text-red-500 transition-colors flex-shrink-0"
                    >
                      <i class="fas fa-times text-xs"></i>
                    </button>
                  </div>
                {/if}
              {/each}
            </div>
          </div>
        </div>
      {/if}

      <!-- ── Step 3: Profondeur ─────────────────────────────── -->
      {#if step === 3}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-5">
          <h2 class="text-zinc-100 font-semibold flex items-center gap-2">
            <i class="fas fa-ruler-combined text-red-500 text-sm"></i>
            Profondeur de la pièce
          </h2>
          <p class="text-zinc-400 text-sm">
            La profondeur (largeur) est perpendiculaire à la vue de côté. C'est la dimension de la pièce dans le sens du pliage.
          </p>
          <div>
            <label for="width" class="block text-xs text-zinc-500 mb-1">Profondeur (mm)</label>
            <input id="width" type="number" min="20" max="1500" step="10"
              bind:value={design.width} class="{inp} w-full sm:w-48">
          </div>
          <div class="grid grid-cols-2 gap-3 max-w-sm">
            {#each [100, 200, 300, 500] as preset}
              <button
                onclick={() => design.width = preset}
                class="px-3 py-2 text-sm font-medium rounded border transition-colors
                  {design.width === preset
                    ? 'bg-red-600/15 border-red-600 text-red-400'
                    : 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-600'}"
              >
                {preset} mm
              </button>
            {/each}
          </div>
          <div class="border-t border-zinc-800 pt-4">
            <p class="text-xs text-zinc-500 mb-1">Aperçu de la pièce dépliée</p>
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden flex items-center justify-center p-4">
              <svg
                viewBox="-10 -10 {totalLength + 20} {design.width + 20}"
                preserveAspectRatio="xMidYMid meet"
                class="w-full"
                style="max-height: 240px;"
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect x="0" y="0" width={totalLength} height={design.width}
                  fill="#3f3f46" stroke="#a1a1aa" stroke-width="1"/>
                <!-- bend lines -->
                {#each segments as seg, i}
                  {#if i < segments.length - 1}
                    {@const xb = segments.slice(0, i + 1).reduce((s, sg) => s + sg.length, 0)}
                    <line x1={xb} y1="0" x2={xb} y2={design.width}
                      stroke="#dc2626" stroke-width="1" stroke-dasharray="4 3" opacity="0.7"/>
                  {/if}
                {/each}
              </svg>
            </div>
            <div class="text-xs text-zinc-500 mt-2 flex justify-between">
              <span>Longueur développée : {totalLength} mm</span>
              <span>Profondeur : {design.width} mm</span>
            </div>
          </div>
        </div>
      {/if}

      <!-- ── Step 4: Opérations sur pièce dépliée ───────────── -->
      {#if step === 4}
        <div class="space-y-4">

          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <h2 class="text-zinc-100 font-semibold flex items-center gap-2 mb-2">
              <i class="fas fa-wrench text-red-500 text-sm"></i>
              Perçages & découpes
            </h2>
            <p class="text-zinc-500 text-xs mb-4">
              Les coordonnées (X, Y) sont mesurées depuis le coin <strong class="text-zinc-300">haut-gauche</strong> de la pièce dépliée.
              X = position le long de la longueur, Y = position dans la profondeur.
            </p>
            <div class="grid grid-cols-2 gap-2">
              {#each [['poincon', 'Perçage', 'fa-circle'], ['decoupe', 'Découpe', 'fa-vector-square']] as [type, label, icon]}
                <button
                  type="button"
                  onclick={() => addExtra(type)}
                  class="flex items-center justify-center gap-2 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 hover:border-zinc-600 rounded text-zinc-300 hover:text-zinc-100 text-sm font-medium transition-colors"
                >
                  <i class="fas {icon} text-red-500 text-sm"></i>
                  {label}
                </button>
              {/each}
            </div>
          </div>

          <!-- Unfolded view with operations -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <div class="flex items-center justify-between mb-3">
              <p class="text-xs text-zinc-500 uppercase tracking-wider">Pièce dépliée</p>
              <span class="text-xs text-zinc-600">{totalLength} × {design.width} mm</span>
            </div>
            <div class="bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden p-3">
              <svg
                viewBox="-20 -20 {totalLength + 40} {design.width + 40}"
                preserveAspectRatio="xMidYMid meet"
                class="w-full"
                style="max-height: 320px;"
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect x="0" y="0" width={totalLength} height={design.width}
                  fill="#3f3f46" stroke="#a1a1aa" stroke-width="1"/>
                <!-- bend lines -->
                {#each segments as seg, i}
                  {#if i < segments.length - 1}
                    {@const xb = segments.slice(0, i + 1).reduce((s, sg) => s + sg.length, 0)}
                    <line x1={xb} y1="0" x2={xb} y2={design.width}
                      stroke="#dc2626" stroke-width="1" stroke-dasharray="4 3" opacity="0.7"/>
                  {/if}
                {/each}
                <!-- top-left origin marker -->
                <circle cx="0" cy="0" r="3" fill="#22c55e"/>
                <text x="6" y="-4" font-size="10" fill="#22c55e" font-family="monospace">(0,0)</text>

                <!-- holes -->
                {#each extras.filter(e => e.type === 'poincon') as op}
                  <circle cx={op.x} cy={op.y} r={(op.diameter || 0) / 2}
                    fill="#09090b" stroke="#fbbf24" stroke-width="1"/>
                {/each}
                <!-- notches -->
                {#each extras.filter(e => e.type === 'decoupe') as op}
                  <rect x={op.x} y={op.y} width={op.w} height={op.h}
                    fill="#09090b" stroke="#f87171" stroke-width="1" stroke-dasharray="3 2"/>
                {/each}
              </svg>
            </div>
            <div class="flex items-center gap-4 mt-3 text-xs text-zinc-500">
              <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-green-500"></span>Origine (0,0)</span>
              <span class="flex items-center gap-1.5"><span class="w-3 h-px bg-red-600"></span>Ligne de pli</span>
              <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full border border-amber-400"></span>Perçage</span>
              <span class="flex items-center gap-1.5"><span class="w-2 h-2 border border-red-400"></span>Découpe</span>
            </div>
          </div>

          <!-- Operation list -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <p class="text-xs text-zinc-500 uppercase tracking-wider mb-3">
              Opérations ({extras.length})
            </p>
            {#if extras.length === 0}
              <p class="text-zinc-600 text-sm text-center py-6">
                Aucune opération. Ajoutez un perçage ou une découpe.
              </p>
            {:else}
              <div class="space-y-3">
                {#each extras as op (op.id)}
                  <div class="bg-zinc-800/50 border border-zinc-700 rounded-lg p-3">
                    <div class="flex items-center justify-between mb-3">
                      <span class="text-zinc-100 text-sm font-medium flex items-center gap-2">
                        <i class="fas {op.type === 'poincon' ? 'fa-circle text-amber-400' : 'fa-vector-square text-red-400'} text-xs"></i>
                        {op.type === 'poincon' ? 'Perçage' : 'Découpe'}
                      </span>
                      <button
                        onclick={() => removeExtra(op.id)}
                        class="text-zinc-500 hover:text-red-500 transition-colors"
                        aria-label="Supprimer"
                      >
                        <i class="fas fa-trash text-xs"></i>
                      </button>
                    </div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      <label class="text-xs text-zinc-500 flex flex-col gap-1">
                        X (mm)
                        <input type="number" min="0" max={totalLength} step="1"
                          bind:value={op.x} class="{inp}">
                      </label>
                      <label class="text-xs text-zinc-500 flex flex-col gap-1">
                        Y (mm)
                        <input type="number" min="0" max={design.width} step="1"
                          bind:value={op.y} class="{inp}">
                      </label>
                      {#if op.type === 'poincon'}
                        <label class="text-xs text-zinc-500 flex flex-col gap-1 col-span-2">
                          Ø (mm)
                          <input type="number" min="2" max="50" step="0.5"
                            bind:value={op.diameter} class="{inp}">
                        </label>
                      {:else}
                        <label class="text-xs text-zinc-500 flex flex-col gap-1">
                          Largeur (mm)
                          <input type="number" min="2" max={totalLength} step="1"
                            bind:value={op.w} class="{inp}">
                        </label>
                        <label class="text-xs text-zinc-500 flex flex-col gap-1">
                          Hauteur (mm)
                          <input type="number" min="2" max={design.width} step="1"
                            bind:value={op.h} class="{inp}">
                        </label>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      {/if}

      <!-- ── Step 5: Devis ──────────────────────────────────── -->
      {#if step === 5}
        <div class="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
          {#if quoteStatus === 'success'}
            <div class="text-center py-8">
              <div class="w-14 h-14 bg-green-600/20 border border-green-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-check text-green-400 text-xl"></i>
              </div>
              <h3 class="text-zinc-100 font-semibold text-lg mb-2">Demande envoyée !</h3>
              <p class="text-zinc-400 text-sm mb-6">Nous vous répondrons sous 24 h avec un devis définitif.</p>
              <button
                onclick={() => { quoteStatus = null; step = 1; }}
                class="bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-2.5 rounded transition-colors"
              >
                Concevoir une autre pièce
              </button>
            </div>
          {:else}
            <h2 class="text-zinc-100 font-semibold flex items-center gap-2 mb-1">
              <i class="fas fa-paper-plane text-red-500 text-sm"></i>
              Demander un devis
            </h2>
            <p class="text-zinc-400 text-sm mb-5">
              Estimation : <span class="text-red-500 font-semibold">{pricing.total.toFixed(2)} €</span>
              · {totalLength} × {design.width} mm · {materials[design.material].label} · {bends.length} pli{bends.length > 1 ? 's' : ''}
            </p>

            <form onsubmit={submitQuote} class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label for="q-nom" class="block text-sm text-zinc-300 mb-1.5">
                    Nom <span class="text-red-500">*</span>
                  </label>
                  <input id="q-nom" type="text" bind:value={quote.nom} required
                    class="w-full {inp} px-4 py-2.5 rounded-lg">
                </div>
                <div>
                  <label for="q-email" class="block text-sm text-zinc-300 mb-1.5">
                    Email <span class="text-red-500">*</span>
                  </label>
                  <input id="q-email" type="email" bind:value={quote.email} required
                    class="w-full {inp} px-4 py-2.5 rounded-lg">
                </div>
              </div>
              <div>
                <label for="q-tel" class="block text-sm text-zinc-300 mb-1.5">Téléphone</label>
                <input id="q-tel" type="tel" bind:value={quote.telephone}
                  class="w-full {inp} px-4 py-2.5 rounded-lg">
              </div>
              <div>
                <label for="q-notes" class="block text-sm text-zinc-300 mb-1.5">Notes (quantité, contraintes, délai…)</label>
                <textarea id="q-notes" bind:value={quote.notes} rows="3"
                  class="w-full {inp} px-4 py-2.5 rounded-lg resize-none"
                  placeholder="Quantité souhaitée, traitement de surface, délai particulier…"
                ></textarea>
              </div>

              {#if quoteStatus === 'error'}
                <p class="text-red-400 text-sm bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
                  <i class="fas fa-exclamation-circle mr-2"></i>{quoteError}
                </p>
              {/if}

              <button
                type="submit"
                disabled={quoteStatus === 'sending'}
                class="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3 rounded transition-colors"
              >
                {#if quoteStatus === 'sending'}
                  <i class="fas fa-spinner fa-spin"></i> Envoi en cours…
                {:else}
                  <i class="fas fa-paper-plane text-sm"></i> Envoyer la demande
                {/if}
              </button>
            </form>
          {/if}
        </div>
      {/if}

      <!-- Step navigation -->
      {#if quoteStatus !== 'success'}
        <div class="flex justify-between mt-5">
          <button
            onclick={() => step > 1 && step--}
            disabled={step === 1}
            class="flex items-center gap-2 px-4 py-2 border border-zinc-700 hover:border-zinc-500 text-zinc-400 hover:text-zinc-200 rounded transition-colors text-sm disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <i class="fas fa-chevron-left text-xs"></i>
            Précédent
          </button>
          {#if step < STEPS.length}
            <button
              onclick={() => step++}
              class="flex items-center gap-2 px-5 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded transition-colors text-sm"
            >
              Suivant
              <i class="fas fa-chevron-right text-xs"></i>
            </button>
          {/if}
        </div>
      {/if}

    </div>
  </div>
</section>
