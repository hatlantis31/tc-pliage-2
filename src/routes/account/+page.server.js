import { redirect } from '@sveltejs/kit';
import { db } from '$lib/server/db.js';
import { getUserTier, getUserTotalSpend } from '$lib/server/auth.js';

export function load({ locals }) {
  if (!locals.user) redirect(303, '/auth/login');

  const { id, name, email, created_at } = locals.user;
  const totalSpend = getUserTotalSpend(id);
  const tier   = getUserTier(totalSpend);
  const quotes = db.quotes.findByUser(id);

  return { user: { id, name, email, created_at }, totalSpend, tier, quotes };
}
