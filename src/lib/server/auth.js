import { db } from './db.js';

export function getUserTier(totalSpend) {
  if (totalSpend >= 2000) {
    return { name: 'Or', discount: 0.10, color: 'amber', next: null, nextThreshold: null };
  }
  if (totalSpend >= 500) {
    return { name: 'Argent', discount: 0.05, color: 'silver', next: 'Or', nextThreshold: 2000 };
  }
  return { name: 'Bronze', discount: 0, color: 'bronze', next: 'Argent', nextThreshold: 500 };
}

export function getUserTotalSpend(userId) {
  const row = db.prepare(`
    SELECT COALESCE(SUM(estimated_cost), 0) AS total
    FROM quotes
    WHERE user_id = ? AND status != 'cancelled'
  `).get(userId);
  return row?.total ?? 0;
}

export function createSession(userId) {
  const id = crypto.randomUUID();
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
  db.prepare('INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)').run(id, userId, expiresAt);
  return { id, expiresAt };
}

export function deleteSession(sessionId) {
  db.prepare('DELETE FROM sessions WHERE id = ?').run(sessionId);
}

export function getSessionUser(sessionId) {
  return db.prepare(`
    SELECT u.id, u.email, u.name, u.created_at
    FROM sessions s
    JOIN users u ON u.id = s.user_id
    WHERE s.id = ? AND s.expires_at > datetime('now')
  `).get(sessionId) ?? null;
}
