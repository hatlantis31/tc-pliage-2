<script>
  import ContactForm from '$lib/components/ContactForm.svelte';
</script>

<section class="hero is-medium ">
  <div class="hero-body">
    <div class="container">
      <h1 class="title is-1">Contactez-nous</h1>
      <h2 class="subtitle">Pour vos Besoins en Fabrication Métallique d'Urgence</h2>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="columns">
      <div class="column is-6">
        <div class="content">
          <h2 class="title is-3">Informations de Contact</h2>
          <p>
            <strong>Adresse:</strong><br>
            Votre Adresse Ici
          </p>
          <p>
            <strong>Téléphone:</strong><br>
            Standard: 01 23 45 67 89<br>
            Urgence: 01 23 45 67 90
          </p>
          <p>
            <strong>Email:</strong><br>
            contact@tcpliage.fr
          </p>
          <p>
            <strong>Horaires:</strong><br>
            Service d'Urgence Disponible 24h/24 et 7j/7
          </p>
        </div>
        
        <div class="mt-6">
          <h3 class="title is-4">Localisation</h3>
          <div class="box">
            <!-- Ajoutez votre code d'intégration Google Maps ici -->
            <iframe
                    width="100%"
                    height="400"
                    style="border:0"
                    loading="lazy"
                    allowfullscreen
                    referrerpolicy="no-referrer-when-downgrade"
                    src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2889.9371526429886!2d1.4033!3d43.5356!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x12aebb7baf3310a3%3A0x1d4f860e16ef5296!2s3%20Av.%20du%20Bois%20Vert%2C%2031120%20Portet-sur-Garonne!5e0!3m2!1sfr!2sfr!4v1650000000000!5m2!1sfr!2sfr"
                  >
                  </iframe>
          </div>
        </div>
      </div>
      
      <div class="column is-6">
        <h2 class="title is-3">Envoyez-nous un Message</h2>
        <ContactForm />
      </div>
    </div>
  </div>
</section>

<style>
  .hero {
    background-image: url('/contact_hero.jpg');
    background-size: cover;
    background-position: center;
  }

  </style>

