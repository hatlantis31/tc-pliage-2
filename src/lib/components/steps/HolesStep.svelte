
<script>
  import { createEventDispatcher } from 'svelte';
  
  export let design;
  
  const dispatch = createEventDispatcher();
  
  // Initialize holes array if not already done
  if (!design.holes) {
    design.holes = [];
  }
  
  // Add a new hole with default values
  function addHole() {
    const defaultX = design.partType === 'circle' 
      ? design.dimensions.diameter / 2 
      : design.dimensions.width / 2;
      
    const defaultY = design.partType === 'circle'
      ? design.dimensions.diameter / 2
      : design.dimensions.height / 2;
    
    const newHole = {
      id: Date.now(),
      x: defaultX,
      y: defaultY,
      diameter: 5
    };
    
    const updatedHoles = [...design.holes, newHole];
    updateHoles(updatedHoles);
  }
  
  // Remove a hole
  function removeHole(holeId) {
    const updatedHoles = design.holes.filter(hole => hole.id !== holeId);
    updateHoles(updatedHoles);
  }
  
  // Update a hole property
  function updateHoleProperty(holeId, property, value) {
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;
    
    const updatedHoles = design.holes.map(hole => {
      if (hole.id === holeId) {
        return { ...hole, [property]: numValue };
      }
      return hole;
    });
    
    updateHoles(updatedHoles);
  }
  
  // Update holes array in parent
  function updateHoles(holes) {
    dispatch('update', {
      field: 'holes',
      value: holes
    });
  }
  
  // Helper function to get dimension value or default
  function getDimension(name, defaultValue = 0) {
    return design.dimensions && design.dimensions[name] !== undefined 
      ? design.dimensions[name] 
      : defaultValue;
  }
  
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
  
  // Check if coordinates are within the part boundaries
  function isPointInBounds(x, y) {
    const padding = 20;
    
    switch (design.partType) {
      case 'rectangle': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        return x >= padding && x <= padding + width && 
               y >= padding && y <= padding + height;
      }
      case 'circle': {
        const radius = getDimension('diameter', 100) / 2;
        const cx = radius + padding;
        const cy = radius + padding;
        const dx = x - cx;
        const dy = y - cy;
        return dx*dx + dy*dy <= radius*radius;
      }
      case 'lShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        const legWidth = getDimension('legWidth', 50);
        
        // Check if in the main rectangle
        if (x >= padding && x <= padding + width && 
            y >= padding && y <= padding + legWidth) {
          return true;
        }
        
        // Check if in the leg
        if (x >= padding && x <= padding + legWidth && 
            y >= padding && y <= padding + height) {
          return true;
        }
        
        return false;
      }
      case 'uShape': {
        const width = getDimension('width', 200);
        const height = getDimension('height', 100);
        const legWidth = getDimension('legWidth', 50);
        const flangeHeight = getDimension('flangeHeight', 30);
        
        // Check if in left leg
        if (x >= padding && x <= padding + legWidth && 
            y >= padding && y <= padding + height) {
          return true;
        }
        
        // Check if in right leg
        if (x >= padding + width - legWidth && x <= padding + width && 
            y >= padding && y <= padding + height) {
          return true;
        }
        
        // Check if in bottom part
        if (x >= padding && x <= padding + width && 
            y >= padding + height - flangeHeight && y <= padding + height) {
          return true;
        }
        
        return false;
      }
      default:
        return false;
    }
  }
  
  // Validate hole position
  function validateHolePosition(hole) {
    // Check if hole is within part boundaries
    if (!isPointInBounds(hole.x + 20, hole.y + 20)) {
      return {
        valid: false,
        message: 'Hole position is outside the part boundaries'
      };
    }
    
    // Check if hole diameter is not too large
    let maxDiameter;
    
    switch (design.partType) {
      case 'rectangle':
        maxDiameter = Math.min(
          getDimension('width', 200), 
          getDimension('height', 100)
        ) * 0.8;
        break;
      case 'lShape':
        maxDiameter = getDimension('legWidth', 50) * 0.8;
        break;
      case 'uShape':
        maxDiameter = Math.min(
          getDimension('legWidth', 50),
          getDimension('flangeHeight', 30)
        ) * 0.8;
        break;
      case 'circle':
        maxDiameter = getDimension('diameter', 100) * 0.8;
        break;
      default:
        maxDiameter = 50;
    }
    
    if (hole.diameter > maxDiameter) {
      return {
        valid: false,
        message: `Hole diameter too large (max: ${maxDiameter.toFixed(1)}mm)`
      };
    }
    
    return { valid: true };
  }
  
  // Track validation errors for holes
  let holeValidation = {};
  
  $: {
    // Update validation whenever holes change
    if (design.holes) {
      holeValidation = {};
      
      design.holes.forEach(hole => {
        const validation = validateHolePosition(hole);
        if (!validation.valid) {
          holeValidation[hole.id] = validation.message;
        }
      });
    }
  }
</script>

<div class="columns">
  <div class="column is-6">
    <div class="is-flex is-justify-content-space-between is-align-items-center mb-4">
      <p>Add holes to your part: <span class="tag is-info ml-2">{design.holes.length} holes</span></p>
      <button class="button is-primary is-small" on:click={addHole}>
        <span class="icon"><i class="fas fa-plus"></i></span>
        <span>Add Hole</span>
      </button>
    </div>
    
    {#if design.holes.length === 0}
      <div class="notification is-light">
        <p>No holes added yet. Click "Add Hole" to add a hole to your part.</p>
        <p class="is-size-7 mt-2">Holes are optional - you can proceed without adding any.</p>
      </div>
    {:else}
      <div class="hole-list">
        {#each design.holes as hole (hole.id)}
          <div class="box mb-3 p-3">
            <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
              <h4 class="title is-6 mb-0">Hole #{design.holes.indexOf(hole) + 1}</h4>
              <button 
                class="button is-danger is-small" 
                on:click={() => removeHole(hole.id)}
              >
                <span class="icon is-small">
                  <i class="fas fa-trash"></i>
                </span>
              </button>
            </div>
            
            <div class="columns is-multiline">
              <div class="column is-4">
                <div class="field">
                  <label class="label is-small">X Position (mm)</label>
                  <div class="control">
                    <input 
                      class="input is-small" 
                      type="number" 
                      min="0" 
                      max="1000" 
                      step="1"
                      value={hole.x}
                      on:input={(e) => updateHoleProperty(hole.id, 'x', e.target.value)}
                    />
                  </div>
                </div>
              </div>
              
              <div class="column is-4">
                <div class="field">
                  <label class="label is-small">Y Position (mm)</label>
                  <div class="control">
                    <input 
                      class="input is-small" 
                      type="number" 
                      min="0" 
                      max="1000" 
                      step="1"
                      value={hole.y}
                      on:input={(e) => updateHoleProperty(hole.id, 'y', e.target.value)}
                    />
                  </div>
                </div>
              </div>
              
              <div class="column is-4">
                <div class="field">
                  <label class="label is-small">Diameter (mm)</label>
                  <div class="control">
                    <input 
                      class="input is-small" 
                      type="number" 
                      min="1" 
                      max="100" 
                      step="0.5"
                      value={hole.diameter}
                      on:input={(e) => updateHoleProperty(hole.id, 'diameter', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {#if holeValidation[hole.id]}
              <p class="help is-danger">{holeValidation[hole.id]}</p>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
    
    <div class="notification is-info is-light mt-4">
      <p class="has-text-weight-bold">Tips:</p>
      <ul>
        <li>Position is measured from the top-left corner of the part</li>
        <li>Standard drill bit sizes: 1mm, 2mm, 3mm, 4mm, 5mm, 6mm, 8mm, 10mm, 12mm</li>
        <li>Hole diameter should be less than the thickness of the material for strength</li>
      </ul>
    </div>
  </div>
  
  <div class="column is-6">
    <div class="box">
      <h3 class="title is-5">Holes Preview</h3>
      
      <div class="preview-image">
        <svg width="100%" height="250" viewBox={getViewBoxDimensions()}>
          <!-- Main shape -->
          <path d={getPartPath()} fill="#ccc" stroke="#333" stroke-width="2" />
          
          <!-- Holes -->
          {#each design.holes as hole (hole.id)}
            <circle 
              cx={hole.x + 20} 
              cy={hole.y + 20} 
              r={hole.diameter / 2}
              fill="white"
              stroke={holeValidation[hole.id] ? "#ff3860" : "#333"}
              stroke-width="2"
            />
            
            <!-- Coordinates label -->
            <text 
              x={hole.x + 20} 
              y={hole.y + 20 - hole.diameter/2 - 5} 
              text-anchor="middle" 
              font-size="8" 
              fill="#666"
            >
              ({hole.x}, {hole.y})
            </text>
            
            <!-- Diameter label -->
            <text 
              x={hole.x + 20} 
              y={hole.y + 20 + hole.diameter/2 + 10} 
              text-anchor="middle" 
              font-size="8" 
              fill="#666"
            >
              Ø{hole.diameter}
            </text>
          {/each}
          
          <!-- Coordinate system indication -->
          <g transform="translate(20, 20)" opacity="0.7">
            <line x1="0" y1="0" x2="20" y2="0" stroke="#666" stroke-width="1" />
            <line x1="0" y1="0" x2="0" y2="20" stroke="#666" stroke-width="1" />
            <polygon points="20,0 16,-3 16,3" fill="#666" />
            <polygon points="0,20 -3,16 3,16" fill="#666" />
            <text x="22" y="3" font-size="8" fill="#666">X</text>
            <text x="3" y="22" font-size="8" fill="#666">Y</text>
            <text x="0" y="-5" font-size="8" fill="#666">(0,0)</text>
          </g>
        </svg>
      </div>
      
      <div class="mt-3">
        <p class="has-text-grey has-text-centered is-size-7">
          <i class="fas fa-info-circle"></i>
          X and Y coordinates are measured from the top-left corner of the part.
        </p>
      </div>
    </div>
    
    <div class="notification is-warning is-light mt-4">
      <p class="has-text-weight-bold">Important:</p>
      <p>Keep holes at least 2x their diameter away from edges to maintain structural integrity. Holes close to edges may weaken the part.</p>
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
  
  .hole-list {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 5px;
  }
</style>