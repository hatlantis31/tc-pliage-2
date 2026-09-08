<script>
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  let isOpen      = $state(false);
  let userMenu    = $state(false);
  let scrolled    = $state(false);
  let menuRef     = $state(null);

  const links = [
    { href: '/',         label: 'Accueil' },
    { href: '/services', label: 'Services' },
    { href: '/about',    label: 'À Propos' },
    { href: '/designer', label: 'Dessin en ligne' },
    { href: '/contact',  label: 'Contact' },
  ];

  function toggleMenu() { isOpen = !isOpen; document.body.style.overflow = isOpen ? 'hidden' : ''; }
  function closeMenu()  { isOpen = false;  document.body.style.overflow = ''; userMenu = false; }

  function handleClickOutside(e) {
    if (menuRef && !menuRef.contains(e.target)) userMenu = false;
  }

  onMount(() => {
    const onScroll = () => { scrolled = window.scrollY > 40; };
    window.addEventListener('scroll', onScroll);
    document.addEventListener('click', handleClickOutside);
    return () => {
      window.removeEventListener('scroll', onScroll);
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<header
  class="fixed top-0 left-0 right-0 z-50 transition-all duration-300
    {scrolled
      ? 'bg-zinc-950/95 backdrop-blur-md shadow-lg shadow-black/50 border-b border-zinc-800 metal-sheen'
      : 'bg-zinc-950/70 backdrop-blur-sm border-b border-transparent'}"
>
  <!-- Hazard rule under the bar, fades in on scroll -->
  <div class="absolute bottom-0 left-0 right-0 h-px hazard-bar transition-opacity duration-300 {scrolled ? 'opacity-60' : 'opacity-0'}"></div>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">

      <a href="/" onclick={closeMenu} class="flex items-center flex-shrink-0">
        <img src="/logo.jpg" alt="TC Pliage" class="h-10 w-auto object-contain">
      </a>

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

      <!-- Desktop right -->
      <div class="hidden lg:flex items-center gap-2">
        {#if $page.data.user}
          <div class="relative" bind:this={menuRef}>
            <button onclick={(e) => { e.stopPropagation(); userMenu = !userMenu; }}
              class="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-zinc-700 hover:border-zinc-500 bg-zinc-900/50 text-zinc-200 text-sm transition-all">
              <div class="w-6 h-6 rounded-full bg-red-600/20 border border-red-600/30 flex items-center justify-center">
                <span class="text-xs font-semibold text-red-400">{$page.data.user.name.charAt(0).toUpperCase()}</span>
              </div>
              <span class="max-w-[140px] truncate">{$page.data.user.name}</span>
              <i class="fas fa-chevron-down text-[10px] text-zinc-500 transition-transform {userMenu ? 'rotate-180' : ''}"></i>
            </button>

            {#if userMenu}
              <div class="absolute right-0 mt-2 w-64 bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden">
                <div class="px-4 py-3 border-b border-zinc-800 bg-zinc-800/30">
                  <p class="text-sm font-semibold text-zinc-100 truncate">{$page.data.user.name}</p>
                  <p class="text-xs text-zinc-500 truncate">{$page.data.user.email}</p>
                </div>
                <div class="py-1.5">
                  <a href="/account" onclick={() => userMenu = false}
                    class="flex items-center gap-3 px-4 py-2.5 text-sm text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors">
                    <i class="fas fa-user-circle w-4 text-red-400"></i>
                    Mon espace
                  </a>
                  <a href="/designer" onclick={() => userMenu = false}
                    class="flex items-center gap-3 px-4 py-2.5 text-sm text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors">
                    <i class="fas fa-draw-polygon w-4 text-zinc-500"></i>
                    Nouvelle pièce
                  </a>
                  {#if $page.data.user.is_admin}
                    <a href="/admin" onclick={() => userMenu = false}
                      class="flex items-center gap-3 px-4 py-2.5 text-sm text-amber-400 hover:bg-zinc-800/60 transition-colors">
                      <i class="fas fa-shield-halved w-4"></i>
                      Espace admin
                    </a>
                  {/if}
                </div>
                <div class="border-t border-zinc-800 py-1.5">
                  <form method="POST" action="/auth/logout">
                    <button type="submit"
                      class="w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors">
                      <i class="fas fa-sign-out-alt w-4"></i>
                      Se déconnecter
                    </button>
                  </form>
                </div>
              </div>
            {/if}
          </div>
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

        {#if $page.data.user}
          <div class="px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-xl mb-2 flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-red-600/20 border border-red-600/30 flex items-center justify-center flex-shrink-0">
              <span class="text-base font-bold text-red-400">{$page.data.user.name.charAt(0).toUpperCase()}</span>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-semibold text-zinc-100 truncate">{$page.data.user.name}</p>
              <p class="text-xs text-zinc-500 truncate">{$page.data.user.email}</p>
            </div>
          </div>
        {/if}

        {#each links as link}
          <a href={link.href} onclick={closeMenu}
            class="px-4 py-3 text-base font-medium rounded transition-colors
              {$page.url.pathname === link.href
                ? 'text-red-400 bg-red-950/30'
                : 'text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800'}">
            {link.label}
          </a>
        {/each}

        <div class="border-t border-zinc-800 mt-2 pt-3 space-y-1">
          {#if $page.data.user}
            <a href="/account" onclick={closeMenu}
              class="flex items-center gap-3 px-4 py-3 text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 rounded transition-colors">
              <i class="fas fa-user-circle w-4 text-red-400"></i>
              Mon espace
            </a>
            {#if $page.data.user.is_admin}
              <a href="/admin" onclick={closeMenu}
                class="flex items-center gap-3 px-4 py-3 text-amber-400 hover:bg-zinc-800 rounded transition-colors">
                <i class="fas fa-shield-halved w-4"></i>
                Espace admin
              </a>
            {/if}
            <form method="POST" action="/auth/logout">
              <button type="submit" onclick={closeMenu}
                class="w-full text-left flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded transition-colors text-base font-medium">
                <i class="fas fa-sign-out-alt w-4"></i>
                Se déconnecter
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
            Urgence 24/7
          </a>
        </div>
      </nav>
    </div>
  {/if}
</header>

<div class="h-16"></div>
