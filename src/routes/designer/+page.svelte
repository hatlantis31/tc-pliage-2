// src/routes/designer/+page.svelte
<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  
  // Import our utility modules
  import { designStore } from '$lib/stores/designStore.js';
  import metalApiService from '$lib/services/metalApiService.js';
  import { validateDesign } from '$lib/utils/validationUtils.js';
  import '$lib/styles/metal-designer.css';
  
  // Import step components
  import PartTypeStep from '$lib/components/steps/PartTypeStep.svelte';
  import DimensionsStep from '$lib/components/steps/DimensionsStep.svelte';
  import HolesStep from '$lib/components/steps/HolesStep.svelte';
  import MaterialStep from '$lib/components/steps/MaterialStep.svelte';
  import ReviewStep from '$lib/components/steps/ReviewStep.svelte';
  
  // Step configuration
  const steps = [
    { id: 'part-type', title: 'Select Part Type', component: PartTypeStep },
    { id: 'dimensions', title: 'Configure Dimensions', component: DimensionsStep },
    { id: 'holes', title: 'Add Holes (Optional)', component: HolesStep },
    { id: 'material', title: 'Material & Finish', component: MaterialStep },
    { id: 'review', title: 'Review & Submit', component: ReviewStep }
  ];
  
  // Track current step
  let currentStepIndex = 0;
  
  // Reactively bind to the design store
  let design;
  const unsubscribe = designStore.subscribe(value => {
    design = value;
  });
  
  // Clean up subscription when component is destroyed
  onMount(() => {
    return () => {
      unsubscribe();
    };
  });
  
  // Message handling
  let message = null;
  let messageType = 'is-info';
  let isSubmitting = false;
  
  function showMessage(text, type = 'is-info') {
    message = text;
    messageType = type;
    setTimeout(() => {
      message = null;
    }, 5000);
  }
  
  // Navigation functions
  function nextStep() {
    if (validateCurrentStep()) {
      if (currentStepIndex < steps.length - 1) {
        currentStepIndex++;
      }
    }
  }
  
  function previousStep() {
    if (currentStepIndex > 0) {
      currentStepIndex--;
    }
  }
  
  function goToStep(index) {
    // Only allow going to a step if all previous steps are valid
    if (index < currentStepIndex || validateStepsUpTo(index)) {
      currentStepIndex = index;
    } else {
      showMessage('Please complete the current step before proceeding', 'is-warning');
    }
  }
  
  // Validation using our validation utility
  function validateCurrentStep() {
    const stepId = steps[currentStepIndex].id;
    
    // Use the validation utility to check the current step
    const result = validateStep(currentStepIndex);
    
    if (!result.isValid) {
      showMessage(result.message, 'is-warning');
    }
    
    return result.isValid;
  }
  
  function validateStep(stepIndex) {
    const stepId = steps[stepIndex].id;
    
    switch(stepId) {
      case 'part-type':
        if (!design.partType) {
          return { isValid: false, message: 'Please select a part type' };
        }
        return { isValid: true };
      
      case 'dimensions':
        if (!design.dimensions || Object.keys(design.dimensions).length === 0) {
          return { isValid: false, message: 'Please configure dimensions' };
        }
        
        // Check specific dimensions based on part type
        const dims = design.dimensions;
        switch(design.partType) {
          case 'rectangle':
            if (!dims.width || !dims.height) {
              return { isValid: false, message: 'Please specify width and height' };
            }
            break;
          case 'lShape':
            if (!dims.width || !dims.height || !dims.legWidth) {
              return { isValid: false, message: 'Please specify all L-shape dimensions' };
            }
            break;
          case 'uShape':
            if (!dims.width || !dims.height || !dims.legWidth || !dims.flangeHeight) {
              return { isValid: false, message: 'Please specify all U-shape dimensions' };
            }
            break;
          case 'circle':
            if (!dims.diameter) {
              return { isValid: false, message: 'Please specify the diameter' };
            }
            break;
        }
        return { isValid: true };
      
      case 'holes':
        // Holes are optional
        return { isValid: true };
      
      case 'material':
        if (!design.material || !design.thickness) {
          return { isValid: false, message: 'Please select material and thickness' };
        }
        
        // Validate finish for material
        if (design.finish === 'anodized' && design.material !== 'aluminum') {
          return { isValid: false, message: 'Anodizing is only available for aluminum' };
        }
        return { isValid: true };
      
      default:
        return { isValid: true };
    }
  }
  
  function validateStepsUpTo(index) {
    for (let i = 0; i <= index; i++) {
      const result = validateStep(i);
      if (!result.isValid) {
        return false;
      }
    }
    return true;
  }
  
  // Update design data from child components by using store
  function handleUpdate(event) {
    const { field, value } = event.detail;
    designStore.updateField(field, value);
  }
  
  // JSON Export/Import
  function exportDesign() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(designStore.exportDesign());
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `metal-design-${design.id}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
    
    showMessage('Design exported successfully', 'is-success');
  }
  
  let importInput;
  
  function triggerImportDialog() {
    importInput.click();
  }
  
  function handleImportFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importedDesign = JSON.parse(e.target.result);
        designStore.loadDesign(importedDesign);
        showMessage('Design imported successfully', 'is-success');
        // Go to first step to validate all data
        currentStepIndex = 0;
      } catch (error) {
        showMessage('Error importing design: Invalid JSON file', 'is-danger');
      }
    };
    reader.readAsText(file);
  }
  // Function to capture screenshot of the design
async function captureDesignScreenshot() {
  try {
    // Get the preview container
    const previewElement = document.querySelector('.preview-container');
    if (!previewElement) {
      console.warn('Preview container not found');
      return null;
    }

    // Use html2canvas library (you'll need to add this)
    // For now, we'll create a simple canvas representation
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const svg = previewElement.querySelector('svg');

    if (svg) {
      // Get SVG dimensions
      const bbox = svg.getBBox();
      canvas.width = bbox.width || 400;
      canvas.height = bbox.height || 300;

      // Convert SVG to data URL
      const svgData = new XMLSerializer().serializeToString(svg);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      return url;
    }

    return null;
  } catch (error) {
    console.error('Error capturing screenshot:', error);
    return null;
  }
}

// Function to send email with design details
async function sendDesignEmail(design, referenceNumber, estimatedCost, productionDays) {
  try {
    const screenshot = await captureDesignScreenshot();

    const emailData = {
      to: 'briand.malo@gmail.com',
      subject: `Nouvelle Conception de Pièce Métallique - ${referenceNumber}`,
      designData: JSON.stringify(design, null, 2),
      referenceNumber: referenceNumber,
      estimatedCost: estimatedCost,
      productionDays: productionDays,
      screenshot: screenshot,
      submittedAt: new Date().toISOString()
    };

    // Send to a serverless function or email service
    const response = await fetch('/api/send-design-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(emailData)
    });

    if (!response.ok) {
      throw new Error('Failed to send email');
    }

    return true;
  } catch (error) {
    console.error('Error sending email:', error);
    return false;
  }
}

 async function submitDesign() {
  try {
    isSubmitting = true;

    // Validate the entire design before submitting
    const validationResult = validateDesign(design);
    if (!validationResult.isValid) {
      const firstError = Object.values(validationResult.errors)[0];
      showMessage(`Validation error: ${firstError}`, 'is-danger');
      isSubmitting = false;
      return;
    }

    // Submit to API service
    const result = await metalApiService.submitDesign(design);

    if (result.success) {
      // Send email with design details
      await sendDesignEmail(
        design,
        result.referenceNumber,
        result.estimatedCost,
        result.estimatedProductionDays
      );

      // Redirect to success page
      goto(`/designer/success?ref=${result.referenceNumber}&cost=${result.estimatedCost}&days=${result.estimatedProductionDays}`);
    } else {
      throw new Error(result.message || 'Error submitting design');
    }
  } catch (error) {
    showMessage('Error submitting design: ' + error.message, 'is-danger');
    isSubmitting = false;
  }
}
</script>

<div class="container">
  <div class="section">
    <h1 class="title has-text-centered">Metal Part Designer</h1>
    <p class="subtitle has-text-centered">Design custom metal parts with precise specifications</p>
    
    <!-- Message display -->
    {#if message}
      <div class="notification {messageType}">
        <button class="delete" on:click={() => message = null}></button>
        {message}
      </div>
    {/if}
    
    <!-- Import/Export buttons -->
    <div class="buttons is-centered mb-5">
      <button class="button is-info is-small" on:click={exportDesign}>
        <span class="icon">
          <i class="fas fa-download"></i>
        </span>
        <span>Export Design</span>
      </button>
      
      <button class="button is-info is-small" on:click={triggerImportDialog}>
        <span class="icon">
          <i class="fas fa-upload"></i>
        </span>
        <span>Import Design</span>
      </button>
      <input 
        bind:this={importInput}
        type="file" 
        accept=".json" 
        on:change={handleImportFile} 
        style="display: none;"
      />
    </div>
    
    <!-- Progress tracker -->
    <div class="steps is-centered mb-5">
      {#each steps as step, index}
        <div 
          class="step-item {index <= currentStepIndex ? 'is-active' : ''} {index < currentStepIndex ? 'is-completed' : ''}"
          on:click={() => goToStep(index)}
        >
          <div class="step-marker">{index + 1}</div>
          <div class="step-details">
            <p class="step-title">{step.title}</p>
          </div>
        </div>
      {/each}
    </div>
    
    <!-- Current step -->
    <div class="box">
      <h2 class="title is-4">{steps[currentStepIndex].title}</h2>
      
      <svelte:component 
        this={steps[currentStepIndex].component} 
        {design}
        on:update={handleUpdate}
      />
      
      <!-- Navigation buttons -->
      <div class="buttons is-centered mt-5">
        {#if currentStepIndex > 0}
          <button class="button" on:click={previousStep}>
            <span class="icon">
              <i class="fas fa-arrow-left"></i>
            </span>
            <span>Previous</span>
          </button>
        {/if}
        
        {#if currentStepIndex < steps.length - 1}
          <button class="button is-primary" on:click={nextStep}>
            <span>Next</span>
            <span class="icon">
              <i class="fas fa-arrow-right"></i>
            </span>
          </button>
        {:else}
        {/if}
      </div>
    </div>
  </div>
</div>

<style>

</style>