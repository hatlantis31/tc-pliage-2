import Database from 'better-sqlite3';
import { mkdirSync } from 'fs';
import { join } from 'path';

const dataDir = join(process.cwd(), 'data');
mkdirSync(dataDir, { recursive: true });

const db = new Database(join(dataDir, 'app.db'));
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    UNIQUE NOT NULL,
    name          TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT    PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT    NOT NULL,
    created_at TEXT    DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS quotes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    email          TEXT    NOT NULL,
    nom            TEXT    NOT NULL,
    telephone      TEXT,
    material       TEXT    NOT NULL,
    thickness      REAL    NOT NULL,
    width          REAL    NOT NULL,
    total_length   REAL    NOT NULL,
    bends_count    INTEGER NOT NULL DEFAULT 0,
    extras_count   INTEGER NOT NULL DEFAULT 0,
    estimated_cost REAL    NOT NULL,
    design_data    TEXT    NOT NULL,
    notes          TEXT,
    status         TEXT    NOT NULL DEFAULT 'pending',
    created_at     TEXT    DEFAULT (datetime('now'))
  );
`);

export { db };
