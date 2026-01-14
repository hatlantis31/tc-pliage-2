// src/routes/designer/success/+page.svelte
<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  
  // Get submission details from URL parameters
  let referenceNumber = $page.url.searchParams.get('ref');
  let estimatedCost = parseFloat($page.url.searchParams.get('cost') || '0');
  let productionDays = parseFloat($page.url.searchParams.get('days') || '0');
  
  // If no reference number, redirect to designer
  onMount(() => {
    if (!referenceNumber) {
      window.location.href = '/designer';
    }
  });
  
  // Format the cost with 2 decimal places and euro symbol
  function formatCost(cost) {
    return `€${cost.toFixed(2)}`;
  }
  
  // Calculate the estimated delivery date
  function calculateDeliveryDate(days) {
    const date = new Date();
    let businessDays = Math.ceil(days);
    
    while (businessDays > 0) {
      date.setDate(date.getDate() + 1);
      
      // Skip weekends
      if (date.getDay() !== 0 && date.getDay() !== 6) {
        businessDays--;
      }
    }
    
    // Format date as DD/MM/YYYY
    return date.toLocaleDateString('fr-FR');
  }
  
  // Get delivery date
  const deliveryDate = calculateDeliveryDate(productionDays);
</script>

<div class="container">
  <section class="section">
    <div class="columns is-centered">
      <div class="column is-8">
        <div class="box has-text-centered">
          <img src="/images/check-success.svg" alt="Success" class="success-icon mb-4" width="120">
          
          <h1 class="title is-2 has-text-success">Design Submitted Successfully!</h1>
          <p class="subtitle">Your custom metal part design has been received.</p>
          
          <div class="notification is-success is-light my-5">
            <p class="is-size-4">Reference Number: <strong>{referenceNumber}</strong></p>
            <p class="is-size-7 mt-2">Please keep this number for tracking your order.</p>
          </div>
          
          <div class="content">
            <h2 class="title is-4">Order Details</h2>
            
            <div class="columns">
              <div class="column">
                <div class="box has-background-light">
                  <p class="heading">Estimated Cost</p>
                  <p class="title is-3">{formatCost(estimatedCost)}</p>
                </div>
              </div>
              
              <div class="column">
                <div class="box has-background-light">
                  <p class="heading">Estimated Delivery</p>
                  <p class="title is-3">{deliveryDate}</p>
                  <p class="is-size-7">({productionDays} business days)</p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="content">
            <h3 class="title is-5">What happens next?</h3>
            
            <div class="steps-vertical">
              <div class="step-vertical">
                <div class="step-marker">1</div>
                <div class="step-content">
                  <h4 class="title is-6">Quote Verification</h4>
                  <p>Our team will review your design and verify the quote.</p>
                </div>
              </div>
              
              <div class="step-vertical">
                <div class="step-marker">2</div>
                <div class="step-content">
                  <h4 class="title is-6">Confirmation Email</h4>
                  <p>You'll receive a confirmation email with final pricing and payment instructions within 24 hours.</p>
                </div>
              </div>
              
              <div class="step-vertical">
                <div class="step-marker">3</div>
                <div class="step-content">
                  <h4 class="title is-6">Production</h4>
                  <p>Once payment is received, we'll start producing your custom part.</p>
                </div>
              </div>
              
              <div class="step-vertical">
                <div class="step-marker">4</div>
                <div class="step-content">
                  <h4 class="title is-6">Delivery</h4>
                  <p>Your finished part will be carefully packaged and shipped to your address.</p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="buttons is-centered mt-6">
            <a href="/designer" class="button is-primary">
              <span class="icon">
                <i class="fas fa-plus"></i>
              </span>
              <span>Design Another Part</span>
            </a>
            
            <a href="/contact" class="button is-light">
              <span class="icon">
                <i class="fas fa-envelope"></i>
              </span>
              <span>Contact Us</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<style>
  .success-icon {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1);
    }
  }
  
  .steps-vertical {
    position: relative;
    padding-left: 2.5rem;
    max-width: 30rem;
    margin: 0 auto;
  }
  
  .steps-vertical::before {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    left: 1rem;
    width: 2px;
    background-color: #dbdbdb;
  }
  
  .step-vertical {
    position: relative;
    margin-bottom: 2rem;
  }
  
  .step-vertical:last-child {
    margin-bottom: 0;
  }
  
  .step-marker {
    width: 2rem;
    height: 2rem;
    border-radius: 50%;
    background-color: #3273dc;
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    position: absolute;
    top: 0;
    left: -2.5rem;
    z-index: 1;
  }
  
  .step-content {
    padding-bottom: 0.5rem;
  }
</style>