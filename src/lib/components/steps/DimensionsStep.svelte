
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  
  export let design;
  
  const dispatch = createEventDispatcher();
  
  // Initialize dimensions based on part type
  onMount(() => {
    if (!design.dimensions || Object.keys(design.dimensions).length === 0) {
      initializeDimensions();
    }
  });
  
  // Default dimensions for each part type
  function initializeDimensions() {
    switch (design.partType) {
      case 'rectangle':
        updateDimension('width', 200);
        updateDimension('height', 100);
        updateDimension('thickness', design.thickness || 2);
        break;
      case 'lShape':
        updateDimension('width', 200);
        updateDimension('height', 100);
        updateDimension('legWidth', 50);
        updateDimension('thickness', design.thickness || 2);
        break;
      case 'uShape':
        updateDimension('width', 200);
        updateDimension('height', 100);
        updateDimension('legWidth', 50);
        updateDimension('flangeHeight', 30);
        updateDimension('thickness', design.thickness || 2);
        break;
      case 'circle':
        updateDimension('diameter', 100);
        updateDimension('thickness', design.thickness || 2);
        break;
    }
  }
  
  // Update dimension in parent
  function updateDimension(name, value) {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;
    
    dispatch('update', {
      field: `dimension.${name}`,
      value: numValue
    });
    
    // If thickness is updated, also update the design.thickness
    if (name === 'thickness') {
      dispatch('update', {
        field: 'thickness',
        value: numValue
      });
    }
  }
  
  // Helper function to get dimension value or default
  function getDimension(name, defaultValue = 0) {
    return design.dimensions && design.dimensions[name] !== undefined 
      ? design.dimensions[name] 
      : defaultValue;
  }
  
  // Helper for creating input fields with consistent styling
  function DimensionInput(name, label, min, max, step = 1, unit = 'mm') {
    return {
      name,
      label,
      min,
      max,
      step,
      unit,
      value: getDimension(name)
    };
  }
  
  // Get relevant dimensions for the current part type
  $: dimensionInputs = (() => {
    switch (design.partType) {
      case 'rectangle':
        return [
          DimensionInput('width', 'Width', 10, 1000),
          DimensionInput('height', 'Height', 10, 1000),
          DimensionInput('thickness', 'Thickness', 0.5, 20, 0.5)
        ];
      case 'lShape':
        return [
          DimensionInput('width', 'Width', 20, 1000),
          DimensionInput('height', 'Height', 20, 1000),
          DimensionInput('legWidth', 'Leg Width', 10, 500),
          DimensionInput('thickness', 'Thickness', 0.5, 20, 0.5)
        ];
      case 'uShape':
        return [
          DimensionInput('width', 'Width', 30, 1000),
          DimensionInput('height', 'Height', 30, 1000),
          DimensionInput('legWidth', 'Leg Width', 10, 200),
          DimensionInput('flangeHeight', 'Flange Height', 10, 200),
          DimensionInput('thickness', 'Thickness', 0.5, 20, 0.5)
        ];
      case 'circle':
        return [
          DimensionInput('diameter', 'Diameter', 10, 1000),
          DimensionInput('thickness', 'Thickness', 0.5, 20, 0.5)
        ];
      default:
        return [];
    }
  })();
  
  // Calculate SVG viewBox dimensions
  function getViewBoxDimensions() {
    const padding = 40;
    
    switch (design.partType) {
      case 'rectangle': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        return `0 0 ${width + padding} ${height + padding}`;
      }
      case 'lShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        return `0 0 ${width + padding} ${height + padding}`;
      }
      case 'uShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        return `0 0 ${width + padding} ${height + padding}`;
      }
      case 'circle': {
        const diameter = getDimension('diameter', 100);
        return `0 0 ${diameter + padding} ${diameter + padding}`;
      }
      default:
        return "0 0 300 200";
    }
  }
  
  // Generate SVG path for the part
  function getPartPath() {
    const padding = 20; // Half of the viewBox padding
    
    switch (design.partType) {
      case 'rectangle': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        return `M ${padding} ${padding} h ${width} v ${height} h -${width} z`;
      }
      case 'lShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        const legWidth = getDimension('legWidth', 50);
        return `M ${padding} ${padding} h ${width} v ${legWidth} h -${width - legWidth} v ${height - legWidth} h -${legWidth} z`;
      }
      case 'uShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        const legWidth = getDimension('legWidth', 50);
        const flangeHeight = getDimension('flangeHeight', 30);
        return `M ${padding} ${padding} h ${legWidth} v ${height - flangeHeight} h ${width - 2 * legWidth} v -${height - flangeHeight} h ${legWidth} v ${height} h -${width} z`;
      }
      case 'circle': {
        const radius = getDimension('diameter', 100) / 2;
        const cx = radius + padding;
        const cy = radius + padding;
        return `M ${cx + radius} ${cy} a ${radius} ${radius} 0 1 0 -${radius * 2} 0 a ${radius} ${radius} 0 1 0 ${radius * 2} 0`;
      }
      default:
        return "";
    }
  }
  
  // Generate side view path
  function getSideViewPath() {
    const padding = 20;
    const halfHeight = 50; // Half height of the SVG view for side view
    const thickness = getDimension('thickness', 2);
    
    switch (design.partType) {
      case 'rectangle': {
        const width = getDimension('width', 200);
        return `M ${padding} ${halfHeight} h ${width} v ${thickness} h -${width} z`;
      }
      case 'lShape': {
        const width = getDimension('width', 200);
        const legWidth = getDimension('legWidth', 50);
        
        // Side view of L-shape depends on orientation
        return `M ${padding} ${halfHeight} h ${width} v ${thickness} h -${width} z`;
      }
      case 'uShape': {
        const width = getDimension('width', 200);
        const legWidth = getDimension('legWidth', 50);
        const flangeHeight = getDimension('flangeHeight', 30);
        
        // U-shape side view (simplified)
        return `
          M ${padding} ${halfHeight} 
          v ${-flangeHeight} h ${thickness} v ${flangeHeight}
          h ${width - 2 * thickness} 
          v ${-flangeHeight} h ${thickness} v ${flangeHeight}
          z
        `;
      }
      case 'circle': {
        const diameter = getDimension('diameter', 100);
        return `M ${padding} ${halfHeight} h ${diameter} v ${thickness} h -${diameter} z`;
      }
      default:
        return "";
    }
  }
  
  // Active view (top or side)
  let activeView = 'top';
</script>

<div class="columns">
  <div class="column is-6">
    <p class="mb-4">Specify the dimensions of your {design.partType} part:</p>
    
    <div class="field is-horizontal" style="align-items: center;">
      <div class="field-label is-normal" style="flex-basis: 120px; flex-grow: 0;">
        <label class="label">Unit</label>
      </div>
      <div class="field-body">
        <div class="field">
          <div class="control">
            <div class="select is-fullwidth">
              <select disabled>
                <option>Millimeters (mm)</option>
                <!-- Could add more units in the future -->
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    {#each dimensionInputs as input}
      <div class="field is-horizontal" style="align-items: center;">
        <div class="field-label is-normal" style="flex-basis: 120px; flex-grow: 0;">
          <label class="label">{input.label}</label>
        </div>
        <div class="field-body">
          <div class="field has-addons">
            <div class="control is-expanded">
              <input 
                class="input" 
                type="number"
                min={input.min}
                max={input.max}
                step={input.step}
                value={input.value}
                on:input={(e) => updateDimension(input.name, e.target.value)}
              />
            </div>
            <div class="control">
              <a class="button is-static">
                {input.unit}
              </a>
            </div>
          </div>
        </div>
      </div>
    {/each}
    
    <div class="notification is-info is-light mt-4">
      <p class="has-text-weight-bold">Tips:</p>
      <ul>
        <li>All dimensions are in millimeters (mm)</li>
        <li>Standard metal sheet thickness: 0.5mm - 3mm</li>
        <li>Toggle between top and side view to see your part from different angles</li>
      </ul>
    </div>
  </div>
  
  <div class="column is-6">
    <div class="box">
      <h3 class="title is-5">Real-time Preview</h3>
      
      <div class="tabs is-boxed">
        <ul>
          <li class={activeView === 'top' ? 'is-active' : ''}>
            <a on:click={() => activeView = 'top'}>Top View</a>
          </li>
          <li class={activeView === 'side' ? 'is-active' : ''}>
            <a on:click={() => activeView = 'side'}>Side View</a>
          </li>
        </ul>
      </div>
      
      <div class="preview-image">
        {#if activeView === 'top'}
          <svg width="100%" height="250" viewBox={getViewBoxDimensions()}>
            <!-- Main shape -->
            <path d={getPartPath()} fill="#ccc" stroke="#333" stroke-width="2" />
            
            <!-- Dimensions - Width -->
            {#if design.partType !== 'circle'}
              <g class="dimension-line">
                <line 
                  x1="20" 
                  y1="10" 
                  x2={20 + getDimension('width', 200)} 
                  y2="10" 
                  stroke="#666" 
                  stroke-width="1" 
                  stroke-dasharray="4,2"
                />
                <line x1="20" y1="8" x2="20" y2="12" stroke="#666" stroke-width="1" />
                <line 
                  x1={20 + getDimension('width', 200)} 
                  y1="8" 
                  x2={20 + getDimension('width', 200)} 
                  y2="12" 
                  stroke="#666" 
                  stroke-width="1" 
                />
                <text 
                  x={20 + getDimension('width', 200)/2} 
                  y="16" 
                  text-anchor="middle" 
                  font-size="10" 
                  fill="#666"
                >
                  {getDimension('width', 200)} mm
                </text>
              </g>
              
              <!-- Dimensions - Height -->
              <g class="dimension-line">
                <line 
                  x1="10" 
                  y1="20" 
                  x2="10" 
                  y2={20 + getDimension('height', 100)} 
                  stroke="#666" 
                  stroke-width="1" 
                  stroke-dasharray="4,2"
                />
                <line x1="8" y1="20" x2="12" y2="20" stroke="#666" stroke-width="1" />
                <line 
                  x1="8" 
                  y1={20 + getDimension('height', 100)} 
                  x2="12" 
                  y2={20 + getDimension('height', 100)} 
                  stroke="#666" 
                  stroke-width="1" 
                />
                <text 
                  x="6" 
                  y={20 + getDimension('height', 100)/2} 
                  text-anchor="middle" 
                  font-size="10" 
                  fill="#666"
                  transform={`rotate(270, 6, ${20 + getDimension('height', 100)/2})`}
                >
                  {getDimension('height', 100)} mm
                </text>
              </g>
            {:else}
              <!-- Dimensions for Circle (Diameter) -->
              <g class="dimension-line">
                <line 
                  x1={20} 
                  y1={20 + getDimension('diameter', 100)/2} 
                  x2={20 + getDimension('diameter', 100)} 
                  y2={20 + getDimension('diameter', 100)/2} 
                  stroke="#666" 
                  stroke-width="1" 
                  stroke-dasharray="4,2"
                />
                <text 
                  x={20 + getDimension('diameter', 100)/2} 
                  y={20 + getDimension('diameter', 100)/2 + 16} 
                  text-anchor="middle" 
                  font-size="10" 
                  fill="#666"
                >
                  Ø {getDimension('diameter', 100)} mm
                </text>
              </g>
            {/if}
            
            <!-- Additional dimensions for L-Shape and U-Shape -->
            {#if design.partType === 'lShape'}
              <g class="dimension-line">
                <line 
                  x1={20 + getDimension('width', 200)} 
                  y1={20 + getDimension('legWidth', 50)/2} 
                  x2={20 + getDimension('width', 200) + 10} 
                  y2={20 + getDimension('legWidth', 50)/2} 
                  stroke="#666" 
                  stroke-width="1" 
                />
                <text 
                  x={20 + getDimension('width', 200) + 15} 
                  y={20 + getDimension('legWidth', 50)/2} 
                  text-anchor="start" 
                  font-size="10" 
                  fill="#666"
                >
                  {getDimension('legWidth', 50)} mm
                </text>
              </g>
            {/if}
            
            {#if design.partType === 'uShape'}
              <g class="dimension-line">
                <line 
                  x1={20 + getDimension('legWidth', 50)/2} 
                  y1={20} 
                  x2={20 + getDimension('legWidth', 50)/2} 
                  y2={20 - 10} 
                  stroke="#666" 
                  stroke-width="1" 
                />
                <text 
                  x={20 + getDimension('legWidth', 50)/2} 
                  y={20 - 15} 
                  text-anchor="middle" 
                  font-size="10" 
                  fill="#666"
                >
                  {getDimension('legWidth', 50)} mm
                </text>
              </g>
              
              <g class="dimension-line">
                <line 
                  x1={20 + getDimension('width', 200) + 10} 
                  y1={20 + getDimension('height', 100) - getDimension('flangeHeight', 30)/2} 
                  x2={20 + getDimension('width', 200) + 20} 
                  y2={20 + getDimension('height', 100) - getDimension('flangeHeight', 30)/2} 
                  stroke="#666" 
                  stroke-width="1" 
                />
                <text 
                  x={20 + getDimension('width', 200) + 25} 
                  y={20 + getDimension('height', 100) - getDimension('flangeHeight', 30)/2} 
                  text-anchor="start" 
                  font-size="10" 
                  fill="#666"
                >
                  {getDimension('flangeHeight', 30)} mm
                </text>
              </g>
            {/if}
            
            <!-- Thickness indicator -->
            <text 
              x="20" 
              y={20 + (design.partType === 'circle' 
                ? getDimension('diameter', 100) 
                : getDimension('height', 100)
              ) + 20} 
              font-size="10" 
              fill="#666"
            >
              Thickness: {getDimension('thickness', 2)} mm
            </text>
          </svg>
        {:else}
          <!-- Side View -->
          <svg width="100%" height="150" viewBox="0 0 280 100">
            <path d={getSideViewPath()} fill="#ccc" stroke="#333" stroke-width="2" />
            
            <!-- Thickness dimension -->
            <line 
              x1={280 - 40} 
              y1={50} 
              x2={280 - 40} 
              y2={50 + getDimension('thickness', 2)} 
              stroke="#666" 
              stroke-width="1" 
              stroke-dasharray="4,2"
            />
            <line 
              x1={280 - 45} 
              y1={50} 
              x2={280 - 35} 
              y2={50} 
              stroke="#666" 
              stroke-width="1"
            />
            <line 
              x1={280 - 45} 
              y1={50 + getDimension('thickness', 2)} 
              x2={280 - 35} 
              y2={50 + getDimension('thickness', 2)} 
              stroke="#666" 
              stroke-width="1"
            />
            <text 
              x={280 - 30} 
              y={50 + getDimension('thickness', 2)/2 + 3} 
              text-anchor="start" 
              font-size="10" 
              fill="#666"
            >
              {getDimension('thickness', 2)} mm
            </text>
          </svg>
        {/if}
      </div>
      
      <div class="material-preview mt-3">
        <p class="has-text-grey has-text-centered">
          <i class="fas fa-info-circle"></i>
          Your part will be milled from solid {design.material || 'metal'} with a thickness of {getDimension('thickness', 2)}mm.
        </p>
      </div>
    </div>
  </div>
</div>

<style>
  .preview-image {
    border: 1px solid #eee;
    border-radius: 4px;
    background-color: #f8f8f8;
    padding: 10px;
    min-height: 250px;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .dimension-line {
    opacity: 0.8;
  }
</style>