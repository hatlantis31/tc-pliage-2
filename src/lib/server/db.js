import { sql } from '@vercel/postgres';

// ── One-time schema bootstrap ──────────────────────────────────────────
// The CREATE TABLE IF NOT EXISTS statements are idempotent, so it's safe to
// await this on every cold start.  The cached promise makes repeat calls free.

let _initPromise = null;

function init() {
  if (_initPromise) return _initPromise;
  _initPromise = (async () => {
    await sql`
      CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         TEXT UNIQUE NOT NULL,
        name          TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin      BOOLEAN NOT NULL DEFAULT FALSE,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS sessions (
        id         TEXT PRIMARY KEY,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS quotes (
        id             SERIAL PRIMARY KEY,
        user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
        email          TEXT NOT NULL,
        nom            TEXT NOT NULL,
        telephone      TEXT,
        material       TEXT NOT NULL,
        thickness      REAL NOT NULL,
        width          REAL NOT NULL,
        total_length   REAL NOT NULL,
        bends_count    INTEGER NOT NULL DEFAULT 0,
        extras_count   INTEGER NOT NULL DEFAULT 0,
        estimated_cost REAL NOT NULL,
        design_data    TEXT NOT NULL,
        notes          TEXT,
        status         TEXT NOT NULL DEFAULT 'pending',
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )
    `;
  })();
  return _initPromise;
}

// ── Public API ────────────────────────────────────────────────────────────

export const db = {
  users: {
    async findByEmail(email) {
      await init();
      const { rows } = await sql`
        SELECT id, email, name, password_hash, is_admin, created_at
        FROM users WHERE email = ${email} LIMIT 1
      `;
      return rows[0] ?? null;
    },

    async findById(id) {
      await init();
      const { rows } = await sql`
        SELECT id, email, name, password_hash, is_admin, created_at
        FROM users WHERE id = ${id} LIMIT 1
      `;
      return rows[0] ?? null;
    },

    async all() {
      await init();
      const { rows } = await sql`
        SELECT id, email, name, is_admin, created_at
        FROM users ORDER BY created_at ASC
      `;
      return rows;
    },

    async insert({ email, name, password_hash }) {
      await init();
      // First user auto-promoted to admin
      const { rows: countRows } = await sql`SELECT COUNT(*)::int AS c FROM users`;
      const isFirst = countRows[0].c === 0;
      const { rows } = await sql`
        INSERT INTO users (email, name, password_hash, is_admin)
        VALUES (${email}, ${name}, ${password_hash}, ${isFirst})
        RETURNING id, email, name, is_admin, created_at
      `;
      return rows[0];
    }
  },

  sessions: {
    async findUser(sessionId) {
      await init();
      const { rows } = await sql`
        SELECT u.id, u.email, u.name, u.is_admin, u.created_at
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.id = ${sessionId} AND s.expires_at > NOW()
        LIMIT 1
      `;
      return rows[0] ?? null;
    },

    async create(id, userId, expiresAt) {
      await init();
      await sql`
        INSERT INTO sessions (id, user_id, expires_at)
        VALUES (${id}, ${userId}, ${expiresAt})
      `;
    },

    async delete(id) {
      await init();
      await sql`DELETE FROM sessions WHERE id = ${id}`;
    }
  },

  quotes: {
    async insert(d) {
      await init();
      const { rows } = await sql`
        INSERT INTO quotes (
          user_id, email, nom, telephone, material, thickness, width,
          total_length, bends_count, extras_count, estimated_cost,
          design_data, notes
        ) VALUES (
          ${d.user_id ?? null}, ${d.email}, ${d.nom}, ${d.telephone ?? null},
          ${d.material}, ${d.thickness}, ${d.width}, ${d.total_length},
          ${d.bends_count ?? 0}, ${d.extras_count ?? 0}, ${d.estimated_cost},
          ${d.design_data}, ${d.notes ?? null}
        )
        RETURNING id, status, created_at
      `;
      return rows[0];
    },

    async findByUser(userId, limit = 50) {
      await init();
      const { rows } = await sql`
        SELECT id, material, thickness, width, total_length,
               bends_count, extras_count, estimated_cost, notes,
               status, created_at
        FROM quotes
        WHERE user_id = ${userId}
        ORDER BY created_at DESC
        LIMIT ${limit}
      `;
      return rows;
    },

    async sumByUser(userId) {
      await init();
      const { rows } = await sql`
        SELECT COALESCE(SUM(estimated_cost), 0)::float AS total
        FROM quotes
        WHERE user_id = ${userId} AND status != 'cancelled'
      `;
      return rows[0].total;
    },

    async all() {
      await init();
      const { rows } = await sql`
        SELECT id, user_id, email, nom, telephone, material, thickness,
               width, total_length, bends_count, extras_count,
               estimated_cost, notes, status, created_at
        FROM quotes
        ORDER BY created_at DESC
      `;
      return rows;
    },

    async updateStatus(id, status) {
      await init();
      const { rows } = await sql`
        UPDATE quotes SET status = ${status}
        WHERE id = ${id}
        RETURNING id, status
      `;
      return rows[0] ?? null;
    }
  }
};
