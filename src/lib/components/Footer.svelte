<script>
  const currentYear = new Date().getFullYear();
  
  // Animate footer elements on scroll
  import { onMount } from 'svelte';
  
  let footerVisible = false;
  
  onMount(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          footerVisible = true;
          observer.disconnect();
        }
      });
    }, { threshold: 0.2 });
    
    const footerElement = document.querySelector('.footer');
    if (footerElement) {
      observer.observe(footerElement);
    }
    
    return () => {
      observer.disconnect();
    };
  });
</script>

<footer class="footer" class:is-visible={footerVisible}>
  <div class="container">
    <div class="footer-top">
      <div class="columns is-multiline">
        <div class="column is-5">
          <div class=" animate-item">
            <img src="/favicon.jpg" alt="TCPliage Logo" width="180">
            <p class="mt-4">
              TC PLIAGE, votre partenaire métallurgique de confiance depuis 2016. Notre savoir-faire et notre réactivité au service de vos projets.
            </p>
            <div class="social-links">
              <a href="#" class="social-link" aria-label="Facebook">
                <i class="fab fa-facebook-f"></i>
              </a>
              <a href="#" class="social-link" aria-label="LinkedIn">
                <i class="fab fa-linkedin-in"></i>
              </a>
              <a href="#" class="social-link" aria-label="Instagram">
                <i class="fab fa-instagram"></i>
              </a>
            </div>
          </div>
        </div>
        
        <div class="column is-2-tablet is-6-mobile">
          <div class="footer-nav animate-item">
            <h3 class="footer-title">Navigation</h3>
            <ul class="footer-links">
              <li><a href="/">Accueil</a></li>
              <li><a href="/services">Services</a></li>
              <li><a href="/about">À Propos</a></li>
              <li><a href="/designer">Dessin en ligne</a></li>
              <li><a href="/contact">Contact</a></li>
            </ul>
          </div>
        </div>
        
        <div class="column is-2-tablet is-6-mobile">
          <div class="footer-nav animate-item">
            <h3 class="footer-title">Nos Services</h3>
            <ul class="footer-links">
              <li><a href="/services">Fabrication d'Urgence</a></li>
              <li><a href="/services">Pièces Sur Mesure</a></li>
              <li><a href="/services">Couvertines</a></li>
              <li><a href="/services">Habillages Métalliques</a></li>
              <li><a href="/services">Quincaillerie</a></li>
            </ul>
          </div>
        </div>
        
        <div class="column is-3-tablet is-12-mobile">
          <div class="footer-contact animate-item">
            <h3 class="footer-title">Contact</h3>
            <ul class="contact-details">
              <li>
                <i class="fas fa-map-marker-alt"></i>
                <span>3 Avenue du Bois Vert, <br>Portet-Sur-Garonne</span>
              </li>
              <li>
                <i class="fas fa-phone"></i>
                <span>Standard: <a href="tel:standard-phone">01 23 45 67 89</a></span>
              </li>
              <li>
                <i class="fas fa-phone-volume"></i>
                <span>Urgence: <a href="tel:emergency-phone" class="emergency">01 23 45 67 90</a></span>
              </li>
              <li>
                <i class="fas fa-envelope"></i>
                <span><a href="mailto:contact@tcpliage.fr">contact@tcpliage.fr</a></span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    
    <div class="footer-bottom">
      <div class="columns is-vcentered">
        <div class="column">
          <p class="copyright">
            © {currentYear} TCPliage. Tous droits réservés.
          </p>
        </div>
        <div class="column has-text-right-tablet">
          <div class="legal-links">
            <a href="#">Mentions Légales</a>
            <span class="separator">|</span>
            <a href="#">Politique de confidentialité</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</footer>


<style>
  .footer {
    background: linear-gradient(135deg, var(--secondary), var(--secondary-dark)) !important;
    color: white;
    padding-top: 4rem !important;
    padding-bottom: 2rem !important;
    margin-top: 5rem;
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.6s ease;
    position: relative;
    overflow: hidden;
  }
  
  .footer::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(to right, var(--primary), var(--warning), var(--info));
  }
  
  .footer.is-visible {
    opacity: 1;
    transform: translateY(0);
  }
  
  .footer-top {
    margin-bottom: 3rem;
  }
  
  .animate-item {
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.5s ease;
  }
  
  .footer.is-visible .animate-item {
    opacity: 1;
    transform: translateY(0);
  }
  
  .footer.is-visible .animate-item:nth-child(2) {
    transition-delay: 0.1s;
  }
  
  .footer.is-visible .animate-item:nth-child(3) {
    transition-delay: 0.2s;
  }
  
  .footer.is-visible .animate-item:nth-child(4) {
    transition-delay: 0.3s;
  }
  
  .footer-brand img {
    max-width: 180px;
    height: auto;
    filter: brightness(0) invert(1);
    margin-bottom: 1rem;
  }
  
  .footer-brand p {
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }
  
  .social-links {
    display: flex;
    gap: 1rem;
  }
  
  .social-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background-color: rgba(255, 255, 255, 0.1);
    color: white !important;
    border-radius: 50%;
    transition: all 0.3s ease;
    text-decoration: none;
  }
  
  .social-link:hover {
    background-color: var(--primary);
    color: white !important;
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(229, 57, 53, 0.3);
  }
  
  .footer-title {
    color: white !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    margin-bottom: 1.5rem !important;
    position: relative;
    padding-bottom: 0.5rem;
  }
  
  .footer-title::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 40px;
    height: 3px;
    background-color: var(--primary);
    border-radius: 2px;
  }
  
  .footer-links {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  .footer-links li {
    margin-bottom: 0.75rem;
  }
  
  .footer-links a {
    color: rgba(255, 255, 255, 0.8) !important;
    text-decoration: none;
    transition: all 0.3s ease;
    position: relative;
    padding-left: 1rem;
  }
  
  .footer-links a::before {
    content: '▸';
    position: absolute;
    left: 0;
    color: var(--primary);
    transition: all 0.3s ease;
  }
  
  .footer-links a:hover {
    color: white !important;
    padding-left: 1.25rem;
  }
  
  .footer-links a:hover::before {
    color: var(--primary);
  }
  
  .contact-details {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  .contact-details li {
    display: flex;
    align-items: flex-start;
    margin-bottom: 1rem;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .contact-details i {
    color: var(--primary);
    margin-right: 0.75rem;
    margin-top: 0.2rem;
    flex-shrink: 0;
    width: 16px;
  }
  
  .contact-details a {
    color: rgba(255, 255, 255, 0.8) !important;
    text-decoration: none;
    transition: all 0.3s ease;
  }
  
  .contact-details a:hover {
    color: white !important;
  }
  
  .contact-details a.emergency {
    color: var(--warning) !important;
    font-weight: 600;
  }
  
  .contact-details a.emergency:hover {
    color: #FFB74D !important;
  }
  
  .footer-bottom {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 2rem;
    margin-top: 2rem;
  }
  
  .copyright {
    color: rgba(255, 255, 255, 0.7) !important;
    margin: 0 !important;
    font-size: 0.9rem;
  }
  
  .legal-links {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }
  
  .legal-links a {
    color: rgba(255, 255, 255, 0.7) !important;
    text-decoration: none;
    transition: all 0.3s ease;
  }
  
  .legal-links a:hover {
    color: white !important;
  }
  
  .separator {
    color: rgba(255, 255, 255, 0.3);
  }
  
  /* Responsive adjustments */
  @media screen and (max-width: 768px) {
    .footer {
      padding-top: 3rem !important;
      margin-top: 3rem;
    }
    
    .footer-top {
      margin-bottom: 2rem;
    }
    
    .footer-brand {
      text-align: center;
      margin-bottom: 2rem;
    }
    
    .footer-nav, .footer-contact {
      margin-bottom: 2rem;
    }
    
    .legal-links {
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 1rem;
    }
    
    .social-links {
      justify-content: center;
    }
  }
  
  @media screen and (max-width: 1023px) {
    .legal-links {
      justify-content: center;
      margin-top: 1rem;
    }
  }
</style>