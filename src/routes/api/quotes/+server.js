import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';

export async function POST({ request, locals }) {
  try {
    const d = await request.json();
    if (!d.email || !d.nom || !d.material) {
      return json({ success: false, error: 'Missing required fields' }, { status: 400 });
    }

    const quote = db.quotes.insert({
      user_id:       locals.user?.id ?? null,
      email:         d.email,
      nom:           d.nom,
      telephone:     d.telephone ?? null,
      material:      d.material,
      thickness:     d.thickness,
      width:         d.width,
      total_length:  d.totalLength,
      bends_count:   d.bendsCount  ?? 0,
      extras_count:  d.extrasCount ?? 0,
      estimated_cost: d.estimatedCost,
      design_data:   d.designData,
      notes:         d.notes ?? null
    });

    return json({ success: true, id: quote.id });
  } catch (err) {
    console.error('Quote save error:', err);
    return json({ success: false, error: err.message }, { status: 500 });
  }
}
