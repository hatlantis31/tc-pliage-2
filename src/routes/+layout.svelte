<!-- src/routes/+layout.svelte -->
<script>
  import 'bulma/css/bulma.min.css';
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import '../app.css';
</script>
<!-- Force light theme by adding class to HTML element -->
<svelte:head>
  <script>
    // Force light theme regardless of system preferences
    document.documentElement.classList.add('light-theme');
    document.documentElement.style.colorScheme = 'light';
  </script>
</svelte:head>

<Header />

<main>
  <slot />
</main>

<Footer />

<style>
  main {
    min-height: calc(100vh - 14rem);
    overflow-x: hidden; /* Prevent horizontal scrolling */
  }
  
  /* Add smooth scrolling for better user experience */
  :global(html) {
    scroll-behavior: smooth;
  }

  /* Improve focus styling for accessibility */
  :global(*:focus) {
    outline: 2px solid #3273dc;
    outline-offset: 2px;
  }
  
  /* Improve touch targets for mobile */
  @media (max-width: 768px) {
    :global(.button, .navbar-item) {
      padding: 0.5em 1em;
    }
  }
</style>