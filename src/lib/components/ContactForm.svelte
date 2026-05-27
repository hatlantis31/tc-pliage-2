<script>
  let formData = $state({
    nom: '',
    email: '',
    telephone: '',
    entreprise: '',
    sujet: 'Demande de devis',
    message: '',
    urgence: 'normal'
  });

  let status = $state(null); // null | 'sending' | 'success' | 'error'
  let errorMsg = $state('');

  const urgencyOptions = [
    { value: 'normal', label: 'Normal (3–5 jours)' },
    { value: 'urgent', label: 'Urgent (24–48h)' },
    { value: 'emergency', label: 'Très urgent (< 24h)' }
  ];

  const subjects = [
    'Demande de devis',
    "Fabrication d'urgence",
    'Informations sur nos services',
    'Service après-vente',
    'Autre demande'
  ];

  function isValidEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!formData.nom.trim() || !isValidEmail(formData.email) || !formData.message.trim()) return;

    status = 'sending';
    errorMsg = '';

    try {
      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        status = 'success';
        formData = { nom: '', email: '', telephone: '', entreprise: '', sujet: 'Demande de devis', message: '', urgence: 'normal' };
      } else {
        throw new Error('Erreur serveur');
      }
    } catch {
      status = 'error';
      errorMsg = "Une erreur s'est produite. Veuillez réessayer ou nous appeler directement.";
    }
  }
</script>

{#if status === 'success'}
  <div class="bg-green-950/40 border border-green-700/50 rounded-xl p-8 text-center">
    <div class="w-14 h-14 bg-green-600/20 border border-green-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
      <i class="fas fa-check text-green-400 text-xl"></i>
    </div>
    <h3 class="text-zinc-100 font-semibold text-lg mb-2">Message envoyé !</h3>
    <p class="text-zinc-400 text-sm">Nous vous répondrons dans les plus brefs délais.</p>
    <button
      onclick={() => status = null}
      class="mt-4 text-red-500 hover:text-red-400 text-sm font-medium transition-colors"
    >
      Envoyer un autre message
    </button>
  </div>
{:else}
  <form onsubmit={handleSubmit} class="space-y-5">

    <!-- Name + Email -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <div>
        <label for="nom" class="block text-sm font-medium text-zinc-300 mb-1.5">
          Nom <span class="text-red-500">*</span>
        </label>
        <input
          id="nom"
          type="text"
          bind:value={formData.nom}
          placeholder="Votre nom"
          required
          class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm"
        >
      </div>
      <div>
        <label for="email" class="block text-sm font-medium text-zinc-300 mb-1.5">
          Email <span class="text-red-500">*</span>
        </label>
        <input
          id="email"
          type="email"
          bind:value={formData.email}
          placeholder="votre@email.fr"
          required
          class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm"
        >
      </div>
    </div>

    <!-- Phone + Company -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <div>
        <label for="telephone" class="block text-sm font-medium text-zinc-300 mb-1.5">Téléphone</label>
        <input
          id="telephone"
          type="tel"
          bind:value={formData.telephone}
          placeholder="01 23 45 67 89"
          class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm"
        >
      </div>
      <div>
        <label for="entreprise" class="block text-sm font-medium text-zinc-300 mb-1.5">Entreprise</label>
        <input
          id="entreprise"
          type="text"
          bind:value={formData.entreprise}
          placeholder="Votre entreprise"
          class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm"
        >
      </div>
    </div>

    <!-- Subject -->
    <div>
      <label for="sujet" class="block text-sm font-medium text-zinc-300 mb-1.5">Sujet</label>
      <select
        id="sujet"
        bind:value={formData.sujet}
        class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm"
      >
        {#each subjects as s}
          <option value={s}>{s}</option>
        {/each}
      </select>
    </div>

    <!-- Urgency -->
    <div>
      <p class="text-sm font-medium text-zinc-300 mb-2">Délai souhaité</p>
      <div class="flex flex-wrap gap-3">
        {#each urgencyOptions as opt}
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="urgence"
              value={opt.value}
              bind:group={formData.urgence}
              class="accent-red-600"
            >
            <span class="text-sm {formData.urgence === opt.value ? 'text-zinc-100' : 'text-zinc-400'}">
              {opt.label}
            </span>
          </label>
        {/each}
      </div>
    </div>

    <!-- Message -->
    <div>
      <label for="message" class="block text-sm font-medium text-zinc-300 mb-1.5">
        Message <span class="text-red-500">*</span>
      </label>
      <textarea
        id="message"
        bind:value={formData.message}
        placeholder="Décrivez votre besoin..."
        required
        rows="5"
        class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600 transition-colors text-sm resize-none"
      ></textarea>
    </div>

    <!-- Error -->
    {#if status === 'error'}
      <p class="text-red-400 text-sm bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
        <i class="fas fa-exclamation-circle mr-2"></i>{errorMsg}
      </p>
    {/if}

    <!-- Submit -->
    <button
      type="submit"
      disabled={status === 'sending'}
      class="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded transition-colors"
    >
      {#if status === 'sending'}
        <i class="fas fa-spinner fa-spin"></i>
        Envoi en cours…
      {:else}
        <i class="fas fa-paper-plane"></i>
        Envoyer le message
      {/if}
    </button>
  </form>
{/if}
