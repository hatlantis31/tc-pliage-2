<script>
  const year = new Date().getFullYear();

  const navLinks = ['/', '/services', '/about', '/designer', '/contact'];
  const navLabels = ['Accueil', 'Services', 'À Propos', 'Dessin en ligne', 'Contact'];
</script>

<footer class="bg-zinc-900 border-t border-zinc-800 mt-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">

      <!-- Brand -->
      <div class="lg:col-span-2">
        <a href="/">
          <img src="/logo.jpg" alt="TC Pliage" class="h-10 w-auto mb-4 brightness-0 invert opacity-70">
        </a>
        <p class="text-zinc-400 text-sm leading-relaxed max-w-xs">
          Votre partenaire en fabrication métallique depuis 2016. Réactivité, qualité et précision au service de vos projets.
        </p>
        <div class="flex gap-3 mt-5">
          {#each [['fab fa-facebook-f', 'Facebook'], ['fab fa-linkedin-in', 'LinkedIn'], ['fab fa-instagram', 'Instagram']] as [icon, label]}
            <span
              role="link"
              tabindex="0"
              class="w-9 h-9 rounded-full bg-zinc-800 hover:bg-red-600 flex items-center justify-center text-zinc-400 hover:text-white transition-colors cursor-pointer"
              aria-label={label}
            >
              <i class="{icon} text-sm"></i>
            </span>
          {/each}
        </div>
      </div>

      <!-- Navigation -->
      <div>
        <h3 class="text-zinc-100 font-semibold text-sm uppercase tracking-wider mb-4">Navigation</h3>
        <ul class="space-y-2">
          {#each navLinks as href, i}
            <li>
              <a {href} class="text-zinc-400 hover:text-zinc-100 text-sm transition-colors">
                {navLabels[i]}
              </a>
            </li>
          {/each}
        </ul>
      </div>

      <!-- Contact -->
      <div>
        <h3 class="text-zinc-100 font-semibold text-sm uppercase tracking-wider mb-4">Contact</h3>
        <ul class="space-y-3 text-sm">
          <li class="flex gap-3 text-zinc-400">
            <i class="fas fa-map-marker-alt text-red-600 mt-0.5 flex-shrink-0"></i>
            <span>3 Avenue du Bois Vert,<br>Portet-Sur-Garonne</span>
          </li>
          <li class="flex gap-3 text-zinc-400">
            <i class="fas fa-phone text-red-600 mt-0.5 flex-shrink-0"></i>
            <div>
              <a href="tel:0123456789" class="hover:text-zinc-100 transition-colors block">01 23 45 67 89</a>
              <a href="tel:0123456790" class="hover:text-red-400 text-red-500 font-medium transition-colors block">
                01 23 45 67 90 (urgences)
              </a>
            </div>
          </li>
          <li class="flex gap-3 text-zinc-400">
            <i class="fas fa-envelope text-red-600 mt-0.5 flex-shrink-0"></i>
            <a href="mailto:contact@tcpliage.fr" class="hover:text-zinc-100 transition-colors">
              contact@tcpliage.fr
            </a>
          </li>
        </ul>
      </div>
    </div>

    <div class="border-t border-zinc-800 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4">
      <p class="text-zinc-500 text-sm">© {year} TC PLIAGE. Tous droits réservés.</p>
      <div class="flex gap-4 text-sm">
        <span class="text-zinc-500">Mentions Légales</span>
        <span class="text-zinc-700">|</span>
        <span class="text-zinc-500">Confidentialité</span>
      </div>
    </div>
  </div>
</footer>
