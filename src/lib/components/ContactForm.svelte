<script>
  import { onMount } from 'svelte';

  let formData = {
    nom: '',
    email: '',
    telephone: '',
    entreprise: '',
    sujet: '',
    message: '',
    urgence: 'normal',
    fichier: null
  };
  
  let submitStatus = null; // null, 'sending', 'success', 'error'
  let errorMessage = '';
  let formValid = false;
  let formFields = {};
  let fileLabel = 'Choisir un fichier';
  
  // Form field validation
  let validation = {
    nom: { valid: false, message: 'Veuillez entrer votre nom' },
    email: { valid: false, message: 'Veuillez entrer un email valide' },
    telephone: { valid: false, message: 'Veuillez entrer un numéro de téléphone valide' },
    message: { valid: false, message: 'Veuillez entrer un message' }
  };
  
  // Urgency levels
  const urgencyLevels = [
    { value: 'normal', label: 'Normal (3-5 jours)', icon: 'clock', color: 'is-info' },
    { value: 'urgent', label: 'Urgent (24-48h)', icon: 'exclamation', color: 'is-warning' },
    { value: 'emergency', label: 'Très urgent (24h)', icon: 'exclamation-triangle', color: 'is-danger' }
  ];
  
  // Contact subjects
  const subjects = [
    'Demande de devis',
    'Fabrication d\'urgence',
    'Informations sur nos services',
    'Service après-vente',
    'Autre demande'
  ];
  
  onMount(() => {
    // Initialize form fields references
    Object.keys(validation).forEach(key => {
      formFields[key] = document.getElementById(key);
    });
    
    // Check if there's a service parameter in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const serviceParam = urlParams.get('service');
    
    if (serviceParam) {
      formData.sujet = `Demande de devis - ${serviceParam}`;
    }
  });
  
  // Validate email format
  function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  // Validate phone format (10 digits, can have spaces, dots or dashes)
  function isValidPhone(phone) {
    const re = /^(?:(?:\+|00)33[\s.-]{0,3}(?:\(0\)[\s.-]{0,3})?|0)[1-9](?:(?:[\s.-]?\d{2}){4})$/;
    return re.test(phone);
  }

  // Validate individual field
  function validateField(field) {
    if (field === 'email') {
      validation.email.valid = isValidEmail(formData.email);
    } else if (field === 'telephone') {
      validation.telephone.valid = isValidPhone(formData.telephone);
    } else if (field === 'nom') {
      validation.nom.valid = formData.nom.trim().length >= 2;
    } else if (field === 'message') {
      validation.message.valid = formData.message.trim().length >= 10;
    }

    updateFormValidity();
    return validation[field].valid;
  }

  // Update overall form validity
  function updateFormValidity() {
    formValid = Object.values(validation).every(field => field.valid);
  }

  // Handle input change
  function handleInput(field) {
    validateField(field);
  }

  // Handle input blur
  function handleBlur(field) {
    if (formFields[field] && !validation[field].valid) {
      formFields[field].classList.add('is-danger');
    }
  }

  // Handle input focus
  function handleFocus(field) {
    if (formFields[field]) {
      formFields[field].classList.remove('is-danger');
    }
  }

  // Handle file selection
  function handleFileChange(event) {
    const file = event.target.files[0];
    if (file) {
      formData.fichier = file;
      fileLabel = file.name;
    } else {
      fileLabel = 'Choisir un fichier';
    }
  }

  // Handle form submission
  async function handleSubmit() {
    // Validate all fields
    Object.keys(validation).forEach(validateField);

    if (!formValid) {
      Object.keys(validation).forEach(field => {
        if (!validation[field].valid && formFields[field]) {
          formFields[field].classList.add('is-danger');
        }
      });
      return;
    }

    submitStatus = 'sending';

    try {
      const response = await fetch('/api/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          to: 'briand.malo@gmail.com',
          replyTo: formData.email,
          subject: `Contact TCPliage: ${formData.sujet || 'Nouveau message'}`,
          message: `
            <h2>Nouveau message de contact</h2>
            <p><strong>Nom:</strong> ${formData.nom}</p>
            <p><strong>Email:</strong> ${formData.email}</p>
            <p><strong>Téléphone:</strong> ${formData.telephone}</p>
            ${formData.entreprise ? `<p><strong>Entreprise:</strong> ${formData.entreprise}</p>` : ''}
            <p><strong>Sujet:</strong> ${formData.sujet}</p>
            <p><strong>Urgence:</strong> ${urgencyLevels.find(u => u.value === formData.urgence)?.label || 'Normal'}</p>
            <hr>
            <p><strong>Message:</strong></p>
            <p>${formData.message.replace(/\n/g, '<br>')}</p>
          `,
          submittedAt: new Date().toISOString()
        })
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Erreur lors de l\'envoi');
      }

      console.log('Email sent successfully:', result);
      submitStatus = 'success';

      // Reset form after success
      setTimeout(() => {
        formData = {
          nom: '',
          email: '',
          telephone: '',
          entreprise: '',
          sujet: '',
          message: '',
          urgence: 'normal',
          fichier: null
        };

        Object.keys(validation).forEach(key => {
          validation[key].valid = false;
          if (formFields[key]) {
            formFields[key].classList.remove('is-danger');
          }
        });

        fileLabel = 'Choisir un fichier';
        formValid = false;
        submitStatus = null;
      }, 3000);

    } catch (error) {
      console.error('Error submitting form:', error);
      submitStatus = 'error';
      errorMessage = error.message || "Une erreur s'est produite. Veuillez réessayer.";
    }
  }
</script>

<div class="contact-form-container">
  {#if submitStatus === 'success'}
    <div class="form-success">
      <div class="success-icon">
        <i class="fas fa-check-circle"></i>
      </div>
      <h3>Message Envoyé!</h3>
      <p>Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais.</p>
    </div>
  {:else}
    <form class="contact-form" on:submit|preventDefault={handleSubmit}>
      <!-- Form Status Messages -->
      {#if submitStatus === 'error'}
        <div class="notification is-danger">
          <button class="delete" on:click={() => submitStatus = null}></button>
          <p>
            <span class="icon"><i class="fas fa-exclamation-triangle"></i></span>
            <span>{errorMessage}</span>
          </p>
        </div>
      {/if}
      
      <div class="columns is-multiline">
        <!-- Left Column -->
        <div class="column is-6">
          <!-- Name Field -->
          <div class="field">
            <label class="label" for="nom">Nom <span class="required">*</span></label>
            <div class="control has-icons-left">
              <input 
                id="nom"
                class="input" 
                type="text" 
                placeholder="Votre nom et prénom"
                bind:value={formData.nom}
                on:input={() => handleInput('nom')}
                on:focus={() => handleFocus('nom')}
                on:blur={() => handleBlur('nom')}
                required
              >
              <span class="icon is-small is-left">
                <i class="fas fa-user"></i>
              </span>
            </div>
            {#if !validation.nom.valid && formData.nom !== ''}
              <p class="help is-danger">{validation.nom.message}</p>
            {/if}
          </div>
          
          <!-- Email Field -->
          <div class="field">
            <label class="label" for="email">Email <span class="required">*</span></label>
            <div class="control has-icons-left">
              <input 
                id="email"
                class="input" 
                type="email" 
                placeholder="Votre adresse email"
                bind:value={formData.email}
                on:input={() => handleInput('email')}
                on:focus={() => handleFocus('email')}
                on:blur={() => handleBlur('email')}
                required
              >
              <span class="icon is-small is-left">
                <i class="fas fa-envelope"></i>
              </span>
            </div>
            {#if !validation.email.valid && formData.email !== ''}
              <p class="help is-danger">{validation.email.message}</p>
            {/if}
          </div>
          
          <!-- Phone Field -->
          <div class="field">
            <label class="label" for="telephone">Téléphone <span class="required">*</span></label>
            <div class="control has-icons-left">
              <input 
                id="telephone"
                class="input" 
                type="tel" 
                placeholder="Votre numéro de téléphone"
                bind:value={formData.telephone}
                on:input={() => handleInput('telephone')}
                on:focus={() => handleFocus('telephone')}
                on:blur={() => handleBlur('telephone')}
                required
              >
              <span class="icon is-small is-left">
                <i class="fas fa-phone"></i>
              </span>
            </div>
            {#if !validation.telephone.valid && formData.telephone !== ''}
              <p class="help is-danger">{validation.telephone.message}</p>
            {/if}
          </div>
          
          <!-- Company Field -->
          <div class="field">
            <label class="label" for="entreprise">Entreprise</label>
            <div class="control has-icons-left">
              <input 
                id="entreprise"
                class="input" 
                type="text" 
                placeholder="Nom de votre entreprise (optionnel)"
                bind:value={formData.entreprise}
              >
              <span class="icon is-small is-left">
                <i class="fas fa-building"></i>
              </span>
            </div>
          </div>
        </div>
        
        <!-- Right Column -->
        <div class="column is-6">
          <!-- Subject Field -->
          <div class="field">
            <label class="label" for="sujet">Sujet</label>
            <div class="control has-icons-left">
              <div class="select is-fullwidth">
                <select id="sujet" bind:value={formData.sujet}>
                  <option value="" disabled selected>Sélectionnez un sujet</option>
                  {#each subjects as subject}
                    <option value={subject}>{subject}</option>
                  {/each}
                </select>
              </div>
              <span class="icon is-small is-left">
                <i class="fas fa-tag"></i>
              </span>
            </div>
          </div>
          
          <!-- Urgency Level Field -->
          <div class="field">
            <label class="label">Niveau d'Urgence</label>
            <div class="control">
              <div class="urgency-selector">
                {#each urgencyLevels as level}
                  <label class="urgency-option">
                    <input 
                      type="radio" 
                      name="urgence"
                      bind:group={formData.urgence} 
                      value={level.value}
                    >
                    <div class={`urgency-label ${level.color}`}>
                      <span class="icon">
                        <i class={`fas fa-${level.icon}`}></i>
                      </span>
                      <span>{level.label}</span>
                    </div>
                  </label>
                {/each}
              </div>
            </div>
          </div>
          
          <!-- File Upload Field -->
          <div class="field">
            <label class="label">Joindre un fichier</label>
            <div class="file has-name is-fullwidth">
              <label class="file-label">
                <input 
                  class="file-input" 
                  type="file" 
                  name="fichier"
                  on:change={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png,.dwg,.dxf"
                >
                <span class="file-cta">
                  <span class="file-icon">
                    <i class="fas fa-upload"></i>
                  </span>
                  <span class="file-label">Choisir</span>
                </span>
                <span class="file-name">
                  {fileLabel}
                </span>
              </label>
            </div>
            <p class="help">Maximum 10 Mo (PDF, JPG, PNG, DWG, DXF)</p>
          </div>
        </div>
        
        <!-- Message Field (Full Width) -->
        <div class="column is-12">
          <div class="field">
            <label class="label" for="message">Message <span class="required">*</span></label>
            <div class="control">
              <textarea 
                id="message"
                class="textarea" 
                placeholder="Détaillez votre demande..."
                rows="5"
                bind:value={formData.message}
                on:input={() => handleInput('message')}
                on:focus={() => handleFocus('message')}
                on:blur={() => handleBlur('message')}
                required
              ></textarea>
            </div>
            {#if !validation.message.valid && formData.message !== ''}
              <p class="help is-danger">{validation.message.message}</p>
            {/if}
          </div>
        </div>
      </div>
      
      <div class="field">
        <div class="control">
          <label class="checkbox">
            <input type="checkbox" required>
            J'accepte que mes données soient traitées pour traiter ma demande conformément à la <a href="#">politique de confidentialité</a>.
          </label>
        </div>
      </div>
      
      <div class="field is-grouped is-grouped-right">
        <div class="control">
          <button 
            type="submit" 
            class="button is-primary is-medium submit-button"
            class:is-loading={submitStatus === 'sending'}
            disabled={submitStatus === 'sending'}
          >
            <span class="icon">
              <i class="fas fa-paper-plane"></i>
            </span>
            <span>Envoyer</span>
          </button>
        </div>
      </div>
    </form>
  {/if}
</div>


<style>
  .contact-form-container {
    max-width: 100%;
    margin: 0 auto;
  }
  
  .contact-form {
    background: linear-gradient(to bottom, var(--bg-white), rgba(248, 249, 250, 0.5));
    border-radius: var(--radius-lg);
    padding: 0;
    position: relative;
  }
  
  /* Form Fields Styling */
  .field {
    margin-bottom: 1.5rem !important;
  }
  
  .label {
    color: var(--dark) !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
    font-size: 1rem !important;
  }
  
  .required {
    color: var(--primary);
    margin-left: 0.25rem;
  }
  
  .input, .textarea, .select select {
    border: 2px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.4rem 2rem !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    background-color: white !important;
  }
  
  .input:focus, .textarea:focus, .select select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(229, 57, 53, 0.1) !important;
  }
  
  .input.is-danger, .textarea.is-danger, .select select.is-danger {
    border-color: #ff3860 !important;
    background-color: rgba(255, 56, 96, 0.05) !important;
  }
  
  .help.is-danger {
    color: #ff3860 !important;
    font-size: 0.875rem !important;
    margin-top: 0.25rem !important;
  }
  
  /* Icon styling */
  .icon.is-left {
    color: var(--text-light) !important;
    pointer-events: none;
  }
  
  .has-icons-left .input:focus ~ .icon.is-left {
    color: var(--primary) !important;
  }
  
  /* Select dropdown */
  .select {
    width: 100%;
  }
  
  .select select {
    width: 100% !important;
    cursor: pointer;
  }
  
  .select:not(.is-multiple):not(.is-loading)::after {
    border-color: var(--primary) !important;
    right: 1rem !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
  }
  
  /* Urgency Selector */
  .urgency-selector {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .urgency-option {
    cursor: pointer;
    display: block;
  }
  
  .urgency-option input[type="radio"] {
    position: absolute !important;
    opacity: 0 !important;
    width: 0 !important;
    height: 0 !important;
  }
  
  .urgency-label {
    display: flex !important;
    align-items: center;
    padding: 0.75rem 1rem !important;
    border: 2px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;
    cursor: pointer;
    background-color: white;
  }
  
  .urgency-label:hover {
    border-color: rgba(229, 57, 53, 0.3) !important;
    background-color: rgba(229, 57, 53, 0.02) !important;
  }
  
  .urgency-option input[type="radio"]:checked + .urgency-label {
    border-color: var(--primary) !important;
    background-color: rgba(229, 57, 53, 0.1) !important;
    color: var(--primary) !important;
  }
  
  .urgency-label.is-info {
    border-color: var(--info) !important;
  }
  
  .urgency-option input[type="radio"]:checked + .urgency-label.is-info {
    border-color: var(--info) !important;
    background-color: rgba(33, 150, 243, 0.1) !important;
    color: var(--info) !important;
  }
  
  .urgency-label.is-warning {
    border-color: var(--warning) !important;
  }
  
  .urgency-option input[type="radio"]:checked + .urgency-label.is-warning {
    border-color: var(--warning) !important;
    background-color: rgba(255, 152, 0, 0.1) !important;
    color: var(--warning) !important;
  }
  
  .urgency-label.is-danger {
    border-color: #ff3860 !important;
  }
  
  .urgency-option input[type="radio"]:checked + .urgency-label.is-danger {
    border-color: #ff3860 !important;
    background-color: rgba(255, 56, 96, 0.1) !important;
    color: #ff3860 !important;
  }
  
  .urgency-label .icon {
    margin-right: 0.75rem !important;
  }
  
  /* File Upload */
  .file.has-name {
    border-radius: var(--radius-md) !important;
    overflow: hidden;
  }
  
  .file-cta {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    border-radius: var(--radius-md) 0 0 var(--radius-md) !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.3s ease !important;
  }
  
  .file-cta:hover {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
  }
  
  .file-name {
    border: 2px solid var(--border) !important;
    border-left: none !important;
    border-radius: 0 var(--radius-md) var(--radius-md) 0 !important;
    padding: 0.75rem 1rem !important;
    background-color: white !important;
    color: var(--text) !important;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .help {
    font-size: 0.875rem !important;
    color: var(--text-light) !important;
    margin-top: 0.25rem !important;
  }
  
  /* Checkbox */
  .checkbox {
    color: var(--text) !important;
    cursor: pointer;
  }
  
  .checkbox input[type="checkbox"] {
    margin-right: 0.5rem !important;
    transform: scale(1.1);
  }
  
  .checkbox a {
    color: var(--primary) !important;
    text-decoration: underline;
  }
  
  .checkbox a:hover {
    color: var(--primary-dark) !important;
  }
  
  /* Submit Button */
  .submit-button {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;
    min-width: 150px;
  }
  
  .submit-button:hover:not(:disabled) {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md) !important;
  }
  
  .submit-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .submit-button.is-loading {
    color: transparent !important;
  }
  
  .submit-button.is-loading::after {
    border-color: transparent transparent white white !important;
  }
  
  /* Success State */
  .form-success {
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(to bottom, var(--bg-white), rgba(76, 175, 80, 0.05));
    border-radius: var(--radius-lg);
    border: 2px solid rgba(76, 175, 80, 0.2);
  }
  
  .success-icon {
    font-size: 4rem;
    color: var(--success);
    margin-bottom: 1.5rem;
    animation: successPulse 2s infinite;
  }
  
  .form-success h3 {
    color: var(--success) !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
  }
  
  .form-success p {
    color: var(--text) !important;
    font-size: 1.1rem;
    line-height: 1.6;
  }
  
  @keyframes successPulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }
  
  /* Notification Messages */
  .notification {
    border-radius: var(--radius-md) !important;
    margin-bottom: 1.5rem !important;
  }
  
  .notification.is-danger {
    background-color: rgba(255, 56, 96, 0.1) !important;
    border: 1px solid rgba(255, 56, 96, 0.3) !important;
    color: #ff3860 !important;
  }
  
  .notification .delete {
    background-color: transparent !important;
    border: none !important;
    color: inherit !important;
  }
  
  /* Responsive Design */
  @media screen and (max-width: 768px) {
    .urgency-selector {
      gap: 0.5rem;
    }
    
    .urgency-label {
      padding: 0.5rem 0.75rem !important;
      font-size: 0.9rem;
    }
    
    .file-name {
      max-width: 150px;
    }
    
    .submit-button {
      width: 100%;
      margin-top: 1rem;
    }
    
    .form-success {
      padding: 2rem 1rem;
    }
    
    .success-icon {
      font-size: 3rem;
    }
  }
  
  /* Form Animation */
  .contact-form {
    animation: formFadeIn 0.5s ease-out;
  }
  
  @keyframes formFadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  /* Focus improvements for accessibility */
  .input:focus, .textarea:focus, .select select:focus, .urgency-label:focus-within {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
  }
  
  /* Loading state improvements */
  .field.is-loading {
    position: relative;
  }
  
  .field.is-loading::after {
    content: '';
    position: absolute;
    top: 50%;
    right: 1rem;
    width: 1rem;
    height: 1rem;
    border: 2px solid var(--border);
    border-top: 2px solid var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>