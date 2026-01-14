// src/routes/api/email/+server.js
import { json } from '@sveltejs/kit';
import { RESEND_API_KEY } from '$env/static/private';

export async function POST({ request }) {
  try {
    const data = await request.json();

    // Validate required fields
    if (!data.replyTo || !data.subject) {
      return json(
        { success: false, error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Format email content
    const emailHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: linear-gradient(135deg, #E53935, #C62828); color: white; padding: 20px; border-radius: 8px 8px 0 0; }
          .content { background: #f9f9f9; padding: 20px; }
          .info-box { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #E53935; }
          .label { font-weight: bold; color: #666; }
          .value { color: #333; margin-left: 10px; }
          .design-data { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0; overflow-x: auto; }
          pre { white-space: pre-wrap; word-wrap: break-word; }
          .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1 style="margin: 0;">🔧 Nouvelle Conception TC PLIAGE</h1>
          </div>

          <div class="content">
            ${data.referenceNumber ? `
              <div class="info-box">
                <span class="label">Référence:</span>
                <span class="value">${data.referenceNumber}</span>
              </div>
            ` : ''}

            ${data.estimatedCost ? `
              <div class="info-box">
                <span class="label">Coût Estimé:</span>
                <span class="value">€${parseFloat(data.estimatedCost).toFixed(2)}</span>
              </div>
            ` : ''}

            ${data.productionDays ? `
              <div class="info-box">
                <span class="label">Délai de Production:</span>
                <span class="value">${data.productionDays} jours</span>
              </div>
            ` : ''}

            <div class="info-box">
              <span class="label">Email du client:</span>
              <span class="value">${data.replyTo}</span>
            </div>

            ${data.submittedAt ? `
              <div class="info-box">
                <span class="label">Date de Soumission:</span>
                <span class="value">${new Date(data.submittedAt).toLocaleString('fr-FR')}</span>
              </div>
            ` : ''}

            ${data.message ? `
              <div class="info-box">
                <span class="label">Message du client:</span>
                <div style="margin-top: 10px;">${data.message}</div>
              </div>
            ` : ''}

            ${data.designData ? `
              <h3>Détails de la Conception:</h3>
              <div class="design-data">
                <pre>${data.designData}</pre>
              </div>
            ` : ''}

            ${data.screenshot ? `
              <h3>Aperçu:</h3>
              <img src="${data.screenshot}" alt="Design Preview" style="max-width: 100%; border-radius: 4px; margin-top: 10px;">
            ` : ''}
          </div>

          <div class="footer">
            <p>TC PLIAGE - Fabrication Métallique d'Urgence</p>
            <p>3 Avenue du Bois Vert, Portet-Sur-Garonne</p>
          </div>
        </div>
      </body>
      </html>
    `;

    // Send email using Resend
    const emailResponse = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        from: 'TC PLIAGE <noreply@resend.dev>', // Use your verified domain or resend.dev for testing
        to: data.to || 'briand.malo@gmail.com',
        reply_to: data.replyTo,
        subject: data.subject,
        html: emailHtml
      })
    });

    const result = await emailResponse.json();

    if (!emailResponse.ok) {
      console.error('Resend API error:', result);
      throw new Error(result.message || 'Failed to send email via Resend');
    }

    return json({ success: true, id: result.id });

  } catch (error) {
    console.error('Email error:', error);
    return json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}