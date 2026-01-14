// src/lib/utils/validationUtils.js

/**
 * Validates the entire metal part design
 * 
 * @param {Object} design - The complete design object
 * @returns {Object} - Validation result with isValid flag and any error messages
 */
export function validateDesign(design) {
    const errors = {};
    
    // Check for required fields
    if (!design.partType) {
      errors.partType = 'Part type is required';
    }
    
    if (!design.material) {
      errors.material = 'Material is required';
    }
    
    if (!design.thickness || design.thickness <= 0) {
      errors.thickness = 'Valid thickness is required';
    }
    
    // Validate dimensions based on part type
    if (design.partType && (!design.dimensions || Object.keys(design.dimensions).length === 0)) {
      errors.dimensions = 'Dimensions are required';
    } else if (design.dimensions) {
      const dimensionErrors = validateDimensions(design.partType, design.dimensions, design.thickness);
      if (Object.keys(dimensionErrors).length > 0) {
        errors.dimensions = dimensionErrors;
      }
    }
    
    // Validate holes
    if (design.holes && design.holes.length > 0) {
      const holeErrors = {};
      
      design.holes.forEach((hole, index) => {
        const holeValidation = validateHole(hole, design);
        if (!holeValidation.isValid) {
          holeErrors[index] = holeValidation.errors;
        }
      });
      
      if (Object.keys(holeErrors).length > 0) {
        errors.holes = holeErrors;
      }
    }
    
    // Check material and finish compatibility
    if (design.material && design.finish) {
      const isCompatible = checkFinishCompatibility(design.material, design.finish);
      if (!isCompatible) {
        errors.finish = `${design.finish} finish is not compatible with ${design.material}`;
      }
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }
  
  /**
   * Validates dimensions for a specific part type
   * 
   * @param {string} partType - The type of part
   * @param {Object} dimensions - The dimensions object
   * @param {number} thickness - The part thickness
   * @returns {Object} - Any dimension errors
   */
  function validateDimensions(partType, dimensions, thickness) {
    const errors = {};
    
    // General constraints
    const minSize = 10; // Minimum size in mm for any dimension
    const maxSize = 1000; // Maximum size in mm for any dimension
    
    switch (partType) {
      case 'rectangle':
        // Validate width
        if (!dimensions.width) {
          errors.width = 'Width is required';
        } else if (dimensions.width < minSize || dimensions.width > maxSize) {
          errors.width = `Width must be between ${minSize} and ${maxSize} mm`;
        }
        
        // Validate height
        if (!dimensions.height) {
          errors.height = 'Height is required';
        } else if (dimensions.height < minSize || dimensions.height > maxSize) {
          errors.height = `Height must be between ${minSize} and ${maxSize} mm`;
        }
        break;
        
      case 'lShape':
        // Validate width
        if (!dimensions.width) {
          errors.width = 'Width is required';
        } else if (dimensions.width < minSize || dimensions.width > maxSize) {
          errors.width = `Width must be between ${minSize} and ${maxSize} mm`;
        }
        
        // Validate height
        if (!dimensions.height) {
          errors.height = 'Height is required';
        } else if (dimensions.height < minSize || dimensions.height > maxSize) {
          errors.height = `Height must be between ${minSize} and ${maxSize} mm`;
        }
        
        // Validate leg width
        if (!dimensions.legWidth) {
          errors.legWidth = 'Leg width is required';
        } else if (dimensions.legWidth < minSize || dimensions.legWidth > Math.min(dimensions.width, dimensions.height)) {
          errors.legWidth = `Leg width must be between ${minSize} mm and the minimum of width/height`;
        }
        break;
        
      case 'uShape':
        // Validate width
        if (!dimensions.width) {
          errors.width = 'Width is required';
        } else if (dimensions.width < minSize || dimensions.width > maxSize) {
          errors.width = `Width must be between ${minSize} and ${maxSize} mm`;
        }
        
        // Validate height
        if (!dimensions.height) {
          errors.height = 'Height is required';
        } else if (dimensions.height < minSize || dimensions.height > maxSize) {
          errors.height = `Height must be between ${minSize} and ${maxSize} mm`;
        }
        
        // Validate leg width
        if (!dimensions.legWidth) {
          errors.legWidth = 'Leg width is required';
        } else if (dimensions.legWidth < minSize || dimensions.legWidth > dimensions.width / 2) {
          errors.legWidth = `Leg width must be between ${minSize} mm and half of the width`;
        }
        
        // Validate flange height
        if (!dimensions.flangeHeight) {
          errors.flangeHeight = 'Flange height is required';
        } else if (dimensions.flangeHeight < minSize || dimensions.flangeHeight > dimensions.height) {
          errors.flangeHeight = `Flange height must be between ${minSize} mm and the height`;
        }
        break;
        
      case 'circle':
        // Validate diameter
        if (!dimensions.diameter) {
          errors.diameter = 'Diameter is required';
        } else if (dimensions.diameter < minSize || dimensions.diameter > maxSize) {
          errors.diameter = `Diameter must be between ${minSize} and ${maxSize} mm`;
        }
        break;
    }
    
    return errors;
  }
  
  /**
   * Validates a hole configuration
   * 
   * @param {Object} hole - The hole object with x, y, and diameter
   * @param {Object} design - The complete design object for context
   * @returns {Object} - Validation result with isValid flag and any error messages
   */
  function validateHole(hole, design) {
    const errors = {};
    
    // Check for required properties
    if (hole.x === undefined || hole.x === null) {
      errors.x = 'X position is required';
    }
    
    if (hole.y === undefined || hole.y === null) {
      errors.y = 'Y position is required';
    }
    
    if (!hole.diameter) {
      errors.diameter = 'Diameter is required';
    } else if (hole.diameter <= 0) {
      errors.diameter = 'Diameter must be positive';
    } else if (hole.diameter > design.thickness * 5) {
      errors.diameter = `Diameter should not exceed 5x the material thickness (${design.thickness * 5} mm) for structural integrity`;
    }
    
    // Check if hole is within the bounds of the part
    if (hole.x !== undefined && hole.y !== undefined && hole.diameter && design.dimensions) {
      const isInBounds = checkHoleInBounds(hole, design);
      if (!isInBounds) {
        errors.position = 'Hole position is outside the part boundaries';
      }
    }
    
    // Check minimum distance between holes (2x diameter)
    if (hole.diameter && design.holes) {
      const minDistanceViolation = checkHoleMinimumDistance(hole, design.holes);
      if (minDistanceViolation) {
        errors.proximity = `Hole is too close to hole #${minDistanceViolation}. Minimum distance should be at least 2x the larger diameter.`;
      }
    }
    
    return {
      isValid: Object.keys(errors).length === 0,
      errors
    };
  }
  
  /**
   * Checks if a hole is within the boundaries of the part
   * 
   * @param {Object} hole - The hole to check
   * @param {Object} design - The design with dimensions and part type
   * @returns {boolean} - True if hole is within bounds
   */
  function checkHoleInBounds(hole, design) {
    const { x, y, diameter } = hole;
    const radius = diameter / 2;
    const { partType, dimensions } = design;
    
    switch (partType) {
      case 'rectangle':
        return x >= radius && 
               x <= dimensions.width - radius && 
               y >= radius && 
               y <= dimensions.height - radius;
        
      case 'circle':
        const centerX = dimensions.diameter / 2;
        const centerY = dimensions.diameter / 2;
        const partRadius = dimensions.diameter / 2;
        
        // Distance from hole center to part center
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        
        // Hole is within bounds if its outer edge is within the part's circle
        return distance + radius <= partRadius;
        
      case 'lShape':
        // Check if hole is within the L-shape
        const inTopBar = x >= radius && 
                         x <= dimensions.width - radius && 
                         y >= radius && 
                         y <= dimensions.legWidth - radius;
                         
        const inSideBar = x >= radius && 
                          x <= dimensions.legWidth - radius && 
                          y >= radius && 
                          y <= dimensions.height - radius;
                          
        return inTopBar || inSideBar;
        
      case 'uShape':
        // Check if hole is within the U-shape
        const inLeftBar = x >= radius && 
                          x <= dimensions.legWidth - radius && 
                          y >= radius && 
                          y <= dimensions.height - radius;
                          
        const inRightBar = x >= dimensions.width - dimensions.legWidth + radius && 
                           x <= dimensions.width - radius && 
                           y >= radius && 
                           y <= dimensions.height - radius;
                           
        const inBottomBar = x >= radius && 
                            x <= dimensions.width - radius && 
                            y >= dimensions.height - dimensions.flangeHeight + radius && 
                            y <= dimensions.height - radius;
                            
        return inLeftBar || inRightBar || inBottomBar;
        
      default:
        return false;
    }
  }
  
  /**
   * Checks minimum distance between holes
   * 
   * @param {Object} hole - The hole to check
   * @param {Array} allHoles - All holes in the design
   * @returns {number|null} - Index+1 of conflicting hole or null if no conflicts
   */
  function checkHoleMinimumDistance(hole, allHoles) {
    for (let i = 0; i < allHoles.length; i++) {
      const otherHole = allHoles[i];
      
      // Skip comparing to self (by checking ID)
      if (otherHole.id === hole.id) {
        continue;
      }
      
      const distance = Math.sqrt(
        Math.pow(hole.x - otherHole.x, 2) + 
        Math.pow(hole.y - otherHole.y, 2)
      );
      
      const largerDiameter = Math.max(hole.diameter, otherHole.diameter);
      const minRequiredDistance = largerDiameter;
      
      if (distance < minRequiredDistance) {
        return i + 1; // Return 1-based index
      }
    }
    
    return null;
  }
  
  /**
   * Check if a finish is compatible with a material
   * 
   * @param {string} material - Material ID
   * @param {string} finish - Finish ID
   * @returns {boolean} - True if compatible
   */
  function checkFinishCompatibility(material, finish) {
    if (finish === 'none') {
      return true; // 'None' finish is compatible with all materials
    }
    
    const compatibilityMap = {
      'steel': ['painted', 'powder-coated', 'galvanized'],
      'aluminum': ['painted', 'powder-coated', 'anodized', 'brushed', 'polished'],
      'copper': ['brushed', 'polished'],
      'brass': ['brushed', 'polished']
    };
    
    return compatibilityMap[material]?.includes(finish) || false;
  }