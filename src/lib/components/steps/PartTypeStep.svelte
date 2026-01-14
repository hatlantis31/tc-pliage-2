
<script>
  import { createEventDispatcher } from 'svelte';
  
  export let design;
  
  const dispatch = createEventDispatcher();
  
  // Part type options
  const partTypes = [
    { id: 'rectangle', name: 'Rectangle', icon: 'fa-square' },
    { id: 'lShape', name: 'L-Shape', icon: 'fa-l' },
    { id: 'uShape', name: 'U-Shape', icon: 'fa-u' },
    { id: 'circle', name: 'Circle', icon: 'fa-circle' }
  ];
  
  // Send updated part type to parent
  function selectPartType(partType) {
    dispatch('update', {
      field: 'partType',
      value: partType
    });
  }
</script>

<div class="columns">
  <div class="column is-6">
    <p class="mb-4">Select the basic shape for your metal part:</p>
    
    <div class="buttons are-medium">
      {#each partTypes as type}
        <button 
          class="button is-fullwidth {design.partType === type.id ? 'is-primary' : 'is-light'}"
          on:click={() => selectPartType(type.id)}
        >
          <span class="icon">
            <i class="fas {type.icon}"></i>
          </span>
          <span>{type.name}</span>
        </button>
      {/each}
    </div>
    
    <div class="notification is-info is-light mt-5">
      <p class="has-text-weight-bold">Tip:</p>
      <p>Choose the shape that best matches your needs. You'll be able to specify exact dimensions in the next step.</p>
    </div>
  </div>
  
  <div class="column is-6">
    <div class="box">
      <h3 class="title is-5">Preview</h3>
      
      {#if design.partType}
        <div class="preview-container">
          <div class="tabs is-boxed">
            <ul>
              <li class="is-active"><a>Top View</a></li>
              <li><a>Side View</a></li>
            </ul>
          </div>
          
          <div class="preview-image">
            {#if design.partType === 'rectangle'}
              <svg width="200" height="150" viewBox="0 0 200 150">
                <!-- Top view -->
                <rect x="25" y="25" width="150" height="100" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
              
              <svg width="200" height="150" viewBox="0 0 200 150" class="side-view">
                <!-- Side view -->
                <rect x="25" y="70" width="150" height="10" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
            {:else if design.partType === 'circle'}
              <svg width="200" height="150" viewBox="0 0 200 150">
                <!-- Top view -->
                <circle cx="100" cy="75" r="50" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
              
              <svg width="200" height="150" viewBox="0 0 200 150" class="side-view">
                <!-- Side view -->
                <rect x="50" y="70" width="100" height="10" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
            {:else if design.partType === 'lShape'}
              <svg width="200" height="150" viewBox="0 0 200 150">
                <!-- Top view -->
                <path d="M25,25 L125,25 L125,50 L175,50 L175,125 L25,125 Z" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
              
              <svg width="200" height="150" viewBox="0 0 200 150" class="side-view">
                <!-- Side view -->
                <rect x="25" y="70" width="150" height="10" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
            {:else if design.partType === 'uShape'}
              <svg width="200" height="150" viewBox="0 0 200 150">
                <!-- Top view -->
                <path d="M25,25 L75,25 L75,100 L125,100 L125,25 L175,25 L175,125 L25,125 Z" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
              
              <svg width="200" height="150" viewBox="0 0 200 150" class="side-view">
                <!-- Side view -->
                <path d="M25,70 L25,80 L50,80 L50,70 L150,70 L150,80 L175,80 L175,70 Z" fill="#ccc" stroke="#333" stroke-width="2" />
              </svg>
            {/if}
          </div>
          
          <div class="part-description mt-3">
            {#if design.partType === 'rectangle'}
              <p>A simple rectangular metal plate with customizable width and height.</p>
            {:else if design.partType === 'circle'}
              <p>A circular metal plate with customizable diameter.</p>
            {:else if design.partType === 'lShape'}
              <p>An L-shaped piece with customizable dimensions, ideal for corners and brackets.</p>
            {:else if design.partType === 'uShape'}
              <p>A U-shaped channel with customizable dimensions, suitable for rails and channels.</p>
            {/if}
          </div>
        </div>
      {:else}
        <div class="has-text-centered p-5">
          <p class="has-text-grey">Select a part type to see preview</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .preview-container {
    min-height: 200px;
  }
  
  .preview-image {
    position: relative;
    display: flex;
    justify-content: center;
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f8f8f8;
    padding: 10px;
  }
  
  .side-view {
    display: none;
  }
  
  .tabs:has(li:nth-child(2).is-active) ~ .preview-image .side-view {
    display: block;
  }
  
  .tabs:has(li:nth-child(2).is-active) ~ .preview-image svg:not(.side-view) {
    display: none;
  }
</style>