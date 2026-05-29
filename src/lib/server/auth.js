import { db } from './db.js';

export function getUserTier(totalSpend) {
  if (totalSpend >= 2000) return { name: 'Or',     discount: 0.10, next: null,    nextThreshold: null };
  if (totalSpend >= 500)  return { name: 'Argent', discount: 0.05, next: 'Or',    nextThreshold: 2000 };
  return                         { name: 'Bronze', discount: 0,    next: 'Argent', nextThreshold: 500  };
}

export function getUserTotalSpend(userId) {
  return db.quotes.sumByUser(userId);
}

export function createSession(userId) {
  const id = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  db.sessions.create(id, userId, expiresAt);
  return { id, expiresAt };
}

export function deleteSession(sessionId) {
  db.sessions.delete(sessionId);
}

export function getSessionUser(sessionId) {
  return db.sessions.findUser(sessionId);
}
