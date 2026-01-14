<script>
  // Accept both old and new prop formats (keep your existing code)
  export let service = null;
  export let title = null;
  export let image = null;
  export let description = null;

  // Use service object if provided, otherwise use individual props
  $: displayTitle = service ? service.titre : title;
  $: displayImage = service ? service.image : image; // This now works with full URLs
  $: displayDescription = service ? service.description : description;
  $: characteristics = service ? service.caracteristiques : [];
  
  // Keep all your existing onMount and animation code...
  import { onMount } from 'svelte';
  let isVisible = false;


  onMount(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          isVisible = true;
          observer.disconnect();
        }
      });
    }, { threshold: 0.1 });
    
    const serviceCard = document.querySelector('.service-card');
    if (serviceCard) {
      observer.observe(serviceCard);
    }
    
    return () => {
      observer.disconnect();
    };
  });
</script>

<!-- Keep all your existing HTML template - just the image src will now work properly -->
{#if service}
  <div class="service-card" class:is-visible={isVisible}>
    <div class="columns is-vcentered">
      <div class="column is-5 image-column">
        <div class="service-image-container">
          {#if displayImage}
            <img src={displayImage} alt={displayTitle} class="service-image">
          {:else}
            <!-- Fallback image when no image is uploaded -->
            <img src="/images/services/default.jpg" alt={displayTitle} class="service-image">
          {/if}
          <div class="service-overlay"></div>
        </div>
      </div>
      
      <div class="column is-7 content-column">
        <div class="service-content">
          <h3 class="service-title">{displayTitle}</h3>
          <div class="title-underline"></div>
          <p class="service-description">{displayDescription}</p>
          
          {#if characteristics && characteristics.length > 0}
            <ul class="service-features">
              {#each characteristics as characteristic}
                <li>
                  <span class="icon"><i class="fas fa-check-circle"></i></span>
                  <span>{typeof characteristic === 'string' ? characteristic : characteristic.description}</span>
                </li>
              {/each}
            </ul>
          {/if}
          
          <div class="service-actions">
            <a href="/contact?service={encodeURIComponent(displayTitle)}" class="button is-primary">Demander un Devis</a>
            <a href="/about" class="button is-light">En savoir plus</a>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}


<style>
  /* Main service card */
  .service-card {
    background: linear-gradient(135deg, var(--bg-white), var(--bg-light));
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
    margin-bottom: 3rem;
    transform: translateY(30px);
    opacity: 0;
    transition: all 0.5s ease;
    border-left: 4px solid var(--primary);
  }
  
  .service-card.is-visible {
    transform: translateY(0);
    opacity: 1;
  }
  
  .service-card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-5px);
  }
  
  .service-image-container {
    position: relative;
    height: 100%;
    min-height: 300px;
    overflow: hidden;
    border-radius: var(--radius-md);
  }
  
  .service-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
  }
  
  .service-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to right, rgba(46, 64, 87, 0.7), rgba(171, 0, 13, 0.4));
    opacity: 0.3;
    transition: opacity 0.3s ease;
  }
  
  .service-image-container:hover .service-image {
    transform: scale(1.05);
  }
  
  .service-image-container:hover .service-overlay {
    opacity: 0.5;
  }
  
  .service-content {
    padding: 2rem;
  }
  
  .service-title {
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--dark) !important;
    margin-bottom: 1rem !important;
    line-height: 1.2;
  }
  
  .title-underline {
    height: 4px;
    width: 60px;
    background-color: var(--primary);
    margin-bottom: 1.5rem;
    border-radius: 2px;
  }
  
  .title-underline.small {
    width: 40px;
    height: 3px;
  }
  
  .service-description {
    color: var(--text-light) !important;
    margin-bottom: 1.5rem !important;
    font-size: 1.1rem !important;
    line-height: 1.6;
  }
  
  .service-features {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 0 2rem !important;
  }
  
  .service-features li {
    display: flex;
    align-items: flex-start;
    margin-bottom: 0.75rem;
    font-weight: 500;
    background-color: rgba(229, 57, 53, 0.08);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    margin-bottom: 0.5rem;
    transition: all 0.3s ease;
  }
  
  .service-features li:hover {
    background-color: rgba(229, 57, 53, 0.12);
    transform: translateX(5px);
  }
  
  .service-features li .icon {
    color: var(--primary) !important;
    margin-right: 0.75rem;
    flex-shrink: 0;
  }
  
  .service-actions {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }
  
  .service-actions .button {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    border-radius: var(--radius-md) !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
  }
  
  .service-actions .button.is-primary {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
  }
  
  .service-actions .button.is-primary:hover {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md) !important;
  }
  
  .service-actions .button.is-light {
    background-color: var(--bg-light) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
  }
  
  .service-actions .button.is-light:hover {
    background-color: var(--border) !important;
    border-color: var(--border-dark) !important;
    transform: translateY(-2px);
  }
  
  /* Simple card version */
  .simple-service-card {
    height: 100%;
    transform: translateY(30px);
    opacity: 0;
    transition: all 0.5s ease;
    background: linear-gradient(to bottom, var(--bg-white) 70%, rgba(229, 57, 53, 0.05) 100%) !important;
    border-top: 3px solid var(--primary) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden;
    box-shadow: var(--shadow-md) !important;
  }
  
  .simple-service-card.is-visible {
    transform: translateY(0);
    opacity: 1;
  }
  
  .simple-service-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg) !important;
  }
  
  .simple-service-card .card-image {
    position: relative;
    overflow: hidden;
    height: 200px;
  }
  
  .simple-service-card .card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.5s ease;
  }
  
  .simple-service-card:hover .card-image img {
    transform: scale(1.08);
  }
  
  .card-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 60%);
  }
  
  .simple-service-card .card-content {
    padding: 1.5rem !important;
    position: relative;
  }
  
  .simple-service-card .card-title {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.75rem !important;
    color: var(--dark) !important;
    line-height: 1.3;
  }
  
  .simple-service-card .card-description {
    color: var(--text-light) !important;
    margin-bottom: 1.5rem !important;
    line-height: 1.5;
  }
  
  .card-link {
    display: inline-flex !important;
    align-items: center;
    color: var(--primary) !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    text-decoration: none;
  }
  
  .card-link .icon {
    margin-left: 0.5rem;
    transition: transform 0.3s ease;
  }
  
  .card-link:hover {
    color: var(--primary-dark) !important;
  }
  
  .card-link:hover .icon {
    transform: translateX(3px);
  }
  
  /* Responsive Adjustments */
  @media screen and (max-width: 768px) {
    .service-card .columns {
      flex-direction: column !important;
    }
    
    .service-image-container {
      min-height: 200px;
    }
    
    .service-title {
      font-size: 1.75rem !important;
    }
    
    .service-content {
      padding: 1.5rem;
    }
    
    .service-actions {
      flex-direction: column;
    }
    
    .service-actions .button {
      width: 100%;
      justify-content: center;
    }
    
    .simple-service-card .card-image {
      height: 160px;
    }
  }
  
  /* Animation delays for multiple cards */
  .service-card:nth-child(2) {
    transition-delay: 0.1s;
  }
  
  .service-card:nth-child(3) {
    transition-delay: 0.2s;
  }
  
  .service-card:nth-child(4) {
    transition-delay: 0.3s;
  }
  
  /* Focus states for accessibility */
  .card-link:focus,
  .service-actions .button:focus {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
  }
  
  /* Loading states */
  .service-card.is-loading {
    opacity: 0.7;
  }
  
  .service-card.is-loading::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 2rem;
    height: 2rem;
    border: 3px solid var(--border);
    border-top: 3px solid var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    transform: translate(-50%, -50%);
  }
  
  @keyframes spin {
    0% { transform: translate(-50%, -50%) rotate(0deg); }
    100% { transform: translate(-50%, -50%) rotate(360deg); }
  }
</style>