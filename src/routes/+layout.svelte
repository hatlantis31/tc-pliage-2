<script>
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import '../app.css';

  let { children } = $props();
</script>

<Header />

<!-- Site-wide drafting grid. Sits behind all content so every page picks up
     the industrial texture without needing its own overlay. -->
<div class="fixed inset-0 bg-blueprint opacity-45 pointer-events-none -z-10" aria-hidden="true"></div>

<main class="relative min-h-screen">
  {@render children()}
</main>
<Footer />
