<!-- ProjectGallery.svelte -->
<script>
    import { onMount } from 'svelte';
    
    export let projects = [];
    export let columns = 3; // Number of columns on desktop
    export let showFilters = true;
    export let categories = ['Tous', 'Urgence', 'Couvertines', 'Habillages', 'Quincaillerie', 'Sur Mesure'];
    
    let selectedCategory = 'Tous';
    let galleryElement;
    let lightboxActive = false;
    let currentProject = null;
    let touchStartX = 0;
    let touchEndX = 0;
    
    // Filter projects by selected category
    $: filteredProjects = selectedCategory === 'Tous'
      ? projects
      : projects.filter(project => project.category === selectedCategory);
    
    // Responsive columns
    $: columnClass = {
      desktop: `is-${12 / columns}`,
      tablet: `is-${columns <= 2 ? 12 / columns : 6}`
    };
    
    // Apply masonry layout when projects change
    $: if (filteredProjects && galleryElement) {
      setTimeout(applyMasonryLayout, 100);
    }
    
    function applyMasonryLayout() {
      if (!galleryElement) return;
      
      const items = galleryElement.querySelectorAll('.gallery-item');
      if (items.length === 0) return;
      
      // Reset heights
      items.forEach(item => {
        item.style.height = 'auto';
      });
      
      // Apply masonry only on desktop
      if (window.innerWidth >= 1024) {
        // Get items per row based on columns
        const itemsPerRow = columns;
        
        for (let i = 0; i < items.length; i += itemsPerRow) {
          // Get max height for this row
          let maxHeight = 0;
          for (let j = i; j < i + itemsPerRow && j < items.length; j++) {
            const height = items[j].offsetHeight;
            if (height > maxHeight) {
              maxHeight = height;
            }
          }
          
          // Set all items in this row to max height
          for (let j = i; j < i + itemsPerRow && j < items.length; j++) {
            items[j].style.height = `${maxHeight}px`;
          }
        }
      }
    }
    
    function setCategory(category) {
      selectedCategory = category;
    }
    
    function openLightbox(project) {
      currentProject = project;
      lightboxActive = true;
      document.body.style.overflow = 'hidden';
    }
    
    function closeLightbox() {
      lightboxActive = false;
      document.body.style.overflow = '';
    }
    
    function nextProject() {
      if (!currentProject) return;
      
      const currentIndex = filteredProjects.findIndex(p => p.id === currentProject.id);
      if (currentIndex >= 0 && currentIndex < filteredProjects.length - 1) {
        currentProject = filteredProjects[currentIndex + 1];
      } else {
        currentProject = filteredProjects[0];
      }
    }
    
    function prevProject() {
      if (!currentProject) return;
      
      const currentIndex = filteredProjects.findIndex(p => p.id === currentProject.id);
      if (currentIndex > 0) {
        currentProject = filteredProjects[currentIndex - 1];
      } else {
        currentProject = filteredProjects[filteredProjects.length - 1];
      }
    }
    
    function handleKeydown(event) {
      if (!lightboxActive) return;
      
      if (event.key === 'Escape') {
        closeLightbox();
      } else if (event.key === 'ArrowRight') {
        nextProject();
      } else if (event.key === 'ArrowLeft') {
        prevProject();
      }
    }
    
    function handleTouchStart(event) {
      touchStartX = event.touches[0].clientX;
    }
    
    function handleTouchMove(event) {
      touchEndX = event.touches[0].clientX;
    }
    
    function handleTouchEnd() {
      if (!lightboxActive) return;
      
      const threshold = 50;
      const deltaX = touchEndX - touchStartX;
      
      if (deltaX > threshold) {
        prevProject();
      } else if (deltaX < -threshold) {
        nextProject();
      }
    }
    
    onMount(() => {
      window.addEventListener('keydown', handleKeydown);
      window.addEventListener('resize', applyMasonryLayout);
      
      // Apply initial masonry layout
      setTimeout(applyMasonryLayout, 300);
      
      return () => {
        window.removeEventListener('keydown', handleKeydown);
        window.removeEventListener('resize', applyMasonryLayout);
      };
    });
  </script>
  
  <svelte:window 
    on:touchstart={handleTouchStart}
    on:touchmove={handleTouchMove}
    on:touchend={handleTouchEnd}
  />
  
  <div class="project-gallery">
    {#if showFilters && categories.length > 0}
      <div class="filter-container">
        <div class="tabs">
          <ul>
            {#each categories as category}
              <li class={category === selectedCategory ? 'is-active' : ''}>
                <a 
                  href="#{category.toLowerCase()}" 
                  on:click|preventDefault={() => setCategory(category)}
                >
                  {category}
                </a>
              </li>
            {/each}
          </ul>
        </div>
      </div>
    {/if}
    
    <div class="gallery-container" bind:this={galleryElement}>
      {#if filteredProjects.length === 0}
        <div class="empty-gallery">
          <p>Aucun projet trouvé dans cette catégorie.</p>
          {#if selectedCategory !== 'Tous'}
            <button class="button is-primary mt-3" on:click={() => setCategory('Tous')}>
              Voir tous les projets
            </button>
          {/if}
        </div>
      {:else}
        <div class="columns is-multiline">
          {#each filteredProjects as project (project.id)}
            <div class="column {columnClass.desktop}-desktop is-6-tablet">
              <div class="gallery-item">
                <div 
                  class="project-card" 
                  on:click={() => openLightbox(project)}
                  on:keypress={(e) => e.key === 'Enter' && openLightbox(project)}
                  role="button"
                  tabindex="0"
                >
                  <div class="project-image-container">
                    <img 
                      src={project.image} 
                      alt={project.title} 
                      loading="lazy"
                      onError={(e) => e.target.src = 'https://via.placeholder.com/600x400?text=TC+PLIAGE'}
                    >
                    <div class="project-overlay">
                      <span class="view-project">
                        <span class="icon">
                          <i class="fas fa-search-plus"></i>
                        </span>
                        <span>Voir le projet</span>
                      </span>
                    </div>
                  </div>
                  <div class="project-info">
                    <h3 class="project-title">{project.title}</h3>
                    {#if project.category}
                      <span class="project-category">{project.category}</span>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Lightbox -->
  {#if lightboxActive && currentProject}
    <div class="lightbox" on:click|self={closeLightbox}>
      <button class="lightbox-close" on:click={closeLightbox}>
        <span class="icon">
          <i class="fas fa-times"></i>
        </span>
      </button>
      
      <div class="lightbox-content">
        <div class="lightbox-image-container">
          <img 
            src={currentProject.largeImage || currentProject.image} 
            alt={currentProject.title}
            on:click|stopPropagation
          >
        </div>
        
        <div class="lightbox-info" on:click|stopPropagation>
          <h3 class="lightbox-title">{currentProject.title}</h3>
          {#if currentProject.category}
            <span class="lightbox-category">{currentProject.category}</span>
          {/if}
          {#if currentProject.description}
            <p class="lightbox-description">{currentProject.description}</p>
          {/if}
          {#if currentProject.client}
            <p class="lightbox-client">
              <strong>Client:</strong> {currentProject.client}
            </p>
          {/if}
          {#if currentProject.date}
            <p class="lightbox-date">
              <strong>Date:</strong> {currentProject.date}
            </p>
          {/if}
        </div>
      </div>
      
      <div class="lightbox-controls">
        <button class="lightbox-control prev-control" on:click|stopPropagation={prevProject}>
          <span class="icon">
            <i class="fas fa-chevron-left"></i>
          </span>
        </button>
        <button class="lightbox-control next-control" on:click|stopPropagation={nextProject}>
          <span class="icon">
            <i class="fas fa-chevron-right"></i>
          </span>
        </button>
      </div>
    </div>
  {/if}
  
  <style>

  </style>