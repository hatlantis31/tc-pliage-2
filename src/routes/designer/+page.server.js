import { getUserTier, getUserTotalSpend } from '$lib/server/auth.js';

export function load({ locals }) {
  if (!locals.user) {
    return { user: null, discount: 0, tier: null, totalSpend: 0 };
  }
  const { id, name, email } = locals.user;
  const totalSpend = getUserTotalSpend(id);
  const tier = getUserTier(totalSpend);
  return {
    user: { id, name, email },
    discount: tier.discount,
    tier: tier.name,
    totalSpend
  };
}
