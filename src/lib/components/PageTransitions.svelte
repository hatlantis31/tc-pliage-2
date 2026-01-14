<!-- PageTransitions.svelte -->
<script>
    import { fly, fade } from 'svelte/transition';
    import { onMount, onDestroy } from 'svelte';
    
    // Current route path
    export let currentPath = '';
    
    // Animation options
    export let duration = 300;
    export let transitionType = 'fade'; // 'fade', 'slide', 'scale', 'custom'
    
    // Preloading progress
    let progress = 0;
    let loading = false;
    let loadingTimeout;
    
    // Keep track of visited paths to enable animations only when changing paths
    let previousPath = '';
    let firstLoad = true;
    
    // Enable/disable animations for path segments
    export let excludedPaths = ['/designer']; // Paths to exclude from animations
    
    // Animation delay for staggered animations
    export let delay = 30;
    
    // Page content ready flag
    let contentReady = false;
    
    // Configure animation base on type
    $: animationProps = getAnimationProps(transitionType);
    
    // Should animate based on paths
    $: shouldAnimate = !firstLoad && 
                      !isExcludedPath(currentPath) && 
                      !isExcludedPath(previousPath) &&
                      currentPath !== previousPath;
    
    function getAnimationProps(type) {
      switch (type) {
        case 'slide':
          return {
            y: 20,
            duration,
            easing: 'easeOut'
          };
        case 'scale':
          return {
            scale: 0.95,
            opacity: 0,
            duration,
            easing: 'easeInOut'
          };
        case 'custom':
          return {
            y: 30,
            x: 10,
            opacity: 0,
            duration,
            easing: 'easeInOutQuad'
          };
        case 'fade':
        default:
          return {
            duration,
            easing: 'easeInOut'
          };
      }
    }
    
    function isExcludedPath(path) {
      return excludedPaths.some(excluded => path.startsWith(excluded));
    }
    
    function simulatePageLoad() {
      // Reset loading state
      progress = 0;
      loading = true;
      contentReady = false;
      
      // Simulate progress increase
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          
          // Short delay before showing content
          loadingTimeout = setTimeout(() => {
            loading = false;
            contentReady = true;
          }, 200);
        }
      }, 50);
      
      return () => {
        clearInterval(interval);
        clearTimeout(loadingTimeout);
      };
    }
    
    onMount(() => {
      // Set initial path
      previousPath = currentPath;
      
      // Simulate initial page load
      const cleanup = simulatePageLoad();
      
      // After first load, disable first load flag
      setTimeout(() => {
        firstLoad = false;
      }, duration + 100);
      
      return cleanup;
    });
    
    // Watch for path changes
    $: if (currentPath !== previousPath && !firstLoad) {
      const cleanup = simulatePageLoad();
      previousPath = currentPath;
      
      return () => cleanup();
    }
    
    onDestroy(() => {
      clearTimeout(loadingTimeout);
    });
  </script>
  
  {#if loading}
    <div class="page-loading" transition:fade={{duration: 200}}>
      <div class="loading-container">
        <div class="logo-container">
          <img src="/logo.jpg" alt="TC Pliage" class="loading-logo" width="120">
        </div>
        <div class="progress-container">
          <div class="progress-bar" style="width: {progress}%"></div>
        </div>
      </div>
    </div>
  {:else if contentReady}
    <!-- Animated container for page transitions -->
    <div 
      class="page-transition-container"
      in:fade={{duration: duration, delay: 100}}
    >
      <!-- Animated content elements -->
      <div 
        class="animate-element primary"
        in:fly={{...animationProps, delay: 100}}
      >
        <slot name="primary"></slot>
      </div>
      
      <div 
        class="animate-element secondary"
        in:fly={{...animationProps, delay: 200}}
      >
        <slot name="secondary"></slot>
      </div>
      
      <div 
        class="animate-element tertiary"
        in:fly={{...animationProps, delay: 300}}
      >
        <slot name="tertiary"></slot>
      </div>
      
      <!-- Default slot for content without specific animation timing -->
      <div 
        class="animate-element default"
        in:fly={{...animationProps, delay: 150}}
      >
        <slot></slot>
      </div>
    </div>
  {/if}
  
  <style>
    .page-loading {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: white;
      z-index: 9999;
    }
    
    .loading-container {
      width: 200px;
      text-align: center;
    }
    
    .logo-container {
      margin-bottom: 1rem;
    }
    
    .loading-logo {
      animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
      0% {
        opacity: 0.6;
      }
      50% {
        opacity: 1;
      }
      100% {
        opacity: 0.6;
      }
    }
    
    .progress-container {
      height: 4px;
      background-color: #f0f0f0;
      border-radius: 2px;
      overflow: hidden;
    }
    
    .progress-bar {
      height: 100%;
      background-color: #E53935;
      transition: width 0.3s ease;
    }
    
    .page-transition-container {
      display: contents;
    }
    
    .animate-element {
      display: contents;
    }
  </style>