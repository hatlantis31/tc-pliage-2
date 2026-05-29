import { json } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';

export async function POST({ request, locals }) {
  try {
    const d = await request.json();

    if (!d.email || !d.nom || !d.material) {
      return json({ success: false, error: 'Missing required fields' }, { status: 400 });
    }

    const { lastInsertRowid } = db.prepare(`
      INSERT INTO quotes
        (user_id, email, nom, telephone, material, thickness, width, total_length,
         bends_count, extras_count, estimated_cost, design_data, notes)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      locals.user?.id ?? null,
      d.email,
      d.nom,
      d.telephone ?? null,
      d.material,
      d.thickness,
      d.width,
      d.totalLength,
      d.bendsCount ?? 0,
      d.extrasCount ?? 0,
      d.estimatedCost,
      d.designData,
      d.notes ?? null
    );

    return json({ success: true, id: Number(lastInsertRowid) });
  } catch (err) {
    console.error('Quote save error:', err);
    return json({ success: false, error: err.message }, { status: 500 });
  }
}
