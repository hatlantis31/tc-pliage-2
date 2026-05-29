<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  let isOpen = $state(false);
  let scrolled = $state(false);

  const links = [
    { href: '/',         label: 'Accueil' },
    { href: '/services', label: 'Services' },
    { href: '/about',    label: 'À Propos' },
    { href: '/designer', label: 'Dessin en ligne' },
    { href: '/contact',  label: 'Contact' },
  ];

  function toggleMenu() { isOpen = !isOpen; document.body.style.overflow = isOpen ? 'hidden' : ''; }
  function closeMenu()  { isOpen = false;  document.body.style.overflow = ''; }

  onMount(() => {
    const onScroll = () => { scrolled = window.scrollY > 40; };
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  });

  const TIER_CLS = {
    Bronze: 'bg-amber-900/30 border-amber-700/40 text-amber-300',
    Argent: 'bg-zinc-700/60 border-zinc-500/40 text-zinc-200',
    Or:     'bg-yellow-900/30 border-yellow-600/40 text-yellow-300'
  };
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
          <a href={link.href}
            class="px-4 py-2 text-sm font-medium rounded transition-colors duration-150
              {$page.url.pathname === link.href
                ? 'text-red-400 bg-red-950/30'
                : 'text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800'}">
            {link.label}
          </a>
        {/each}
      </nav>

      <!-- Desktop right: auth + CTA -->
      <div class="hidden lg:flex items-center gap-2">
        {#if $page.data.user}
          {@const tier = null}
          <a href="/account"
            class="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 text-sm transition-all">
            <i class="fas fa-user-circle text-red-500 text-sm"></i>
            <span class="max-w-[120px] truncate">{$page.data.user.name}</span>
          </a>
        {:else}
          <a href="/auth/login"
            class="px-3 py-1.5 text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors">
            Connexion
          </a>
          <a href="/auth/register"
            class="px-3 py-1.5 text-sm font-medium border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-zinc-100 rounded-lg transition-all">
            S'inscrire
          </a>
        {/if}
        <a href="tel:0123456790"
          class="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white text-sm font-semibold px-4 py-2 rounded transition-colors duration-150">
          <i class="fas fa-phone text-xs"></i>
          Urgence 24/7
        </a>
      </div>

      <!-- Mobile burger -->
      <button onclick={toggleMenu}
        class="lg:hidden p-2 rounded text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
        aria-label="Menu" aria-expanded={isOpen}>
        <i class="fas {isOpen ? 'fa-times' : 'fa-bars'} text-lg"></i>
      </button>
    </div>
  </div>

  <!-- Mobile menu -->
  {#if isOpen}
    <div class="lg:hidden bg-zinc-950 border-t border-zinc-800">
      <nav class="px-4 py-4 flex flex-col gap-1">
        {#each links as link}
          <a href={link.href} onclick={closeMenu}
            class="px-4 py-3 text-base font-medium rounded transition-colors
              {$page.url.pathname === link.href
                ? 'text-red-400 bg-red-950/30'
                : 'text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800'}">
            {link.label}
          </a>
        {/each}
        <div class="border-t border-zinc-800 mt-2 pt-3 space-y-2">
          {#if $page.data.user}
            <a href="/account" onclick={closeMenu}
              class="flex items-center gap-2 px-4 py-3 text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 rounded transition-colors">
              <i class="fas fa-user-circle text-red-500"></i>
              Mon compte
            </a>
            <form method="POST" action="/auth/logout">
              <button type="submit" onclick={closeMenu}
                class="w-full text-left px-4 py-3 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition-colors text-base font-medium">
                <i class="fas fa-sign-out-alt mr-2"></i>Déconnexion
              </button>
            </form>
          {:else}
            <a href="/auth/login" onclick={closeMenu}
              class="flex items-center justify-center px-4 py-3 border border-zinc-700 text-zinc-300 rounded-xl transition-all text-base font-medium">
              Se connecter
            </a>
            <a href="/auth/register" onclick={closeMenu}
              class="flex items-center justify-center px-4 py-3 bg-zinc-800 text-zinc-100 rounded-xl transition-all text-base font-medium">
              Créer un compte
            </a>
          {/if}
          <a href="tel:0123456790" onclick={closeMenu}
            class="flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white font-semibold px-4 py-3 rounded transition-colors">
            <i class="fas fa-phone text-sm"></i>
            Urgence 24/7 — 01 23 45 67 90
          </a>
        </div>
      </nav>
    </div>
  {/if}
</header>

<div class="h-16"></div>
