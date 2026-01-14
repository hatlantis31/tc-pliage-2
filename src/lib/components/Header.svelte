<script>
  import { onMount } from 'svelte';
  
  let isActive = false;
  let isScrolled = false;
  let lastScrollY = 0;
  let isNavHidden = false;
  
  onMount(() => {
    const handleScroll = () => {
      // Detect scroll direction for hiding/showing navbar
      const currentScrollY = window.scrollY;
      isNavHidden = currentScrollY > lastScrollY && currentScrollY > 200;
      lastScrollY = currentScrollY;
      
      // Apply style change on scroll
      isScrolled = window.scrollY > 50;
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  });
  
  function toggleMenu() {
    isActive = !isActive;
    // Prevent scrolling when menu is open on mobile
    if (isActive) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
  }
</script>

<header class="site-header {isScrolled ? 'is-scrolled' : ''} {isNavHidden ? 'is-hidden' : ''}">
  <div class="container">
    <nav class="navbar" role="navigation" aria-label="Menu principal">
      <div class="navbar-brand">
        <a class="navbar-item logo-container" href="/">
          <img class="logo" src="/logo.jpg" alt="TCPliage - Fabrication métallique d'urgence">
        </a>

        <!-- Emergency button for mobile -->
        <a href="tel:your-emergency-number" class="navbar-item is-hidden-desktop emergency-call">
          <span class="icon has-text-danger">
            <i class="fas fa-phone-alt"></i>
          </span>
          <span>Urgence</span>
        </a>

        <button
          class="navbar-burger {isActive ? 'is-active' : ''}"
          aria-label="menu"
          aria-expanded="{isActive}"
          on:click={toggleMenu}
        >
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
        </button>
      </div>

      <div class="navbar-menu {isActive ? 'is-active' : ''}">
        <div class="navbar-end">
          <a class="navbar-item" href="/" on:click={() => isActive = false}>Accueil</a>
          <a class="navbar-item" href="/services" on:click={() => isActive = false}>Services</a>
          <a class="navbar-item" href="/about" on:click={() => isActive = false}>À Propos</a>
          <a class="navbar-item" href="/designer" on:click={() => isActive = false}>Dessin en ligne</a>
          <a class="navbar-item" href="/contact" on:click={() => isActive = false}>Contact</a>
          
          <!-- Emergency Call Button -->
          <div class="navbar-item is-hidden-touch">
            <a href="tel:your-emergency-number" class="button is-danger">
              <span class="icon">
                <i class="fas fa-phone-alt"></i>
              </span>
              <span>Service d'Urgence 24/7</span>
            </a>
          </div>
        </div>
      </div>
    </nav>
  </div>
</header>

/* Header.svelte CSS */
<style>
  /* CSS Variables for consistency */
  :root {
    --primary: #E53935;
    --primary-dark: #C62828;
    --secondary: #2E4057;
    --secondary-dark: #1a2d40;
    --dark: #333333;
    --text: #555555;
    --text-light: #777777;
    --bg-white: #e0e0e0;
    --bg-light: #e0e0e0;
    --border: #e0e0e0;
    --border-dark: #cccccc;
    --success: #4CAF50;
    --warning: #FF9800;
    --info: #2196F3;
    --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.12);
    --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.15);
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
  }

  .site-header {
    position: fixed !important;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    transition: all 0.3s ease;
    background: #e0e0e0 !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    border-bottom: 3px solid var(--primary);
  }
  
  .site-header.is-scrolled {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    background-color: #e0e0e0 !important;
  }
  
  .site-header.is-hidden {
    transform: translateY(-100%);
  }
  
  .navbar {
    background-color: transparent !important;
    min-height: 4.5rem;
    padding: 0.5rem 0;
  }
  
  .logo-container {
    padding: 0.25rem 0.75rem !important;
  }
  
  .logo {
    height: 3rem !important;
    width: auto;
    max-height: none !important;
    object-fit: contain;
    transition: all 0.3s ease;
  }
  
  .is-scrolled .logo {
    height: 2.5rem !important;
  }
  
  .navbar-item {
    font-weight: 600 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    color: var(--text) !important;
    padding: 0.5rem 1rem !important;
    margin: 0 0.25rem;
    transition: all 0.3s ease;
    position: relative;
    border-radius: var(--radius-sm);
  }
  
  .navbar-item::after {
    content: "";
    position: absolute;
    width: 0;
    height: 3px;
    bottom: 0;
    left: 50%;
    background-color: var(--primary);
    transition: all 0.3s ease;
    transform: translateX(-50%);
  }
  
  .navbar-item:hover {
    color: var(--primary) !important;
    background-color: rgba(229, 57, 53, 0.05) !important;
  }
  
  .navbar-item:hover::after {
    width: 70%;
  }
  
  /* Current page indicator - add class 'is-active' to current page nav item */
  .navbar-item.is-active {
    color: var(--primary) !important;
    background-color: rgba(229, 57, 53, 0.1) !important;
  }
  
  .navbar-item.is-active::after {
    width: 70%;
  }
  
  .navbar-burger {
    height: 4.5rem !important;
    width: 4.5rem !important;
    background: none !important;
    border: none !important;
    cursor: pointer;
    padding: 0 !important;
    color: var(--text);
  }
  
  .navbar-burger span {
    height: 2px !important;
    width: 30px !important;
    left: calc(50% - 15px) !important;
    background-color: var(--text) !important;
    transition: all 0.3s ease;
  }
  
  .navbar-burger:hover span {
    background-color: var(--primary) !important;
  }
  
  .navbar-burger.is-active span:nth-child(1) {
    transform: translateY(7px) rotate(45deg) !important;
  }
  
  .navbar-burger.is-active span:nth-child(2) {
    opacity: 0 !important;
  }
  
  .navbar-burger.is-active span:nth-child(3) {
    transform: translateY(-7px) rotate(-45deg) !important;
  }
  
  .emergency-call {
    background-color: rgba(229, 57, 53, 0.1) !important;
    color: var(--primary) !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    margin-right: 0.5rem;
  }
  
  .emergency-call:hover {
    background-color: rgba(229, 57, 53, 0.15) !important;
  }
  
  /* Emergency button in navbar */
  .navbar-item .button.is-danger {
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    color: white !important;
    font-weight: 600;
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
  }
  
  .navbar-item .button.is-danger:hover {
    background-color: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
  
  /* Mobile menu styles */
  @media screen and (max-width: 1023px) {
    :global(body) {
      padding-top: 4.5rem;
    }
    
    .navbar-menu {
      position: fixed !important;
      top: 4.5rem;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: white !important;
      padding: 1rem !important;
      display: flex !important;
      flex-direction: column;
      align-items: stretch;
      opacity: 0;
      pointer-events: none;
      transform: translateY(-10px);
      transition: all 0.3s ease;
      box-shadow: none !important;
      overflow-y: auto;
    }
    
    .navbar-menu.is-active {
      opacity: 1 !important;
      pointer-events: auto;
      transform: translateY(0);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
    }
    
    .navbar-end {
      flex-direction: column !important;
      margin-top: 1rem;
    }
    
    .navbar-item {
      padding: 1rem !important;
      margin: 0.25rem 0 !important;
      text-align: center;
      font-size: 1.25rem !important;
      border-radius: var(--radius-md) !important;
    }
    
    .navbar-item:hover {
      background-color: rgba(229, 57, 53, 0.1) !important;
    }
    
    .navbar-item::after {
      display: none;
    }
    
    .emergency-call {
      margin: 0.5rem 0 !important;
      justify-content: center;
    }
  }
  
  /* Larger screens */
  @media screen and (min-width: 1024px) {
    :global(body) {
      padding-top: 4.5rem;
    }
    
    .navbar-menu {
      display: flex !important;
      background-color: transparent !important;
    }
    
    .navbar-end {
      align-items: center;
    }
  }
</style>