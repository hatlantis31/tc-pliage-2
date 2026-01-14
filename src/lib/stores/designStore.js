// src/lib/stores/designStore.js
import { writable } from 'svelte/store';
import { v4 as uuidv4 } from 'uuid';

/**
 * Creates an initial design state
 * @returns {Object} The initial design state
 */
function createInitialDesign() {
  return {
    id: uuidv4(),
    partType: null,
    dimensions: {},
    holes: [],
    material: 'steel',
    thickness: 2,
    finish: 'none',
    finishColor: '#000000',
    timestamp: new Date().toISOString()
  };
}

/**
 * Creates a design store with methods for updating and managing design state
 */
function createDesignStore() {
  const { subscribe, set, update } = writable(createInitialDesign());

  return {
    subscribe,
    
    /**
     * Update a specific field in the design
     * @param {string} field - The field to update
     * @param {any} value - The new value
     */
    updateField: (field, value) => {
      update(design => {
        // Handle special case for dimension updates
        if (field.startsWith('dimension.')) {
          const dimensionName = field.split('.')[1];
          design.dimensions = {
            ...design.dimensions,
            [dimensionName]: value
          };
          
          // When updating thickness dimension, also update the main thickness field
          if (dimensionName === 'thickness') {
            design.thickness = value;
          }
          
          return { ...design };
        }
        
        // Handle special case for updating part type
        if (field === 'partType') {
          return {
            ...design,
            partType: value,
            dimensions: {} // Reset dimensions when part type changes
          };
        }
        
        // Default handling for other fields
        return {
          ...design,
          [field]: value
        };
      });
    },
    
    /**
     * Add a hole to the design
     * @param {Object} hole - The hole to add
     */
    addHole: (hole) => {
      update(design => ({
        ...design,
        holes: [...design.holes, {
          id: hole.id || Date.now(),
          ...hole
        }]
      }));
    },
    
    /**
     * Update an existing hole
     * @param {string|number} holeId - The ID of the hole to update
     * @param {Object} updates - The properties to update
     */
    updateHole: (holeId, updates) => {
      update(design => {
        const updatedHoles = design.holes.map(hole => {
          if (hole.id === holeId) {
            return { ...hole, ...updates };
          }
          return hole;
        });
        
        return {
          ...design,
          holes: updatedHoles
        };
      });
    },
    
    /**
     * Remove a hole
     * @param {string|number} holeId - The ID of the hole to remove
     */
    removeHole: (holeId) => {
      update(design => ({
        ...design,
        holes: design.holes.filter(hole => hole.id !== holeId)
      }));
    },
    
    /**
     * Reset the design to initial state
     */
    reset: () => {
      set(createInitialDesign());
    },
    
    /**
     * Load a design from JSON
     * @param {Object} designData - The design data to load
     */
    loadDesign: (designData) => {
      // Ensure required fields
      const design = {
        ...createInitialDesign(),
        ...designData,
        timestamp: new Date().toISOString() // Update timestamp
      };
      
      set(design);
    },
    
    /**
     * Export the current design as JSON
     * @returns {string} The design as a JSON string
     */
    exportDesign: () => {
      let design;
      subscribe(value => {
        design = value;
      })();
      
      return JSON.stringify(design, null, 2);
    }
  };
}

// Create and export the store
export const designStore = createDesignStore();