<script>
  const materials = {
    acier:     { label: 'Acier',           sub: 'Standard · 7.85 g/cm³',  price: 1.5, density: 7.85 },
    galvanise: { label: 'Acier galvanisé', sub: 'Anti-corrosion · 7.85 g/cm³', price: 1.8, density: 7.85 },
    aluminium: { label: 'Aluminium',       sub: 'Léger · 2.70 g/cm³',     price: 4.0, density: 2.70 },
    inox:      { label: 'Inox',            sub: 'Haute qualité · 7.90 g/cm³', price: 6.0, density: 7.90 }
  };

  const BASE_COST = 25;
  const MIN_COST  = 30;
  const opPrices  = { pli: 3, pli_ecrase: 5, poincon: 1.5, decoupe: 4 };

  let _id = 0;
  const uid = () => ++_id;

  let step = $state(1);
  let design = $state({ material: 'acier', thickness: 1.5, width: 200 });
  let segments = $state([{ id: uid(), length: 200 }]);
  let bends    = $state([]);
  let extras   = $state([]);
  let zoom     = $state(1);

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
    const ns = [...segments], nb = [...bends];
    ns.splice(idx, 1);
    const bi = idx < bends.length ? idx : idx - 1;
    if (bi >= 0) nb.splice(bi, 1);
    segments = ns; bends = nb;
  }
  function removeBend(idx) {
    const ns = [...segments], nb = [...bends];
    ns[idx] = { ...ns[idx], length: ns[idx].length + ns[idx + 1].length };
    ns.splice(idx + 1, 1);
    nb.splice(idx, 1);
    segments = ns; bends = nb;
  }
  function addExtra(type) {
    const cx = Math.round(totalLength / 2);
    const cy = Math.round(design.width / 2);
    extras = [...extras,
      type === 'poincon'
        ? { id: uid(), type, x: cx, y: cy, diameter: 8 }
        : { id: uid(), type, x: cx - 15, y: cy - 7.5, w: 30, h: 15 }
    ];
  }
  function removeExtra(id) { extras = extras.filter(e => e.id !== id); }

  // ── Geometry ──────────────────────────────────────────────
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
          a += Math.PI;
          const nx = Math.cos(a + (b.direction === 'up' ? -Math.PI / 2 : Math.PI / 2));
          const ny = Math.sin(a + (b.direction === 'up' ? -Math.PI / 2 : Math.PI / 2));
          x += nx * t; y += ny * t;
        } else {
          a += (b.direction === 'up' ? -1 : 1) * (b.angle || 90) * Math.PI / 180;
        }
      }
    }
    return { points, segData };
  });

  let viewBox = $derived.by(() => {
    const xs = geometry.points.map(p => p.x);
    const ys = geometry.points.map(p => p.y);
    const pad = Math.max(60, design.thickness * 5);
    const w0 = (Math.max(...xs) - Math.min(...xs) + pad * 2) / zoom;
    const h0 = (Math.max(...ys) - Math.min(...ys) + pad * 2) / zoom;
    const cx = (Math.min(...xs) + Math.max(...xs)) / 2;
    const cy = (Math.min(...ys) + Math.max(...ys)) / 2;
    return `${cx - w0 / 2} ${cy - h0 / 2} ${w0} ${h0}`;
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
    quoteStatus = 'sending'; quoteError = '';
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
        ? `Perçage Ø${e.diameter} mm — (${e.x}, ${e.y}) depuis coin haut-gauche`
        : `Découpe ${e.w}×${e.h} mm — coin (${e.x}, ${e.y}) depuis coin haut-gauche`);
    }
    const message = `
<strong>Devis designer — TC Pliage</strong><br><br>
Nom : ${quote.nom}<br>Email : ${quote.email}<br>
Téléphone : ${quote.telephone || '—'}<br>
Notes : ${quote.notes ? quote.notes.replace(/\n/g, '<br>') : '—'}<br><br>
<strong>Pièce</strong><br>
${materials[design.material].label} — ép. ${design.thickness} mm — larg. ${design.width} mm<br>
Longueur développée : ${totalLength} mm — Poids : ${pricing.kg.toFixed(3)} kg — Plis : ${bends.length}<br><br>
<pre style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px">${lines.join('\n')}</pre>
`.trim();
    try {
      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          replyTo: quote.email,
          subject: `Devis — ${materials[design.material].label} ${totalLength}×${design.width}×${design.thickness} mm`,
          message,
          estimatedCost: pricing.total.toFixed(2),
          designData: JSON.stringify({ design, segments, bends, extras }, null, 2),
          submittedAt: new Date().toISOString()
        })
      });
      if (!res.ok) throw new Error();
      quoteStatus = 'success';
    } catch {
      quoteStatus = 'error';
      quoteError = "L'envoi a échoué. Merci de nous contacter directement par téléphone.";
    }
  }

  const STEPS = [
    { n: 1, label: 'Matériau'    },
    { n: 2, label: 'Profil'      },
    { n: 3, label: 'Profondeur'  },
    { n: 4, label: 'Opérations'  },
    { n: 5, label: 'Devis'       }
  ];
</script>

<svelte:head>
  <title>Designer — TC Pliage</title>
</svelte:head>

<!-- ── Page header ──────────────────────────────────────────── -->
<section class="relative border-b border-zinc-800/60 overflow-hidden">
  <div class="absolute inset-0 bg-gradient-to-br from-zinc-950 via-zinc-950 to-red-950/30 pointer-events-none"></div>
  <div class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-red-600/30 to-transparent"></div>
  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex items-start gap-5">
      <div class="w-12 h-12 bg-red-600/10 border border-red-600/20 rounded-2xl flex items-center justify-center flex-shrink-0 mt-0.5">
        <i class="fas fa-draw-polygon text-red-500"></i>
      </div>
      <div>
        <p class="text-red-500/80 text-xs font-semibold uppercase tracking-[0.15em] mb-1">Outil de conception</p>
        <h1 class="text-3xl sm:text-4xl font-bold text-zinc-100 tracking-tight">Concevoir une pièce</h1>
        <p class="text-zinc-500 mt-2 text-sm max-w-xl leading-relaxed">
          Dessinez votre profil point par point, définissez la profondeur, placez perçages et découpes, puis obtenez un devis instantané.
        </p>
      </div>
    </div>
  </div>
</section>

<!-- ── Main layout ──────────────────────────────────────────── -->
<section class="py-8">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">

    <!-- ─────────────── LEFT PANEL ─────────────────────────── -->
    <div class="lg:col-span-2 space-y-4 lg:sticky lg:top-6">

      <!-- Side-profile preview -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl shadow-black/40">
        <!-- SVG area (no padding) -->
        <div class="relative aspect-square bg-zinc-950 overflow-hidden">
          <svg {viewBox} preserveAspectRatio="xMidYMid meet"
            class="w-full h-full"
            xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="minor" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#27272a" stroke-width="0.4"/>
              </pattern>
              <pattern id="major" width="100" height="100" patternUnits="userSpaceOnUse">
                <rect width="100" height="100" fill="url(#minor)"/>
                <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#3f3f46" stroke-width="0.8"/>
              </pattern>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur"/>
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>
            <rect x="-10000" y="-10000" width="20000" height="20000" fill="url(#major)"/>

            <!-- Profile stroke (thickness = actual mm × 4 for visibility) -->
            <path d={pathD} fill="none" stroke="#52525b"
              stroke-width={design.thickness * 4 + 2}
              stroke-linejoin="round" stroke-linecap="round"/>
            <path d={pathD} fill="none" stroke="#d4d4d8"
              stroke-width={design.thickness * 4}
              stroke-linejoin="round" stroke-linecap="round"/>

            <!-- Bend markers -->
            {#each bends as bend, i}
              {@const px = geometry.points[i + 1].x}
              {@const py = geometry.points[i + 1].y}
              {@const isEcrase = bend.type === 'pli_ecrase'}
              <circle cx={px} cy={py} r={design.thickness * 4} fill={isEcrase ? '#f97316' : '#dc2626'} opacity="0.15" filter="url(#glow)"/>
              <circle cx={px} cy={py} r={design.thickness * 2.5} fill={isEcrase ? '#f97316' : '#dc2626'} opacity="0.9"/>
              <circle cx={px} cy={py} r={design.thickness * 1.2} fill="white" opacity="0.9"/>
            {/each}

            <!-- Start / end anchors -->
            {#if geometry.points.length}
              {@const sp = geometry.points[0]}
              {@const ep = geometry.points.at(-1)}
              <circle cx={sp.x} cy={sp.y} r={Math.max(5, design.thickness * 2.5)} fill="#22c55e" opacity="0.9"/>
              <circle cx={ep.x} cy={ep.y} r={Math.max(5, design.thickness * 2.5)} fill="#3b82f6" opacity="0.9"/>
            {/if}
          </svg>

          <!-- Edge gradient overlay for depth -->
          <div class="absolute inset-0 pointer-events-none"
            style="background: radial-gradient(ellipse at center, transparent 60%, rgba(9,9,11,0.6) 100%)"></div>

          <!-- Zoom controls overlay -->
          <div class="absolute bottom-3 right-3 flex items-center gap-1 bg-zinc-900/90 backdrop-blur border border-zinc-700/60 rounded-xl p-1">
            <button
              onclick={() => zoom = Math.max(0.25, +(zoom / 1.25).toFixed(2))}
              class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700/60 transition-all"
              aria-label="Dézoomer"
            ><i class="fas fa-minus text-xs"></i></button>
            <button
              onclick={() => zoom = 1}
              class="px-2 h-7 text-xs font-mono text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700/60 rounded-lg transition-all tabular-nums"
            >{Math.round(zoom * 100)}%</button>
            <button
              onclick={() => zoom = Math.min(8, +(zoom * 1.25).toFixed(2))}
              class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-700/60 transition-all"
              aria-label="Zoomer"
            ><i class="fas fa-plus text-xs"></i></button>
          </div>

          <!-- Top-left label -->
          <div class="absolute top-3 left-3 flex items-center gap-2">
            <span class="bg-zinc-900/80 backdrop-blur border border-zinc-700/40 text-zinc-500 text-xs px-2.5 py-1 rounded-lg font-medium tracking-wide">
              Vue de côté
            </span>
          </div>
        </div>

        <!-- Legend -->
        <div class="px-4 py-3 flex items-center gap-4 border-t border-zinc-800/60">
          <span class="flex items-center gap-1.5 text-xs text-zinc-500">
            <span class="w-2 h-2 rounded-full bg-green-500"></span>Début
          </span>
          <span class="flex items-center gap-1.5 text-xs text-zinc-500">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>Fin
          </span>
          <span class="flex items-center gap-1.5 text-xs text-zinc-500">
            <span class="w-2 h-2 rounded-full bg-red-600"></span>Pli
          </span>
          <span class="flex items-center gap-1.5 text-xs text-zinc-500">
            <span class="w-2 h-2 rounded-full bg-orange-500"></span>Pli écrasé
          </span>
        </div>
      </div>

      <!-- Price card -->
      <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl shadow-black/30">
        <div class="p-5 border-b border-zinc-800/60">
          <p class="text-zinc-500 text-xs font-medium uppercase tracking-[0.1em] mb-3">Estimation tarifaire</p>
          <div class="flex items-end justify-between">
            <span class="text-4xl font-bold text-zinc-100 tabular-nums">{pricing.total.toFixed(2)}<span class="text-2xl text-zinc-400 ml-1">€</span></span>
            <span class="text-xs text-zinc-500 text-right leading-relaxed">
              Indicatif<br>Devis sous 24 h
            </span>
          </div>
        </div>
        <div class="p-5 space-y-2.5">
          {#each [
            ['Matière', `${pricing.kg.toFixed(3)} kg × ${materials[design.material].price} €/kg`, pricing.mat.toFixed(2)],
            ['Opérations', `${bends.length + extras.length} opération${bends.length + extras.length > 1 ? 's' : ''}`, pricing.ops.toFixed(2)],
            ['Frais de mise en route', '', BASE_COST.toFixed(2)]
          ] as [label, detail, val]}
            <div class="flex items-start justify-between gap-2">
              <div>
                <p class="text-zinc-300 text-sm">{label}</p>
                {#if detail}<p class="text-zinc-600 text-xs mt-0.5">{detail}</p>{/if}
              </div>
              <span class="text-zinc-400 text-sm tabular-nums flex-shrink-0 font-mono">{val} €</span>
            </div>
          {/each}
          <div class="border-t border-zinc-800 pt-2.5 flex items-center justify-between text-xs text-zinc-600 font-mono">
            <span>Longueur dév. · Profondeur</span>
            <span>{totalLength} × {design.width} mm</span>
          </div>
        </div>
        <div class="px-5 pb-5">
          <button
            onclick={() => step = 5}
            class="w-full bg-red-600 hover:bg-red-500 text-white font-semibold py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-red-900/30"
          >
            <i class="fas fa-paper-plane text-sm"></i>
            Demander un devis
          </button>
        </div>
      </div>
    </div>

    <!-- ─────────────── RIGHT PANEL ────────────────────────── -->
    <div class="lg:col-span-3 space-y-5">

      <!-- Step indicator -->
      <div class="bg-zinc-900/60 border border-zinc-800/60 rounded-2xl p-4">
        <div class="flex items-center">
          {#each STEPS as s, idx}
            <button
              onclick={() => step = s.n}
              class="flex flex-col items-center gap-1.5 group flex-shrink-0 cursor-pointer"
            >
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-200 {
                step > s.n
                  ? 'bg-green-600/20 border border-green-600/50 text-green-400'
                  : step === s.n
                    ? 'bg-red-600 text-white shadow-lg shadow-red-900/40'
                    : 'bg-zinc-800 border border-zinc-700 text-zinc-500 group-hover:border-zinc-500 group-hover:text-zinc-300'
              }">
                {#if step > s.n}
                  <i class="fas fa-check text-xs"></i>
                {:else}
                  {s.n}
                {/if}
              </div>
              <span class="text-xs transition-colors duration-200 hidden sm:block {
                step === s.n ? 'text-zinc-200 font-medium' : step > s.n ? 'text-zinc-500' : 'text-zinc-600 group-hover:text-zinc-400'
              }">{s.label}</span>
            </button>
            {#if idx < STEPS.length - 1}
              <div class="flex-1 mx-1.5 sm:mx-2 mb-5 sm:mb-4 h-px transition-colors duration-300 {step > s.n ? 'bg-green-600/30' : 'bg-zinc-800'}"></div>
            {/if}
          {/each}
        </div>
      </div>

      <!-- ── Step 1: Matériau ───────────────────────────────── -->
      {#if step === 1}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-zinc-100 mb-0.5">Matériau</h2>
            <p class="text-zinc-500 text-sm">Choisissez le matériau qui correspond à votre besoin.</p>
          </div>

          <div class="grid grid-cols-2 gap-3">
            {#each Object.entries(materials) as [key, m]}
              <button
                type="button"
                onclick={() => design.material = key}
                class="group relative text-left p-4 rounded-xl border transition-all duration-200 {
                  design.material === key
                    ? 'bg-red-600/10 border-red-600/60 shadow-lg shadow-red-900/20'
                    : 'bg-zinc-800/40 border-zinc-700/60 hover:bg-zinc-800 hover:border-zinc-600'
                }"
              >
                {#if design.material === key}
                  <span class="absolute top-3 right-3 w-2 h-2 rounded-full bg-red-500"></span>
                {/if}
                <p class="font-semibold text-sm {design.material === key ? 'text-zinc-100' : 'text-zinc-300'}">{m.label}</p>
                <p class="text-xs mt-1 {design.material === key ? 'text-red-400/80' : 'text-zinc-600'}">{m.sub}</p>
                <p class="text-xs mt-2 font-mono {design.material === key ? 'text-red-400' : 'text-zinc-500'}">{m.price} €/kg</p>
              </button>
            {/each}
          </div>

          <div class="pt-2 border-t border-zinc-800">
            <label for="thickness" class="block text-sm font-medium text-zinc-300 mb-3">
              Épaisseur de la tôle
            </label>
            <div class="flex items-center gap-4">
              <div class="relative">
                <input id="thickness" type="number" min="0.5" max="10" step="0.1"
                  bind:value={design.thickness}
                  class="w-32 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 text-lg font-mono font-bold focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 transition-all">
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-sm pointer-events-none">mm</span>
              </div>
              <div class="flex gap-2">
                {#each [0.8, 1.5, 2, 3] as t}
                  <button
                    onclick={() => design.thickness = t}
                    class="px-3 py-2 text-xs font-mono rounded-lg border transition-all {
                      design.thickness == t
                        ? 'bg-red-600/15 border-red-600/60 text-red-400'
                        : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200'
                    }"
                  >{t}</button>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- ── Step 2: Profil ─────────────────────────────────── -->
      {#if step === 2}
        <div class="space-y-4">

          <!-- Add point actions -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <div class="mb-4">
              <h2 class="text-lg font-semibold text-zinc-100 mb-0.5">Dessiner le profil</h2>
              <p class="text-zinc-500 text-sm">Ajoutez des points pour étendre le profil dans la direction souhaitée.</p>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <!-- Left side -->
              <div class="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4 space-y-2">
                <div class="flex items-center gap-2 mb-3">
                  <div class="w-6 h-6 bg-zinc-700 rounded-full flex items-center justify-center">
                    <i class="fas fa-arrow-left text-zinc-300 text-xs"></i>
                  </div>
                  <span class="text-sm font-medium text-zinc-300">Gauche</span>
                </div>
                <button onclick={addLeft}
                  class="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-zinc-700/60 hover:bg-red-600/20 border border-zinc-600 hover:border-red-600/50 rounded-lg text-zinc-300 hover:text-red-300 text-sm font-medium transition-all duration-200">
                  <span>Pli normal</span>
                  <i class="fas fa-plus text-xs opacity-70"></i>
                </button>
                <button onclick={addRetourLeft}
                  class="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-zinc-700/60 hover:bg-orange-600/20 border border-zinc-600 hover:border-orange-600/50 rounded-lg text-zinc-400 hover:text-orange-300 text-xs font-medium transition-all duration-200">
                  <span>Retour (écrasé)</span>
                  <i class="fas fa-plus text-xs opacity-70"></i>
                </button>
              </div>
              <!-- Right side -->
              <div class="bg-zinc-800/50 border border-zinc-700/50 rounded-xl p-4 space-y-2">
                <div class="flex items-center justify-end gap-2 mb-3">
                  <span class="text-sm font-medium text-zinc-300">Droite</span>
                  <div class="w-6 h-6 bg-zinc-700 rounded-full flex items-center justify-center">
                    <i class="fas fa-arrow-right text-zinc-300 text-xs"></i>
                  </div>
                </div>
                <button onclick={addRight}
                  class="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-zinc-700/60 hover:bg-red-600/20 border border-zinc-600 hover:border-red-600/50 rounded-lg text-zinc-300 hover:text-red-300 text-sm font-medium transition-all duration-200">
                  <i class="fas fa-plus text-xs opacity-70"></i>
                  <span>Pli normal</span>
                </button>
                <button onclick={addRetourRight}
                  class="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-zinc-700/60 hover:bg-orange-600/20 border border-zinc-600 hover:border-orange-600/50 rounded-lg text-zinc-400 hover:text-orange-300 text-xs font-medium transition-all duration-200">
                  <i class="fas fa-plus text-xs opacity-70"></i>
                  <span>Retour (écrasé)</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Segment / bend chain -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-sm font-semibold text-zinc-200">Profil</h3>
                <p class="text-xs text-zinc-600 mt-0.5">{segments.length} segment{segments.length > 1 ? 's' : ''} · {bends.length} pli{bends.length > 1 ? 's' : ''} · {totalLength} mm développés</p>
              </div>
            </div>

            <div class="space-y-1.5">
              {#each segments as seg, i (seg.id)}
                <!-- Segment -->
                <div class="group flex items-center gap-3 bg-zinc-800/40 hover:bg-zinc-800/70 border border-zinc-700/50 rounded-xl px-4 py-3 transition-all">
                  <div class="w-2 h-2 rounded-sm bg-zinc-500 flex-shrink-0"></div>
                  <span class="text-xs text-zinc-500 w-12 flex-shrink-0 font-mono">Seg {i + 1}</span>
                  <div class="flex-1 flex items-center gap-2">
                    <input type="number" min="5" max="3000" step="5" bind:value={seg.length}
                      class="w-24 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 text-zinc-100 text-sm font-mono focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all">
                    <span class="text-zinc-600 text-xs">mm</span>
                  </div>
                  <button
                    onclick={() => removeSegment(i)}
                    disabled={segments.length === 1}
                    class="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded-lg text-zinc-600 hover:text-red-500 hover:bg-red-500/10 disabled:opacity-0 transition-all"
                  ><i class="fas fa-times text-xs"></i></button>
                </div>

                <!-- Bend -->
                {#if i < bends.length}
                  {@const bend = bends[i]}
                  <div class="group flex items-center gap-3 ml-4 bg-zinc-900/60 border border-zinc-800/80 rounded-xl px-4 py-2.5 transition-all">
                    <div class="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 {bend.type === 'pli_ecrase' ? 'bg-orange-600/20 border border-orange-600/40' : 'bg-red-600/20 border border-red-600/40'}">
                      <span class="text-xs {bend.type === 'pli_ecrase' ? 'text-orange-400' : 'text-red-400'}">↗</span>
                    </div>
                    <select bind:value={bend.type}
                      class="bg-zinc-800 border border-zinc-700/60 rounded-lg px-2 py-1 text-zinc-300 text-xs focus:outline-none focus:border-red-600 transition-all">
                      <option value="pli">Pli</option>
                      <option value="pli_ecrase">Pli écrasé</option>
                    </select>
                    {#if bend.type === 'pli'}
                      <div class="flex items-center gap-1.5">
                        <input type="number" min="10" max="175" step="5" bind:value={bend.angle}
                          class="w-16 bg-zinc-800 border border-zinc-700/60 rounded-lg px-2 py-1 text-zinc-100 text-xs font-mono focus:outline-none focus:border-red-600 transition-all">
                        <span class="text-zinc-600 text-xs">°</span>
                      </div>
                    {/if}
                    <select bind:value={bend.direction}
                      class="bg-zinc-800 border border-zinc-700/60 rounded-lg px-2 py-1 text-zinc-300 text-xs focus:outline-none focus:border-red-600 transition-all">
                      <option value="up">↑ Haut</option>
                      <option value="down">↓ Bas</option>
                    </select>
                    <button
                      onclick={() => removeBend(i)}
                      class="ml-auto opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded-lg text-zinc-600 hover:text-red-500 hover:bg-red-500/10 transition-all"
                    ><i class="fas fa-times text-xs"></i></button>
                  </div>
                {/if}
              {/each}
            </div>
          </div>
        </div>
      {/if}

      <!-- ── Step 3: Profondeur ─────────────────────────────── -->
      {#if step === 3}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-6">
          <div>
            <h2 class="text-lg font-semibold text-zinc-100 mb-0.5">Profondeur de la pièce</h2>
            <p class="text-zinc-500 text-sm">Dimension perpendiculaire au profil — dans le sens du pliage.</p>
          </div>

          <div class="flex items-center gap-4">
            <div class="relative">
              <input id="width" type="number" min="20" max="1500" step="10"
                bind:value={design.width}
                class="w-36 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 text-2xl font-mono font-bold focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/30 transition-all">
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-sm pointer-events-none">mm</span>
            </div>
            <div class="flex gap-2 flex-wrap">
              {#each [50, 100, 200, 300, 500] as p}
                <button
                  onclick={() => design.width = p}
                  class="px-3 py-2 text-xs font-mono rounded-lg border transition-all {
                    design.width === p
                      ? 'bg-red-600/15 border-red-600/60 text-red-400'
                      : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200'
                  }"
                >{p}</button>
              {/each}
            </div>
          </div>

          <!-- Developed piece preview -->
          <div class="rounded-xl border border-zinc-800 overflow-hidden">
            <div class="px-4 py-2.5 border-b border-zinc-800 flex items-center justify-between bg-zinc-800/30">
              <span class="text-xs text-zinc-500 font-medium">Aperçu — pièce dépliée</span>
              <span class="text-xs text-zinc-600 font-mono">{totalLength} × {design.width} mm</span>
            </div>
            <div class="bg-zinc-950 p-6 flex items-center justify-center" style="min-height: 180px;">
              <svg
                viewBox="-12 -12 {Math.max(totalLength + 24, 1)} {Math.max(design.width + 24, 1)}"
                preserveAspectRatio="xMidYMid meet"
                class="w-full"
                style="max-height: 200px;"
                xmlns="http://www.w3.org/2000/svg"
              >
                <rect x="0" y="0" width={totalLength} height={design.width} fill="#3f3f46" stroke="#71717a" stroke-width="1" rx="0"/>
                <!-- Fold lines -->
                {#each segments as seg, i}
                  {#if i < segments.length - 1}
                    {@const xb = segments.slice(0, i + 1).reduce((s, sg) => s + sg.length, 0)}
                    <line x1={xb} y1="0" x2={xb} y2={design.width} stroke="#ef4444" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.6"/>
                  {/if}
                {/each}
                <!-- Dimension arrows -->
                <line x1="0" y1={design.width + 8} x2={totalLength} y2={design.width + 8} stroke="#52525b" stroke-width="0.8" marker-end="url(#arrow)"/>
                <text x={totalLength / 2} y={design.width + 11} text-anchor="middle" font-size="8" fill="#71717a" font-family="monospace">{totalLength}</text>
              </svg>
            </div>
          </div>
        </div>
      {/if}

      <!-- ── Step 4: Opérations ──────────────────────────────── -->
      {#if step === 4}
        <div class="space-y-4">

          <!-- Add buttons -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
            <div class="mb-4">
              <h2 class="text-lg font-semibold text-zinc-100 mb-0.5">Perçages & découpes</h2>
              <p class="text-zinc-500 text-sm">Coordonnées mesurées depuis le coin <span class="text-zinc-300 font-medium">haut-gauche (0, 0)</span> de la pièce dépliée.</p>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <button onclick={() => addExtra('poincon')}
                class="group flex items-center gap-3 px-4 py-3.5 bg-zinc-800/50 hover:bg-amber-600/10 border border-zinc-700 hover:border-amber-600/40 rounded-xl text-left transition-all duration-200">
                <div class="w-8 h-8 bg-amber-600/20 border border-amber-600/30 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-amber-600/30 transition-all">
                  <i class="fas fa-circle text-amber-400 text-xs"></i>
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-200">Perçage</p>
                  <p class="text-xs text-zinc-600">Trou circulaire</p>
                </div>
              </button>
              <button onclick={() => addExtra('decoupe')}
                class="group flex items-center gap-3 px-4 py-3.5 bg-zinc-800/50 hover:bg-red-600/10 border border-zinc-700 hover:border-red-600/40 rounded-xl text-left transition-all duration-200">
                <div class="w-8 h-8 bg-red-600/20 border border-red-600/30 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-red-600/30 transition-all">
                  <i class="fas fa-vector-square text-red-400 text-xs"></i>
                </div>
                <div>
                  <p class="text-sm font-medium text-zinc-200">Découpe</p>
                  <p class="text-xs text-zinc-600">Encoche rectangulaire</p>
                </div>
              </button>
            </div>
          </div>

          <!-- Unfolded piece view -->
          <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
            <div class="px-5 py-3 border-b border-zinc-800 flex items-center justify-between bg-zinc-800/20">
              <span class="text-sm font-medium text-zinc-300">Pièce dépliée</span>
              <span class="text-xs text-zinc-600 font-mono">{totalLength} × {design.width} mm</span>
            </div>
            <div class="bg-zinc-950 p-4">
              <svg
                viewBox="-22 -22 {Math.max(totalLength + 44, 1)} {Math.max(design.width + 44, 1)}"
                preserveAspectRatio="xMidYMid meet"
                class="w-full"
                style="max-height: 300px;"
                xmlns="http://www.w3.org/2000/svg"
              >
                <!-- Background -->
                <rect x="0" y="0" width={totalLength} height={design.width}
                  fill="#27272a" stroke="#52525b" stroke-width="1"/>
                <!-- Fold lines -->
                {#each segments as seg, i}
                  {#if i < segments.length - 1}
                    {@const xb = segments.slice(0, i + 1).reduce((s, sg) => s + sg.length, 0)}
                    <line x1={xb} y1="0" x2={xb} y2={design.width}
                      stroke="#ef4444" stroke-width="0.8" stroke-dasharray="4 3" opacity="0.5"/>
                  {/if}
                {/each}
                <!-- Origin -->
                <circle cx="0" cy="0" r="2.5" fill="#22c55e"/>
                <text x="4" y="-4" font-size="8" fill="#22c55e" font-family="monospace" opacity="0.8">0,0</text>
                <!-- Axis -->
                <line x1="0" y1="0" x2="18" y2="0" stroke="#22c55e" stroke-width="0.6" opacity="0.5"/>
                <line x1="0" y1="0" x2="0" y2="18" stroke="#22c55e" stroke-width="0.6" opacity="0.5"/>

                <!-- Holes -->
                {#each extras.filter(e => e.type === 'poincon') as op}
                  <circle cx={op.x} cy={op.y} r={(op.diameter || 8) / 2}
                    fill="#0a0a0b" stroke="#fbbf24" stroke-width="1.2"/>
                  <circle cx={op.x} cy={op.y} r="1" fill="#fbbf24" opacity="0.6"/>
                {/each}
                <!-- Notches -->
                {#each extras.filter(e => e.type === 'decoupe') as op}
                  <rect x={op.x} y={op.y} width={op.w} height={op.h}
                    fill="#0a0a0b" stroke="#f87171" stroke-width="1.2" stroke-dasharray="3 2"/>
                {/each}
              </svg>
            </div>
          </div>

          <!-- Operation list -->
          {#if extras.length > 0}
            <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3">
              <p class="text-sm font-semibold text-zinc-200">Opérations ({extras.length})</p>
              {#each extras as op (op.id)}
                <div class="bg-zinc-800/40 border border-zinc-700/50 rounded-xl p-4">
                  <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center gap-2">
                      <div class="w-6 h-6 rounded-lg flex items-center justify-center {op.type === 'poincon' ? 'bg-amber-600/20' : 'bg-red-600/20'}">
                        <i class="fas {op.type === 'poincon' ? 'fa-circle text-amber-400' : 'fa-vector-square text-red-400'} text-xs"></i>
                      </div>
                      <span class="text-sm font-medium text-zinc-200">{op.type === 'poincon' ? 'Perçage' : 'Découpe'}</span>
                    </div>
                    <button onclick={() => removeExtra(op.id)}
                      class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-all">
                      <i class="fas fa-trash text-xs"></i>
                    </button>
                  </div>
                  <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                    {#each op.type === 'poincon'
                      ? [['X', 'x', 0, totalLength], ['Y', 'y', 0, design.width], ['Ø', 'diameter', 2, 50]]
                      : [['X', 'x', 0, totalLength], ['Y', 'y', 0, design.width], ['Largeur', 'w', 2, totalLength], ['Hauteur', 'h', 2, design.width]]
                    as [lbl, key, min, max]}
                      <label class="flex flex-col gap-1">
                        <span class="text-xs text-zinc-500">{lbl} <span class="text-zinc-700">mm</span></span>
                        <input type="number" {min} {max} step="1" bind:value={op[key]}
                          class="bg-zinc-900 border border-zinc-700/60 rounded-lg px-3 py-2 text-zinc-100 text-sm font-mono focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all">
                      </label>
                    {/each}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <!-- ── Step 5: Devis ──────────────────────────────────── -->
      {#if step === 5}
        <div class="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
          {#if quoteStatus === 'success'}
            <div class="p-12 text-center">
              <div class="w-16 h-16 bg-green-600/15 border border-green-600/30 rounded-full flex items-center justify-center mx-auto mb-5">
                <i class="fas fa-check text-green-400 text-xl"></i>
              </div>
              <h3 class="text-xl font-semibold text-zinc-100 mb-2">Demande envoyée</h3>
              <p class="text-zinc-400 text-sm mb-8 max-w-sm mx-auto">Notre équipe vous contactera sous 24 h avec un devis précis correspondant à votre conception.</p>
              <button
                onclick={() => { quoteStatus = null; step = 1; }}
                class="bg-red-600 hover:bg-red-500 text-white font-semibold px-8 py-3 rounded-xl transition-all duration-200 shadow-lg shadow-red-900/30"
              >
                Concevoir une autre pièce
              </button>
            </div>
          {:else}
            <div class="px-6 py-5 border-b border-zinc-800 bg-zinc-800/20">
              <h2 class="text-lg font-semibold text-zinc-100">Demande de devis</h2>
              <div class="flex items-center gap-3 mt-2">
                <span class="text-2xl font-bold text-red-400 tabular-nums">{pricing.total.toFixed(2)} €</span>
                <span class="text-zinc-600 text-sm">·</span>
                <span class="text-zinc-500 text-sm">{totalLength} × {design.width} mm</span>
                <span class="text-zinc-600 text-sm">·</span>
                <span class="text-zinc-500 text-sm">{materials[design.material].label}</span>
              </div>
            </div>

            <form onsubmit={submitQuote} class="p-6 space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label for="q-nom" class="block text-sm font-medium text-zinc-300 mb-2">Nom <span class="text-red-500">*</span></label>
                  <input id="q-nom" type="text" bind:value={quote.nom} required placeholder="Votre nom"
                    class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
                </div>
                <div>
                  <label for="q-email" class="block text-sm font-medium text-zinc-300 mb-2">Email <span class="text-red-500">*</span></label>
                  <input id="q-email" type="email" bind:value={quote.email} required placeholder="votre@email.fr"
                    class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
                </div>
              </div>
              <div>
                <label for="q-tel" class="block text-sm font-medium text-zinc-300 mb-2">Téléphone</label>
                <input id="q-tel" type="tel" bind:value={quote.telephone} placeholder="01 23 45 67 89"
                  class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm">
              </div>
              <div>
                <label for="q-notes" class="block text-sm font-medium text-zinc-300 mb-2">Notes <span class="text-zinc-600 font-normal">(quantité, délai, finition…)</span></label>
                <textarea id="q-notes" bind:value={quote.notes} rows="3"
                  class="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600/20 transition-all text-sm resize-none"
                  placeholder="Ex : 10 pièces, livraison sous 5 jours, grenaillage…"
                ></textarea>
              </div>

              {#if quoteStatus === 'error'}
                <div class="flex items-start gap-3 bg-red-950/30 border border-red-800/40 rounded-xl px-4 py-3">
                  <i class="fas fa-exclamation-circle text-red-400 mt-0.5 flex-shrink-0"></i>
                  <p class="text-red-300 text-sm">{quoteError}</p>
                </div>
              {/if}

              <button
                type="submit"
                disabled={quoteStatus === 'sending'}
                class="w-full flex items-center justify-center gap-2.5 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-all duration-200 shadow-lg shadow-red-900/30"
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

      <!-- Navigation -->
      {#if quoteStatus !== 'success'}
        <div class="flex items-center justify-between pt-1">
          <button
            onclick={() => step > 1 && step--}
            disabled={step === 1}
            class="flex items-center gap-2 px-5 py-2.5 border border-zinc-700 hover:border-zinc-500 text-zinc-400 hover:text-zinc-200 rounded-xl transition-all text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <i class="fas fa-chevron-left text-xs"></i>
            Précédent
          </button>
          {#if step < STEPS.length}
            <button
              onclick={() => step++}
              class="flex items-center gap-2 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-xl transition-all duration-200 text-sm shadow-lg shadow-red-900/30"
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
