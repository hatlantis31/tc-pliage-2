<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  let isOpen = $state(false);
  let scrolled = $state(false);

  const links = [
    { href: '/', label: 'Accueil' },
    { href: '/services', label: 'Services' },
    { href: '/about', label: 'À Propos' },
    { href: '/designer', label: 'Dessin en ligne' },
    { href: '/contact', label: 'Contact' },
  ];

  function toggleMenu() {
    isOpen = !isOpen;
    document.body.style.overflow = isOpen ? 'hidden' : '';
  }

  function closeMenu() {
    isOpen = false;
    document.body.style.overflow = '';
  }

  onMount(() => {
    const onScroll = () => { scrolled = window.scrollY > 40; };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  });
</script>

<header
  class="fixed top-0 left-0 right-0 z-50 transition-all duration-300
    {scrolled
      ? 'bg-zinc-950 shadow-lg shadow-black/40 border-b border-zinc-800'
      : 'bg-zinc-950/80 backdrop-blur-sm border-b border-transparent'}"
>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">

      <!-- Logo -->
      <a href="/" onclick={closeMenu} class="flex items-center flex-shrink-0">
        <img src="/logo.jpg" alt="TC Pliage" class="h-10 w-auto object-contain">
      </a>

      <!-- Desktop nav -->
      <nav class="hidden lg:flex items-center gap-1">
        {#each links as link}
          <a
            href={link.href}
            class="px-4 py-2 text-sm font-medium rounded transition-colors duration-150
              {$page.url.pathname === link.href
                ? 'text-red-400 bg-red-950/30'
                : 'text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800'}"
          >
            {link.label}
          </a>
        {/each}
      </nav>

      <!-- Desktop CTA -->
      <div class="hidden lg:flex">
        <a
          href="tel:0123456790"
          class="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold px-4 py-2 rounded transition-colors duration-150"
        >
          <i class="fas fa-phone text-xs"></i>
          Urgence 24/7
        </a>
      </div>

      <!-- Mobile burger -->
      <button
        onclick={toggleMenu}
        class="lg:hidden p-2 rounded text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
        aria-label="Menu"
        aria-expanded={isOpen}
      >
        <i class="fas {isOpen ? 'fa-times' : 'fa-bars'} text-lg"></i>
      </button>
    </div>
  </div>

  <!-- Mobile menu -->
  {#if isOpen}
    <div class="lg:hidden bg-zinc-950 border-t border-zinc-800">
      <nav class="px-4 py-4 flex flex-col gap-1">
        {#each links as link}
          <a
            href={link.href}
            onclick={closeMenu}
            class="px-4 py-3 text-base font-medium rounded transition-colors
              {$page.url.pathname === link.href
                ? 'text-red-400 bg-red-950/30'
                : 'text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800'}"
          >
            {link.label}
          </a>
        {/each}
        <a
          href="tel:0123456790"
          onclick={closeMenu}
          class="mt-2 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-4 py-3 rounded transition-colors"
        >
          <i class="fas fa-phone text-sm"></i>
          Urgence 24/7 — 01 23 45 67 90
        </a>
      </nav>
    </div>
  {/if}
</header>

<!-- Spacer for fixed header -->
<div class="h-16"></div>
