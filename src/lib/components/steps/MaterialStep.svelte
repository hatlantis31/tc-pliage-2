<script>
  import { createEventDispatcher } from 'svelte';
  
  export let design;
  
  const dispatch = createEventDispatcher();
  
  // Material options
  const materials = [
    { 
      id: 'steel', 
      name: 'Steel', 
      description: 'Strong and durable, good for structural applications',
      density: 7.85, // g/cm³
      image: '/images/materials/steel.jpg'
    },
    { 
      id: 'aluminum', 
      name: 'Aluminum', 
      description: 'Lightweight and corrosion-resistant',
      density: 2.7, // g/cm³
      image: '/images/materials/aluminum.jpg'
    },
    { 
      id: 'copper', 
      name: 'Copper', 
      description: 'Excellent electrical and thermal conductivity',
      density: 8.96, // g/cm³
      image: '/images/materials/copper.jpg'
    },
    { 
      id: 'brass', 
      name: 'Brass', 
      description: 'Good machinability and corrosion resistance',
      density: 8.4, // g/cm³
      image: '/images/materials/brass.jpg'
    }
  ];
  
  // Finish options
  const finishes = [
    { 
      id: 'none', 
      name: 'No Finish', 
      description: 'Raw metal without any coating or treatment',
      compatibleWith: ['steel', 'aluminum', 'copper', 'brass']
    },
    { 
      id: 'painted', 
      name: 'Painted', 
      description: 'Decorative and protective coating available in various colors',
      compatibleWith: ['steel', 'aluminum']
    },
    { 
      id: 'powder-coated', 
      name: 'Powder Coated', 
      description: 'Durable finish that is more resistant than conventional paint',
      compatibleWith: ['steel', 'aluminum']
    },
    { 
      id: 'galvanized', 
      name: 'Galvanized', 
      description: 'Zinc coating that prevents corrosion',
      compatibleWith: ['steel']
    },
    { 
      id: 'anodized', 
      name: 'Anodized', 
      description: 'Electrochemical process that increases corrosion resistance',
      compatibleWith: ['aluminum']
    },
    { 
      id: 'brushed', 
      name: 'Brushed', 
      description: 'Satin finish with fine lines',
      compatibleWith: ['aluminum', 'copper', 'brass']
    },
    { 
      id: 'polished', 
      name: 'Polished', 
      description: 'Smooth, reflective surface',
      compatibleWith: ['aluminum', 'copper', 'brass']
    }
  ];
  
  // Standard thickness options (in mm)
  const thicknessOptions = [
    0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0
  ];
  
  // Color options for painted and powder-coated finishes
  const colorOptions = [
    { id: 'black', name: 'Black', hex: '#000000' },
    { id: 'white', name: 'White', hex: '#FFFFFF' },
    { id: 'red', name: 'Red', hex: '#FF0000' },
    { id: 'blue', name: 'Blue', hex: '#0000FF' },
    { id: 'green', name: 'Green', hex: '#008000' },
    { id: 'yellow', name: 'Yellow', hex: '#FFFF00' },
    { id: 'orange', name: 'Orange', hex: '#FFA500' },
    { id: 'purple', name: 'Purple', hex: '#800080' },
    { id: 'grey', name: 'Grey', hex: '#808080' },
    { id: 'silver', name: 'Silver', hex: '#C0C0C0' },
    { id: 'custom', name: 'Custom Color', hex: '#CCCCCC' }
  ];
  
  // Filter finishes based on selected material
  $: availableFinishes = finishes.filter(finish => 
    finish.compatibleWith.includes(design.material)
  );
  
  // Check if color selection is needed
  $: needsColorSelection = design.finish === 'painted' || design.finish === 'powder-coated';
  
  // Update material in parent
  function selectMaterial(materialId) {
    dispatch('update', {
      field: 'material',
      value: materialId
    });
    
    // If current finish is not compatible with new material, reset it
    const currentFinish = design.finish;
    if (currentFinish) {
      const isCompatible = finishes.find(
        f => f.id === currentFinish && f.compatibleWith.includes(materialId)
      );
      
      if (!isCompatible) {
        dispatch('update', {
          field: 'finish',
          value: 'none'
        });
      }
    }
  }
  
  // Update thickness in parent
  function updateThickness(value) {
    const thickness = parseFloat(value);
    if (isNaN(thickness)) return;
    
    dispatch('update', {
      field: 'thickness',
      value: thickness
    });
    
    // Also update in dimensions
    dispatch('update', {
      field: 'dimension.thickness',
      value: thickness
    });
  }
  
  // Update finish in parent
  function selectFinish(finishId) {
    dispatch('update', {
      field: 'finish',
      value: finishId
    });
    
    // Reset color if finish doesn't need color
    if (finishId !== 'painted' && finishId !== 'powder-coated') {
      dispatch('update', {
        field: 'finishColor',
        value: '#000000'
      });
    }
  }
  
  // Update finish color in parent
  function updateFinishColor(color) {
    dispatch('update', {
      field: 'finishColor',
      value: color
    });
  }
  
  // Find material object from id
  $: selectedMaterial = materials.find(m => m.id === design.material) || materials[0];
  
  // Find finish object from id
  $: selectedFinish = finishes.find(f => f.id === design.finish) || finishes[0];
  
  // Calculate approximate weight
  $: weight = calculateWeight();
  
  function calculateWeight() {
    if (!design.dimensions || !design.material) return 0;
    
    const material = materials.find(m => m.id === design.material);
    if (!material) return 0;
    
    const density = material.density; // g/cm³
    const thicknessInCm = design.thickness / 10;
    let volume = 0; // in cm³
    
    switch (design.partType) {
      case 'rectangle': {
        const width = design.dimensions.width / 10; // mm to cm
        const height = design.dimensions.height / 10; // mm to cm
        volume = width * height * thicknessInCm;
        break;
      }
      case 'lShape': {
        const width = design.dimensions.width / 10;
        const height = design.dimensions.height / 10;
        const legWidth = design.dimensions.legWidth / 10;
        
        // L-shape area = full rectangle - missing rectangle
        const area = (width * height) - ((width - legWidth) * (height - legWidth));
        volume = area * thicknessInCm;
        break;
      }
      case 'uShape': {
        const width = design.dimensions.width / 10;
        const height = design.dimensions.height / 10;
        const legWidth = design.dimensions.legWidth / 10;
        const flangeHeight = design.dimensions.flangeHeight / 10;
        
        // U-shape has two vertical legs and a horizontal connection
        const leftLeg = legWidth * height;
        const rightLeg = legWidth * height;
        const bottom = (width - (2 * legWidth)) * flangeHeight;
        
        volume = (leftLeg + rightLeg + bottom) * thicknessInCm;
        break;
      }
      case 'circle': {
        const radius = design.dimensions.diameter / 20; // diameter/2 in cm
        volume = Math.PI * radius * radius * thicknessInCm;
        break;
      }
      default:
        return 0;
    }
    
    // Subtract volume of holes
    if (design.holes && design.holes.length > 0) {
      design.holes.forEach(hole => {
        const holeRadius = hole.diameter / 20; // diameter/2 in cm
        const holeVolume = Math.PI * holeRadius * holeRadius * thicknessInCm;
        volume -= holeVolume;
      });
    }
    
    // Calculate weight in grams
    return volume * density;
  }
</script>

<div class="columns">
  <div class="column is-6">
    <div class="mb-5">
      <h3 class="title is-5 mb-3">Material Selection</h3>
      
      <div class="field">
        <div class="control">
          {#each materials as material}
            <label class="radio material-option box mb-3 p-3 {material.id === design.material ? 'is-selected' : ''}">
              <input 
                type="radio" 
                name="material" 
                value={material.id}
                checked={material.id === design.material}
                on:change={() => selectMaterial(material.id)}
              />
              <div class="is-flex">
                <figure class="image is-64x64 mr-3">
                  <div class="material-image {material.id}"></div>
                </figure>
                <div>
                  <p class="is-size-5 has-text-weight-bold">{material.name}</p>
                  <p class="is-size-7">{material.description}</p>
                </div>
              </div>
            </label>
          {/each}
        </div>
      </div>
    </div>
    
    <div class="mb-5">
      <h3 class="title is-5 mb-3">Thickness</h3>
      
      <div class="field has-addons">
        <div class="control is-expanded">
          <input 
            class="input" 
            type="number" 
            min="0.5" 
            max="20" 
            step="0.1"
            value={design.thickness}
            on:input={(e) => updateThickness(e.target.value)}
          />
        </div>
        <div class="control">
          <a class="button is-static">mm</a>
        </div>
      </div>
      
      <div class="field mt-2">
        <label class="label is-small">Standard thicknesses:</label>
        <div class="buttons are-small">
          {#each thicknessOptions as thickness}
            <button 
              class="button {design.thickness === thickness ? 'is-primary' : 'is-light'}"
              on:click={() => updateThickness(thickness)}
            >
              {thickness} mm
            </button>
          {/each}
        </div>
      </div>
    </div>
  </div>
  
  <div class="column is-6">
    <div class="mb-5">
      <h3 class="title is-5 mb-3">Surface Finish</h3>
      
      <div class="field">
        <div class="control">
          {#each availableFinishes as finish}
            <label class="radio finish-option box mb-3 p-3 {finish.id === design.finish ? 'is-selected' : ''}">
              <input 
                type="radio" 
                name="finish" 
                value={finish.id}
                checked={finish.id === design.finish}
                on:change={() => selectFinish(finish.id)}
              />
              <div>
                <p class="is-size-5 has-text-weight-bold">{finish.name}</p>
                <p class="is-size-7">{finish.description}</p>
              </div>
            </label>
          {/each}
        </div>
      </div>
    </div>
    
    {#if needsColorSelection}
      <div class="mb-5">
        <h3 class="title is-5 mb-3">Color Selection</h3>
        
        <div class="field">
          <div class="control">
            <div class="color-grid">
              {#each colorOptions.filter(c => c.id !== 'custom') as color}
                <div 
                  class="color-option {color.hex === design.finishColor ? 'is-selected' : ''}"
                  style="background-color: {color.hex};"
                  on:click={() => updateFinishColor(color.hex)}
                >
                  <span class="color-name">{color.name}</span>
                </div>
              {/each}
              
              <!-- Custom color option -->
              <div class="color-option custom">
                <input 
                  type="color" 
                  value={design.finishColor}
                  on:input={(e) => updateFinishColor(e.target.value)}
                />
                <span class="color-name">Custom</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
    
    <div class="box">
      <h3 class="title is-5">Material Summary</h3>
      
      <table class="table is-fullwidth">
        <tbody>
          <tr>
            <th>Material</th>
            <td>{selectedMaterial.name}</td>
          </tr>
          <tr>
            <th>Thickness</th>
            <td>{design.thickness} mm</td>
          </tr>
          <tr>
            <th>Finish</th>
            <td>{selectedFinish.name}</td>
          </tr>
          {#if needsColorSelection}
            <tr>
              <th>Color</th>
              <td>
                <div class="is-flex is-align-items-center">
                  <div 
                    class="color-swatch mr-2"
                    style="background-color: {design.finishColor};"
                  ></div>
                  <span>{design.finishColor}</span>
                </div>
              </td>
            </tr>
          {/if}
          <tr>
            <th>Estimated Weight</th>
            <td>
              {#if weight < 1000}
                {weight.toFixed(1)} g
              {:else}
                {(weight / 1000).toFixed(2)} kg
              {/if}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<style>
  .material-option,
  .finish-option {
    cursor: pointer;
    transition: all 0.2s;
    display: block;
    width: 100%;
  }
  
  .material-option:hover,
  .finish-option:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  .material-option.is-selected,
  .finish-option.is-selected {
    border: 2px solid #3273dc;
    background-color: #f0f5ff;
  }
  
  .material-image {
    width: 100%;
    height: 100%;
    border-radius: 4px;
    background-size: cover;
    background-position: center;
  }
  
  .material-image.steel {
    background-color: #708090;
  }
  
  .material-image.aluminum {
    background-color: #E8E8E8;
  }
  
  .material-image.copper {
    background-color: #B87333;
  }
  
  .material-image.brass {
    background-color: #D4AF37;
  }
  
  .color-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }
  
  .color-option {
    position: relative;
    width: 100%;
    padding-top: 100%; /* 1:1 aspect ratio */
    border-radius: 4px;
    cursor: pointer;
    overflow: hidden;
    transition: transform 0.2s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .color-option:hover {
    transform: scale(1.05);
  }
  
  .color-option.is-selected {
    box-shadow: 0 0 0 3px #3273dc;
  }
  
  .color-name {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 2px 0;
    font-size: 10px;
    text-align: center;
    background-color: rgba(0, 0, 0, 0.5);
    color: white;
  }
  
  .color-option.custom input[type="color"] {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 0;
    border: none;
    cursor: pointer;
  }
  
  .color-swatch {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
</style>