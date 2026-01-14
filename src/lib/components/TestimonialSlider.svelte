<!-- TestimonialSlider.svelte -->
<script>
    import { onMount, onDestroy } from 'svelte';
    
    export let testimonials = [];
    export let autoplaySpeed = 5000; // in milliseconds
    export let showControls = true;
    export let columns = 3; // Number of columns in desktop view
    
    let currentIndex = 0;
    let intervalId;
    let testimonialContainer;
    let isTransitioning = false;
    
    // Calculate number of slides to show based on columns
    $: slidesToShow = Math.min(testimonials.length, columns);
    $: totalSlides = Math.ceil(testimonials.length / slidesToShow);
    
    // Adjust currentIndex to stay within bounds
    $: if (testimonials.length && currentIndex >= totalSlides) {
      currentIndex = 0;
    }
    
    // Get visible testimonials based on current index and slides to show
    $: visibleTestimonials = getVisibleTestimonials(currentIndex, slidesToShow);
    
    function getVisibleTestimonials(index, count) {
      const startIndex = index * count;
      return testimonials.slice(startIndex, startIndex + count);
    }
    
    function nextSlide() {
      if (isTransitioning) return;
      isTransitioning = true;
      
      // Add transition-out class to current items
      if (testimonialContainer) {
        const items = testimonialContainer.querySelectorAll('.testimonial-card');
        items.forEach(item => {
          item.classList.add('transition-out');
        });
        
        // Wait for transition to complete
        setTimeout(() => {
          currentIndex = (currentIndex + 1) % totalSlides;
          
          // Remove transition classes after a brief delay to allow new items to render
          setTimeout(() => {
            const newItems = testimonialContainer.querySelectorAll('.testimonial-card');
            newItems.forEach(item => {
              item.classList.remove('transition-out');
              item.classList.add('transition-in');
            });
            
            // Remove transition-in class after animation completes
            setTimeout(() => {
              newItems.forEach(item => {
                item.classList.remove('transition-in');
              });
              isTransitioning = false;
            }, 500);
          }, 50);
        }, 300);
      }
    }
    
    function prevSlide() {
      if (isTransitioning) return;
      isTransitioning = true;
      
      // Add transition-out class to current items
      if (testimonialContainer) {
        const items = testimonialContainer.querySelectorAll('.testimonial-card');
        items.forEach(item => {
          item.classList.add('transition-out-reverse');
        });
        
        // Wait for transition to complete
        setTimeout(() => {
          currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
          
          // Remove transition classes after a brief delay to allow new items to render
          setTimeout(() => {
            const newItems = testimonialContainer.querySelectorAll('.testimonial-card');
            newItems.forEach(item => {
              item.classList.remove('transition-out-reverse');
              item.classList.add('transition-in-reverse');
            });
            
            // Remove transition-in class after animation completes
            setTimeout(() => {
              newItems.forEach(item => {
                item.classList.remove('transition-in-reverse');
              });
              isTransitioning = false;
            }, 500);
          }, 50);
        }, 300);
      }
    }
    
    function goToSlide(index) {
      if (isTransitioning || index === currentIndex) return;
      
      const direction = index > currentIndex ? 'next' : 'prev';
      
      // Add appropriate transition class
      if (testimonialContainer) {
        const items = testimonialContainer.querySelectorAll('.testimonial-card');
        items.forEach(item => {
          item.classList.add(direction === 'next' ? 'transition-out' : 'transition-out-reverse');
        });
        
        // Wait for transition to complete
        setTimeout(() => {
          currentIndex = index;
          
          // Remove transition classes after a brief delay
          setTimeout(() => {
            const newItems = testimonialContainer.querySelectorAll('.testimonial-card');
            newItems.forEach(item => {
              item.classList.remove('transition-out', 'transition-out-reverse');
              item.classList.add(direction === 'next' ? 'transition-in' : 'transition-in-reverse');
            });
            
            // Remove transition-in class after animation completes
            setTimeout(() => {
              newItems.forEach(item => {
                item.classList.remove('transition-in', 'transition-in-reverse');
              });
              isTransitioning = false;
            }, 500);
          }, 50);
        }, 300);
      }
    }
    
    function startAutoplay() {
      if (testimonials.length <= slidesToShow) return;
      
      intervalId = setInterval(() => {
        nextSlide();
      }, autoplaySpeed);
    }
    
    function pauseAutoplay() {
      if (intervalId) {
        clearInterval(intervalId);
      }
    }
    
    function resumeAutoplay() {
      pauseAutoplay();
      startAutoplay();
    }
    
    onMount(() => {
      if (testimonials.length > slidesToShow) {
        startAutoplay();
      }
    });
    
    onDestroy(() => {
      pauseAutoplay();
    });
  </script>
  
  <div 
    class="testimonial-slider"
    on:mouseenter={pauseAutoplay}
    on:mouseleave={resumeAutoplay}
  >
    {#if showControls && testimonials.length > slidesToShow}
      <button 
        class="slider-control prev-control" 
        on:click={prevSlide}
        aria-label="Témoignage précédent"
      >
        <span class="icon">
          <i class="fas fa-chevron-left"></i>
        </span>
      </button>
      
      <button 
        class="slider-control next-control" 
        on:click={nextSlide}
        aria-label="Témoignage suivant"
      >
        <span class="icon">
          <i class="fas fa-chevron-right"></i>
        </span>
      </button>
    {/if}
    
    <div bind:this={testimonialContainer} class="testimonial-container">
      {#if visibleTestimonials.length === 0}
        <div class="empty-state">
          <p>Aucun témoignage disponible pour le moment.</p>
        </div>
      {:else}
        <div class="columns is-multiline">
          {#each visibleTestimonials as testimonial (testimonial.id || testimonial.name)}
            <div class="column is-{12/slidesToShow}">
              <div class="testimonial-card">
                <div class="testimonial-content">
                  <div class="quote-mark">"</div>
                  <p class="testimonial-text">{testimonial.quote || testimonial.text}</p>
                  <div class="rating">
                    {#each Array(5) as _, i}
                      <span class="icon is-small">
                        <i class={`fas fa-star ${i < (testimonial.rating || 5) ? 'filled' : 'empty'}`}></i>
                      </span>
                    {/each}
                  </div>
                </div>
                <div class="testimonial-author">
                  {#if testimonial.image}
                    <div class="author-image">
                      <img src={testimonial.image} alt={testimonial.name} class="is-rounded">
                    </div>
                  {:else}
                    <div class="author-initials">
                      {testimonial.name.split(' ').map(n => n[0]).join('')}
                    </div>
                  {/if}
                  <div class="author-info">
                    <p class="author-name">{testimonial.name}</p>
                    {#if testimonial.company}
                      <p class="author-title">{testimonial.company}</p>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    
    {#if showControls && testimonials.length > slidesToShow}
      <div class="slider-indicators">
        {#each Array(totalSlides) as _, i}
          <button 
            class="slider-indicator {i === currentIndex ? 'is-active' : ''}" 
            on:click={() => goToSlide(i)}
            aria-label={`Aller au témoignage ${i + 1}`}
          ></button>
        {/each}
      </div>
    {/if}
  </div>
  
  <style>
   
  </style>