<!-- src/routes/designer/steps/ReviewStep.svelte -->
<script>
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';

  export let design;

  const dispatch = createEventDispatcher();

  // ──────────────────────────────────────
  // 1. CONSTANTS (your pro address)
  // ──────────────────────────────────────
  const RECIPIENT = 'briand.malo@gmail.com';   // <-- ALWAYS this address
  const REPLY_TO  = '';                        // will be filled with user email

  // ──────────────────────────────────────
  // 2. UI state
  // ──────────────────────────────────────
  let userEmail = '';
  let userMessage = '';
  let sending = false;
  let sent = false;
  let error = '';
  let screenshot = '';

  // ──────────────────────────────────────
  // 3. SVG → PNG (runs once the component is in the DOM)
  // ──────────────────────────────────────
  onMount(async () => {
    await new Promise(r => setTimeout(r, 120));               // tiny paint-delay
    const svg = document.querySelector('#preview-svg');
    if (!svg) return;

    const data = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([data], { type: 'image/svg+xml' });
    const url  = URL.createObjectURL(blob);

    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width  = 600;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#f8f8f8';
      ctx.fillRect(0, 0, 600, 400);
      ctx.drawImage(img, 50, 50, 500, 300);
      screenshot = canvas.toDataURL('image/png');
      URL.revokeObjectURL(url);
    };
    img.src = url;
  });

  // ──────────────────────────────────────
  // 4. SEND EMAIL
  // ──────────────────────────────────────
  async function sendEmail() {
    if (!userEmail || sending) return;

    sending = true; error = ''; sent = false;

    try {
      const payload = {
        to: RECIPIENT,                     // <-- YOUR PRO ADDRESS
        replyTo: userEmail,                // <-- user can be answered directly
        subject: `Nouvelle conception – Ref: ${Date.now().toString(36).toUpperCase()}`,
        referenceNumber: Date.now().toString(36).toUpperCase(),
        submittedAt: new Date().toISOString(),
        designData: JSON.stringify(design, null, 2),
        screenshot,
        message: userMessage || 'Aucune note supplémentaire.'
      };

      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Échec d’envoi');
      sent = true;
    } catch (e) {
      error = e.message || 'Erreur réseau';
    } finally {
      sending = false;
    }
  }

  // ──────────────────────────────────────
  // 5. Helpers (same as before – only UI)
  // ──────────────────────────────────────
  const materials = { steel:{name:'Acier'}, aluminum:{name:'Aluminium'}, copper:{name:'Cuivre'}, brass:{name:'Laiton'} };
  const finishes  = { none:'Aucune', painted:'Peint', 'powder-coated':'Poudre', galvanized:'Galvanisé', anodized:'Anodisé', brushed:'Brossé', polished:'Poli' };
  const partTypes = { rectangle:'Rectangle', lShape:'L-Shape', uShape:'U-Shape', circle:'Cercle' };

  function formatDims() {
    const d = design.dimensions || {};
    const t = design.thickness || 0;
    switch (design.partType) {
      case 'rectangle': return `${d.width} × ${d.height} × ${t} mm`;
      case 'lShape':    return `${d.width} × ${d.height} × ${t} mm, Jambe: ${d.legWidth} mm`;
      case 'uShape':    return `${d.width} × ${d.height} × ${t} mm, Jambe: ${d.legWidth} mm, Bride: ${d.flangeHeight} mm`;
      case 'circle':    return `Ø${d.diameter} × ${t} mm`;
      default:          return 'N/A';
    }
  }

  function partPath() {
    const d = design.dimensions || {};
    const p = 20;
    switch (design.partType) {
      case 'rectangle': return `M ${p} ${p} h ${d.width||200} v ${d.height||100} h -${d.width||200} z`;
      case 'circle':
        const r = (d.diameter||100)/2;
        return `M ${p+r} ${p} a ${r} ${r} 0 1 0 0 ${r*2} a ${r} ${r} 0 1 0 0 -${r*2}`;
      case 'lShape':
        return `M ${p} ${p} h ${d.width||200} v ${d.legWidth||50} h -${(d.width||200)-(d.legWidth||50)} v ${(d.height||100)-(d.legWidth||50)} h -${d.legWidth||50} z`;
      case 'uShape':
        const w = d.width||200, h = d.height||100, lw = d.legWidth||50, fh = d.flangeHeight||30;
        return `M ${p} ${p} h ${lw} v ${h-fh} h ${w-2*lw} v -${h-fh} h ${lw} v ${h} h -${w} z`;
      default: return `M ${p} ${p} h 200 v 100 h -200 z`;
    }
  }
</script>

<div class="columns is-multiline">

  <!-- ==== LEFT : EMAIL CARD ==== -->
  <div class="column is-12-mobile is-5-tablet is-4-desktop">
    <div class="card email-card">
      <header class="card-header">
        <p class="card-header-title">Envoyer à briand.malo@gmail.com</p>
      </header>
      <div class="card-content">

        <div class="field">
          <label class="label">Votre e-mail (pour la réponse)</label>
          <div class="control has-icons-left">
            <input class="input" type="email" bind:value={userEmail} placeholder="vous@exemple.com" required />
            <span class="icon is-small is-left"><i class="fas fa-envelope"></i></span>
          </div>
        </div>

        <div class="field">
          <label class="label">Message (facultatif)</label>
          <div class="control">
            <textarea class="textarea" bind:value={userMessage} rows="3"
                      placeholder="Ex : urgence, tolérance spéciale…"></textarea>
          </div>
        </div>

        <div class="field">
          <div class="control">
            <button class="button is-primary is-fullwidth"
                    on:click={sendEmail}
                    disabled={!userEmail || sending || sent}>
              {#if sending}
                <span class="icon"><i class="fas fa-spinner fa-spin"></i></span>
                <span>Envoi…</span>
              {:else if sent}
                <span class="icon"><i class="fas fa-check"></i></span>
                <span>Envoyé !</span>
              {:else}
                <span class="icon"><i class="fas fa-paper-plane"></i></span>
                <span>Envoyer</span>
              {/if}
            </button>
          </div>
        </div>

        {#if error}<p class="help is-danger">{error}</p>{/if}
        {#if sent}<p class="help is-success mt-3"><i class="fas fa-check-circle"></i> Demande envoyée.</p>{/if}
      </div>
    </div>
  </div>

  <!-- ==== RIGHT : ONE CARD (preview + characteristics) ==== -->
  <div class="column is-12-mobile is-7-tablet is-8-desktop">
    <div class="card summary-card">
      <header class="card-header">
        <p class="card-header-title">Résumé de la pièce</p>
      </header>
      <div class="card-content">

        <div class="columns is-mobile">
          <div class="column is-5">
            <figure class="image is-square">
              <svg id="preview-svg" viewBox="0 0 280 200"
                   style="background:#f8f8f8; width:100%; height:auto;">
                <path d={partPath()} fill="#ccc" stroke="#333" stroke-width="2"/>
                {#each design.holes || [] as h}
                  <circle cx={h.x+20} cy={h.y+20} r={h.diameter/2}
                          fill="white" stroke="#333" stroke-width="1.5"/>
                {/each}
                <text x="20" y="15" font-size="10" fill="#666">TC Pliage</text>
              </svg>
            </figure>
          </div>

          <div class="column is-7">
            <table class="table is-fullwidth is-striped is-narrow">
              <tbody>
                <tr><th>Type</th><td>{partTypes[design.partType] || '–'}</td></tr>
                <tr><th>Dimensions</th><td>{formatDims()}</td></tr>
                <tr><th>Matériau</th><td>{materials[design.material]?.name || '–'}</td></tr>
                <tr><th>Finition</th><td>{finishes[design.finish] || 'Aucune'}</td></tr>
                <tr><th>Épaisseur</th><td>{design.thickness} mm</td></tr>
                <tr><th>Trous</th><td>{(design.holes||[]).length}</td></tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </div>

</div>

<style>
  .card { border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,.05); }
  .email-card .card-content { padding:1.5rem; }
  .summary-card .card-content { padding:1.5rem; }
  .image.is-square { padding-top:100%; position:relative; }
  .image.is-square > svg { position:absolute; top:0; left:0; width:100%; height:100%; }
  @media (max-width:768px){
    .columns { flex-direction:column; }
    .column.is-5, .column.is-7 { width:100%; }
  }
</style>