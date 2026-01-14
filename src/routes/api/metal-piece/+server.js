// src/routes/api/metal-piece/+server.js
import { json } from '@sveltejs/kit';
import { v4 as uuidv4 } from 'uuid';

/**
 * Handles POST requests to create a new metal part design
 * 
 * @param {Object} request - The request object
 * @returns {Object} - JSON response with the result
 */
export async function POST({ request }) {
  try {
    // Parse the request body
    const designData = await request.json();
    
    // Validate the design data
    const validationResult = validateDesign(designData);
    
    if (!validationResult.isValid) {
      return json({
        success: false,
        error: 'Invalid design data',
        validationErrors: validationResult.errors
      }, { status: 400 });
    }
    
    // In a real application, we would save this to a database
    // For now, we'll just simulate a successful creation
    
    // Generate a reference number
    const referenceNumber = generateReferenceNumber();
    
    // Calculate estimated cost
    const cost = calculateEstimatedCost(designData);
    
    // Calculate production time
    const productionTime = estimateProductionTime(designData);
    
    return json({
      success: true,
      message: 'Design submitted successfully',
      referenceNumber,
      estimatedCost: cost,
      estimatedProductionDays: productionTime,
      design: designData
    });
  } catch (error) {
    console.error('Error processing design submission:', error);
    
    return json({
      success: false,
      error: 'Error processing design submission',
      message: error.message
    }, { status: 500 });
  }
}

/**
 * Validates the design data
 * In a real application, this would be imported from a validation module
 * 
 * @param {Object} design - The design to validate
 * @returns {Object} - Validation result
 */
function validateDesign(design) {
  // Simple validation for demonstration purposes
  const errors = {};
  
  if (!design.partType) {
    errors.partType = 'Part type is required';
  }
  
  if (!design.material) {
    errors.material = 'Material is required';
  }
  
  if (!design.thickness || design.thickness <= 0) {
    errors.thickness = 'Valid thickness is required';
  }
  
  if (!design.dimensions || Object.keys(design.dimensions).length === 0) {
    errors.dimensions = 'Dimensions are required';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * Generates a unique reference number for the design
 * 
 * @returns {string} - The reference number
 */
function generateReferenceNumber() {
  const prefix = 'TCP';
  const timestamp = Date.now().toString().slice(-6);
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  
  return `${prefix}-${timestamp}-${random}`;
}

/**
 * Calculates an estimated cost for the design
 * In a real application, this would be much more complex
 * 
 * @param {Object} design - The design to estimate cost for
 * @returns {number} - The estimated cost in euros
 */
function calculateEstimatedCost(design) {
  // Base costs for materials per cm³
  const materialCosts = {
    'steel': 0.08,
    'aluminum': 0.12,
    'copper': 0.25,
    'brass': 0.20
  };
  
  // Multipliers for finishes
  const finishMultipliers = {
    'none': 1.0,
    'painted': 1.2,
    'powder-coated': 1.3,
    'galvanized': 1.25,
    'anodized': 1.4,
    'brushed': 1.15,
    'polished': 1.35
  };
  
  // Material density (g/cm³)
  const densities = {
    'steel': 7.85,
    'aluminum': 2.7,
    'copper': 8.96,
    'brass': 8.4
  };
  
  // Calculate volume in cm³
  let volume = 0;
  const thicknessInCm = design.thickness / 10;
  
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
  }
  
  // Subtract volume of holes
  if (design.holes && design.holes.length > 0) {
    design.holes.forEach(hole => {
      const holeRadius = hole.diameter / 20; // diameter/2 in cm
      const holeVolume = Math.PI * holeRadius * holeRadius * thicknessInCm;
      volume -= holeVolume;
    });
  }
  
  // Calculate material cost
  const materialCost = volume * materialCosts[design.material];
  
  // Add cost for each hole (drilling)
  const holeCost = (design.holes?.length || 0) * 1.5;
  
  // Apply finish multiplier
  const finishMultiplier = finishMultipliers[design.finish] || 1.0;
  
  // Calculate total cost
  const subtotal = (materialCost + holeCost) * finishMultiplier;
  
  // Add fixed costs (setup, handling, etc.)
  const fixedCosts = 15;
  
  // Calculate final cost with a minimum of €20
  return Math.max(20, subtotal + fixedCosts);
}

/**
 * Estimates production time for the design
 * 
 * @param {Object} design - The design to estimate production time for
 * @returns {number} - Estimated production time in business days
 */
function estimateProductionTime(design) {
  // Base time depends on part type
  let baseTime = 1; // 1 day
  
  // Add time for complex shapes
  if (design.partType === 'lShape') {
    baseTime += 0.5;
  } else if (design.partType === 'uShape') {
    baseTime += 1;
  }
  
  // Add time for holes
  if (design.holes && design.holes.length > 0) {
    baseTime += 0.2 * Math.min(design.holes.length, 10); // Cap at 10 holes
  }
  
  // Add time for finishing
  if (design.finish !== 'none') {
    // Special finishes take longer
    if (['powder-coated', 'anodized'].includes(design.finish)) {
      baseTime += 1;
    } else {
      baseTime += 0.5;
    }
  }
  
  // Round up to nearest half day
  return Math.ceil(baseTime * 2) / 2;
}