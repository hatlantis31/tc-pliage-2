<script>
  import ContactForm from '$lib/components/ContactForm.svelte';
  import { onMount } from 'svelte';
  
  let mapLoaded = false;
  let activeTab = 'form';
  
  // Office hours
  const officeHours = [
    { day: 'Lundi', hours: '5h - 19h' },
    { day: 'Mardi', hours: '5h - 19h' },
    { day: 'Mercredi', hours: '5h - 19h' },
    { day: 'Jeudi', hours: '5h - 19h' },
    { day: 'Vendredi', hours: '5h - 19h' },
    { day: 'Samedi', hours: 'Sur rendez-vous' },
    { day: 'Dimanche', hours: 'Fermé (urgences uniquement)' }
  ];
  
  onMount(() => {
    // If you have a Google Maps API key, you can initialize the map here
    setTimeout(() => {
      mapLoaded = true;
    }, 1000);
  });
  
  function setActiveTab(tab) {
    activeTab = tab;
  }
</script>

<section class="section contact-hero">
  <div class="container">
    <div class="content has-text-centered">
      <h1 class="title is-1 has-text-white">Contactez-nous</h1>
      <p class="subtitle is-4 has-text-white">Notre équipe est à votre écoute pour répondre à vos besoins</p>
    </div>
  </div>
</section>

<section class="section contact-options">
  <div class="container">
    <div class="columns is-multiline">
      <!-- Card 1: Emergency Contact -->
      <div class="column is-4-desktop is-6-tablet">
        <div class="contact-card emergency">
          <div class="card-icon">
            <span class="icon is-large">
              <i class="fas fa-phone-alt fa-2x"></i>
            </span>
          </div>
          <h3 class="title is-4">Service d'Urgence</h3>
          <p>Disponible 24h/24 et 7j/7 pour tous vos besoins urgents de fabrication métallique.</p>
          <a href="tel:emergency-number" class="button is-danger is-fullwidth">
            <span class="icon">
              <i class="fas fa-phone"></i>
            </span>
            <span>01 23 45 67 90</span>
          </a>
        </div>
      </div>
      
      <!-- Card 2: Email Contact -->
      <div class="column is-4-desktop is-6-tablet">
        <div class="contact-card email">
          <div class="card-icon">
            <span class="icon is-large">
              <i class="fas fa-envelope fa-2x"></i>
            </span>
          </div>
          <h3 class="title is-4">Email & Devis</h3>
          <p>Pour les demandes de devis et renseignements généraux sur nos services.</p>
          <a href="mailto:contact@tcpliage.fr" class="button is-primary is-fullwidth">
            <span class="icon">
              <i class="fas fa-envelope"></i>
            </span>
            <span>contact@tcpliage.fr</span>
          </a>
        </div>
      </div>
      
      <!-- Card 3: Visit Us -->
      <div class="column is-4-desktop is-6-tablet">
        <div class="contact-card visit">
          <div class="card-icon">
            <span class="icon is-large">
              <i class="fas fa-map-marker-alt fa-2x"></i>
            </span>
          </div>
          <h3 class="title is-4">Visitez Notre Atelier</h3>
          <p>Venez nous rencontrer directement à notre atelier de fabrication à Portet-Sur-Garonne.</p>
          <a 
            href="https://maps.google.com?q=3+Avenue+du+Bois+Vert,+Portet-Sur-Garonne" 
            target="_blank" 
            class="button is-info is-fullwidth"
          >
            <span class="icon">
              <i class="fas c"></i>
            </span>
            <span>Itinéraire</span>
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section contact-main">
  <div class="container">
    <div class="tabs is-centered is-boxed is-medium">
      <ul>
        <li class={activeTab === 'form' ? 'is-active' : ''}>
          <a on:click|preventDefault={() => setActiveTab('form')}>
            <span class="icon"><i class="fas fa-paper-plane"></i></span>
            <span>Formulaire de Contact</span>
          </a>
        </li>
        <li class={activeTab === 'info' ? 'is-active' : ''}>
          <a on:click|preventDefault={() => setActiveTab('info')}>
            <span class="icon"><i class="fas fa-info-circle"></i></span>
            <span>Informations</span>
          </a>
        </li>
      </ul>
    </div>
    
    <div class="tab-content">
      {#if activeTab === 'form'}
        <div class="columns">
          <div class="column is-8 is-offset-2">
            <div class="box contact-form-container">
              <h2 class="title is-3 has-text-centered mb-5">Envoyez-nous un Message</h2>
              <ContactForm />
            </div>
          </div>
        </div>
      {:else}
        <div class="columns">
          <div class="column is-6">
            <div class="box info-box">
              <h3 class="title is-4">Coordonnées</h3>
              <div class="contact-details">
                <div class="contact-detail">
                  <span class="icon has-text-danger">
                    <i class="fas fa-map-marker-alt"></i>
                  </span>
                  <div>
                    <strong >Adresse:</strong><br>
                    3 Avenue du Bois Vert<br>
                    Portet-Sur-Garonne, France
                  </div>
                </div>
                
                <div class="contact-detail">
                  <span class="icon has-text-danger">
                    <i class="fas fa-phone"></i>
                  </span>
                  <div>
                    <strong>Téléphone:</strong><br>
                    Standard: <a href="tel:standard-number">01 23 45 67 89</a><br>
                    Urgence: <a href="tel:emergency-number">01 23 45 67 90</a>
                  </div>
                </div>
                
                <div class="contact-detail">
                  <span class="icon has-text-danger">
                    <i class="fas fa-envelope"></i>
                  </span>
                  <div>
                    <strong>Email:</strong><br>
                    <a href="mailto:contact@tcpliage.fr">contact@tcpliage.fr</a>
                  </div>
                </div>
              </div>
              
              <h3 class="title is-4 mt-5">Horaires d'Ouverture</h3>
              <table class="table is-fullwidth opening-hours">
                <tbody>
                  {#each officeHours as { day, hours }}
                    <tr>
                      <td>{day}</td>
                      <td class="has-text-right">{hours}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
              
              <div class="notification is-warning is-light mt-4">
                <p class="has-text-weight-medium">
                  <span class="icon has-text-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                  </span>
                  Notre service d'urgence est disponible 24h/24 et 7j/7 en dehors des heures d'ouverture.
                </p>
              </div>
            </div>
          </div>
          <div class="column is-6">
            <div class="box map-container">
              <h3 class="title is-4">Notre Localisation</h3>
              <div class="map-wrapper">
                {#if mapLoaded}
                  <iframe
                    width="100%"
                    height="400"
                    style="border:0"
                    loading="lazy"
                    allowfullscreen
                    referrerpolicy="no-referrer-when-downgrade"
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2889.9371526429886!2d1.4033!3d43.5356!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x12aebb7baf3310a3%3A0x1d4f860e16ef5296!2s3%20Av.%20du%20Bois%20Vert%2C%2031120%20Portet-sur-Garonne!5e0!3m2!1sfr!2sfr!4v1650000000000!5m2!1sfr!2sfr"
                  >
                  </iframe>
                {:else}
                  <div class="map-loading">
                    <span class="icon is-large">
                      <i class="fas fa-spinner fa-pulse fa-2x"></i>
                    </span>
                    <p>Chargement de la carte...</p>
                  </div>
                {/if}
              </div>
              
              <div class="buttons is-centered mt-4">
                <a 
                  href="https://maps.google.com?q=3+Avenue+du+Bois+Vert,+Portet-Sur-Garonne" 
                  target="_blank" 
                  class="button is-info"
                >
                  <span class="icon">
                    <i class="fas fa-directions"></i>
                  </span>
                  <span>Itinéraire</span>
                </a>
                <a href="tel:standard-number" class="button is-primary">
                  <span class="icon">
                    <i class="fas fa-phone"></i>
                  </span>
                  <span>Appeler</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</section>

<section class="section faq-section">
  <div class="container">
    <h2 class="title is-2 has-text-centered">Questions Fréquentes</h2>
    <div class="columns is-multiline">
      <div class="column is-6">
        <div class="faq-item">
          <h3 class="title is-5">Quel est votre délai de fabrication en urgence ?</h3>
          <p>Pour les commandes urgentes, nous garantissons une fabrication en 24h. Notre équipe est mobilisée pour traiter les demandes d'urgence en priorité.</p>
        </div>
      </div>
      <div class="column is-6">
        <div class="faq-item">
          <h3 class="title is-5">Quels types de métaux travaillez-vous ?</h3>
          <p>Nous travaillons principalement l'acier, l'aluminium, l'inox et le cuivre. Nos machines sont adaptées pour tous types d'épaisseurs selon vos besoins.</p>
        </div>
      </div>
      <div class="column is-6">
        <div class="faq-item">
          <h3 class="title is-5">Comment obtenir un devis ?</h3>
          <p>Vous pouvez obtenir un devis en nous contactant par téléphone, email ou en utilisant notre formulaire de contact en ligne. Pour les pièces complexes, notre outil de dessin en ligne est disponible.</p>
        </div>
      </div>
      <div class="column is-6">
        <div class="faq-item">
          <h3 class="title is-5">Livrez-vous dans toute la France ?</h3>
          <p>Oui, nous livrons dans toute la France. Pour les commandes urgentes, nous proposons un service de livraison express pour garantir la réception de vos pièces dans les plus brefs délais.</p>
        </div>
      </div>
    </div>
    
    <div class="has-text-centered mt-6">
      <p class="subtitle is-5">Vous avez d'autres questions ?</p>
      <a href="tel:standard-number" class="button is-medium is-danger">
        <span class="icon">
          <i class="fas fa-phone"></i>
        </span>
        <span>Contactez-nous directement</span>
      </a>
    </div>
  </div>
</section>


<style>
  /* Hero Section */
  .contact-hero {
    background-image:  url('/home-hero.jpg');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    padding: 6rem 1.5rem !important;
    margin-bottom: 0;
    position: relative;
    overflow: hidden;
  }
  .button.is-info {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
  }
  .contact-hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(167, 93, 91, 0.8), rgba(46, 64, 87, 0.8));
    z-index: 1;
  }
  
  .contact-hero .container {
    position: relative;
    z-index: 2;
  }
  
  .contact-hero .title {
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem !important;
    color: white !important;
  }
  
  .contact-hero .subtitle {
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    font-weight: 300 !important;
    opacity: 0.95;
    color: white !important;
  }
  
  /* Contact Options Cards */
  .contact-options {
    padding: 4rem 1.5rem 2rem !important;
    background: linear-gradient(to bottom, var(--bg-white), var(--bg-light));
  }
  
  .contact-card {
    background-color: white;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
    padding: 2rem !important;
    text-align: center;
    height: 100%;
    transition: all var(--transition-normal);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
  }
  
  .contact-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    transition: all var(--transition-normal);
  }
  
  .contact-card:hover {
    transform: translateY(-8px);
    box-shadow: var(--shadow-lg) !important;
  }
  
  .contact-card.emergency::before {
    background: linear-gradient(to right, var(--primary), #FF5722);
  }
  
  .contact-card.email::before {
    background: linear-gradient(to right, #00897B, #4CAF50);
  }
  
  .contact-card.visit::before {
    background: linear-gradient(to right, var(--info), #00BCD4);
  }
  
  .card-icon {
    margin-bottom: 1.5rem;
    color: var(--text-light);
    transition: all var(--transition-normal);
  }
  
  .contact-card:hover .card-icon {
    color: var(--primary);
    transform: scale(1.1);
  }
  
  .contact-card.emergency:hover .card-icon {
    color: var(--primary);
  }
  
  .contact-card.email:hover .card-icon {
    color: #00897B;
  }
  
  .contact-card.visit:hover .card-icon {
    color: var(--info);
  }
  
  .contact-card h3 {
    margin-bottom: 1rem !important;
    color: var(--dark) !important;
  }
  
  .contact-card p {
    color: var(--text-light) !important;
    margin-bottom: 1.5rem !important;
    flex-grow: 1;
    line-height: 1.6;
  }
  
  .contact-card .button {
    margin-top: auto;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
  }
  
  /* Tabs Styling */
  .tabs.is-centered.is-boxed.is-medium {
    margin-bottom: 3rem !important;
  }
  
  .tabs.is-boxed li.is-active a {
    border-color: var(--primary) !important;
    color: var(--primary) !important;
    background-color: rgba(229, 57, 53, 0.05) !important;
  }
  
  .tabs a {
    transition: all var(--transition-fast) !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    font-weight: 500 !important;
    padding: 1rem 1.5rem !important;
  }
  
  .tabs a:hover {
    border-bottom-color: var(--primary) !important;
    color: var(--primary) !important;
    background-color: rgba(229, 57, 53, 0.02) !important;
  }
  
  .tab-content {
    padding: 2rem 0;
    min-height: 500px;
  }
  
  /* Contact Form Container */
  .contact-form-container {
    padding: 2rem !important;
    border-radius: var(--radius-lg) !important;
    background: linear-gradient(to bottom, white, rgba(248, 249, 250, 0.5)) !important;
    box-shadow: var(--shadow-md) !important;
    border: 1px solid var(--border-light);
  }
  
  .contact-form-container h2 {
    color: var(--dark) !important;
    margin-bottom: 2rem !important;
    position: relative;
  }
  
  .contact-form-container h2::after {
    content: '';
    position: absolute;
    bottom: -0.5rem;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 3px;
    background-color: var(--primary);
    border-radius: 2px;
  }
  
  /* Contact Information */
  .info-box {
    height: 100%;
    background: linear-gradient(135deg, white, var(--bg-light)) !important;
    border: 1px solid var(--border-light);
  }
  
  .contact-details {
    margin: 2rem 0;
  }
  
  .contact-detail {
    display: flex;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background-color: rgba(229, 57, 53, 0.03);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--primary);
    transition: all var(--transition-normal);
  }
  
  .contact-detail:hover {
    background-color: rgba(229, 57, 53, 0.05);
    transform: translateX(5px);
  }
  
  .contact-detail .icon {
    margin-right: 1rem;
    margin-top: 5px;
    color: var(--primary) !important;
    flex-shrink: 0;
  }
  
  .contact-detail strong {
    color: var(--dark);
    display: block;
    margin-bottom: 0.25rem;
  }
  
  .contact-detail a {
    color: var(--primary) !important;
    text-decoration: none;
    transition: all var(--transition-fast);
  }
  
  .contact-detail a:hover {
    color: var(--primary-dark) !important;
    text-decoration: underline;
  }
  
  .opening-hours {
    background-color: white !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm) !important;
  }
  
  .opening-hours tr {
    border-bottom: 1px solid var(--border-light) !important;
    transition: all var(--transition-fast);
  }
  
  .opening-hours tr:hover {
    background-color: var(--bg-light) !important;
  }
  
  .opening-hours tr:last-child {
    border-bottom: none !important;
  }
  
  .opening-hours td {
    padding: 0.75rem 1rem !important;
    vertical-align: middle !important;
  }
  
  .opening-hours td:first-child {
    font-weight: 600;
    color: var(--dark);
  }
  
  .opening-hours td:last-child {
    color: var(--text-light);
    font-weight: 500;
  }
  
  /* Map Container */
  .map-container {
    height: 100%;
    background: linear-gradient(135deg, white, var(--bg-light)) !important;
    border: 1px solid var(--border-light);
  }
  
  .map-wrapper {
    position: relative;
    width: 100%;
    height: 400px;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-sm) !important;
    border: 2px solid var(--border-light);
  }
  
  .map-wrapper iframe {
    border-radius: var(--radius-md) !important;
  }
  
  .map-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, var(--bg-light), var(--bg-gray));
    color: var(--text-light);
  }
  
  .map-loading .icon {
    margin-bottom: 1rem;
    color: var(--primary) !important;
  }
  
  /* FAQ Section */
  .faq-section {
    background: linear-gradient(135deg, var(--bg-light), white) !important;
    padding: 5rem 1.5rem !important;
    position: relative;
    overflow: hidden;
  }
  
  .faq-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: radial-gradient(circle at 20% 50%, rgba(229, 57, 53, 0.03) 0%, transparent 50%),
                      radial-gradient(circle at 80% 20%, rgba(33, 150, 243, 0.03) 0%, transparent 50%);
    z-index: 1;
  }
  
  .faq-section .container {
    position: relative;
    z-index: 2;
  }
  
  .faq-section .title {
    margin-bottom: 3rem !important;
    position: relative;
  }
  
  .faq-section .title::after {
    content: '';
    position: absolute;
    bottom: -1rem;
    left: 50%;
    transform: translateX(-50%);
    width: 80px;
    height: 4px;
    background: linear-gradient(to right, var(--primary), var(--info));
    border-radius: 2px;
  }
  
  .faq-item {
    background-color: white !important;
    padding: 2rem !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
    height: 100%;
    transition: all var(--transition-normal);
    border: 1px solid var(--border-light);
    position: relative;
    overflow: hidden;
  }
  
  .faq-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(to bottom, var(--primary), var(--info));
    transition: width var(--transition-normal);
  }
  
  .faq-item:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg) !important;
  }
  
  .faq-item:hover::before {
    width: 8px;
  }
  
  .faq-item h3 {
    margin-bottom: 1rem !important;
    color: var(--dark) !important;
    line-height: 1.3;
    font-size: 1.25rem !important;
  }
  
  .faq-item p {
    color: var(--text-light) !important;
    line-height: 1.6;
    margin: 0 !important;
  }
  
  /* Contact CTA at bottom */
  .faq-section .has-text-centered {
    margin-top: 4rem;
    padding: 2rem;
    background: linear-gradient(135deg, rgba(229, 57, 53, 0.05), rgba(33, 150, 243, 0.05));
    border-radius: var(--radius-lg);
    border: 1px solid rgba(229, 57, 53, 0.1);
  }
  
  .faq-section .subtitle {
    margin-bottom: 1.5rem !important;
    color: var(--text) !important;
  }
  
  /* Responsive adjustments */
  @media screen and (max-width: 768px) {
    .contact-hero {
      padding: 4rem 1rem !important;
      background-attachment: scroll;
    }
    
    .contact-options {
      padding: 2rem 1rem !important;
    }
    
    .contact-card {
      margin-bottom: 2rem;
    }
    
    .contact-detail {
      flex-direction: column;
      text-align: center;
    }
    
    .contact-detail .icon {
      margin-bottom: 0.5rem;
      margin-right: 0;
    }
    
    .map-wrapper {
      height: 300px;
    }
    
    .faq-section {
      padding: 3rem 1rem !important;
    }
    
    .faq-item {
      padding: 1.5rem !important;
      margin-bottom: 1.5rem;
    }
    
    .contact-form-container {
      padding: 1.5rem !important;
    }
    
    .tab-content {
      min-height: auto;
    }
  }
  
  /* Animation classes */
  .contact-card {
    animation: slideUp 0.6s ease-out;
  }
  
  .contact-card:nth-child(2) {
    animation-delay: 0.1s;
  }
  
  .contact-card:nth-child(3) {
    animation-delay: 0.2s;
  }
  
  .faq-item {
    animation: slideUp 0.6s ease-out;
  }
  
  .faq-item:nth-child(2) {
    animation-delay: 0.1s;
  }
  
  .faq-item:nth-child(3) {
    animation-delay: 0.2s;
  }
  
  .faq-item:nth-child(4) {
    animation-delay: 0.3s;
  }
  
  /* Notification warning style */
  .notification.is-warning.is-light {
    background-color: rgba(255, 152, 0, 0.1) !important;
    border: 1px solid rgba(255, 152, 0, 0.3) !important;
    color: #E65100 !important;
    border-radius: var(--radius-md) !important;
  }
  
  .notification.is-warning.is-light .icon {
    color: var(--warning) !important;
  }
</style>