import { db } from './db.js';

export function getUserTier(totalSpend) {
  if (totalSpend >= 2000) return { name: 'Or',     discount: 0.10, next: null,     nextThreshold: null };
  if (totalSpend >= 500)  return { name: 'Argent', discount: 0.05, next: 'Or',     nextThreshold: 2000 };
  return                         { name: 'Bronze', discount: 0,    next: 'Argent', nextThreshold: 500  };
}

export async function getUserTotalSpend(userId) {
  return await db.quotes.sumByUser(userId);
}

export async function createSession(userId) {
  const id = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  await db.sessions.create(id, userId, expiresAt);
  return { id, expiresAt };
}

export async function deleteSession(sessionId) {
  await db.sessions.delete(sessionId);
}

export async function getSessionUser(sessionId) {
  return await db.sessions.findUser(sessionId);
}
