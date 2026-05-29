import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

const dataDir = join(process.cwd(), 'data');
mkdirSync(dataDir, { recursive: true });

function load(table) {
  const p = join(dataDir, `${table}.json`);
  if (!existsSync(p)) return [];
  try { return JSON.parse(readFileSync(p, 'utf-8')); }
  catch { return []; }
}

function save(table, rows) {
  writeFileSync(join(dataDir, `${table}.json`), JSON.stringify(rows));
}

function nextId(rows) {
  return rows.length === 0 ? 1 : Math.max(...rows.map(r => r.id ?? 0)) + 1;
}

export const db = {
  users: {
    findByEmail: (email) => load('users').find(u => u.email === email) ?? null,
    findById:    (id)    => load('users').find(u => u.id === id) ?? null,
    insert(data) {
      const rows = load('users');
      const row = { id: nextId(rows), created_at: new Date().toISOString(), ...data };
      rows.push(row);
      save('users', rows);
      return row;
    }
  },

  sessions: {
    findUser(sessionId) {
      const sessions = load('sessions');
      const s = sessions.find(s => s.id === sessionId && new Date(s.expires_at) > new Date());
      if (!s) return null;
      return load('users').find(u => u.id === s.user_id) ?? null;
    },
    create(id, userId, expiresAt) {
      const rows = load('sessions');
      rows.push({ id, user_id: userId, expires_at: expiresAt, created_at: new Date().toISOString() });
      save('sessions', rows);
    },
    delete(id) {
      save('sessions', load('sessions').filter(s => s.id !== id));
    }
  },

  quotes: {
    insert(data) {
      const rows = load('quotes');
      const row = { id: nextId(rows), status: 'pending', created_at: new Date().toISOString(), ...data };
      rows.push(row);
      save('quotes', rows);
      return row;
    },
    findByUser(userId, limit = 50) {
      return load('quotes')
        .filter(q => q.user_id === userId)
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .slice(0, limit);
    },
    sumByUser(userId) {
      return load('quotes')
        .filter(q => q.user_id === userId && q.status !== 'cancelled')
        .reduce((s, q) => s + (q.estimated_cost ?? 0), 0);
    }
  }
};
