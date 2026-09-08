import { error, redirect, fail } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';
import { getUserTier } from '$lib/server/auth.js';

export async function load({ locals }) {
  if (!locals.user) redirect(303, '/auth/login');
  if (!locals.user.is_admin) error(403, 'Accès réservé aux administrateurs');

  const [users, quotes] = await Promise.all([db.users.all(), db.quotes.all()]);

  const enrichedUsers = users.map(u => {
    const userQuotes = quotes.filter(q => q.user_id === u.id);
    const totalSpend = userQuotes
      .filter(q => q.status !== 'cancelled')
      .reduce((s, q) => s + (Number(q.estimated_cost) || 0), 0);
    return {
      ...u,
      tier:       getUserTier(totalSpend).name,
      totalSpend,
      quoteCount: userQuotes.length,
      lastQuote:  userQuotes.length
        ? userQuotes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0].created_at
        : null
    };
  });

  const stats = {
    totalUsers:    users.length,
    totalQuotes:   quotes.length,
    pendingQuotes: quotes.filter(q => q.status === 'pending').length,
    revenue:       quotes.filter(q => q.status === 'validated')
                         .reduce((s, q) => s + (Number(q.estimated_cost) || 0), 0)
  };

  return { users: enrichedUsers, quotes, stats };
}

export const actions = {
  updateStatus: async ({ request, locals }) => {
    if (!locals.user?.is_admin) return fail(403, { error: 'Forbidden' });
    const form   = await request.formData();
    const id     = Number(form.get('id'));
    const status = String(form.get('status') ?? '');
    if (!['pending', 'validated', 'cancelled'].includes(status)) {
      return fail(400, { error: 'Invalid status' });
    }
    await db.quotes.updateStatus(id, status);
    return { success: true };
  }
};
