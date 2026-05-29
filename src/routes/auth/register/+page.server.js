import { fail, redirect } from '@sveltejs/kit';
import bcrypt from 'bcryptjs';
import { db } from '$lib/server/db.js';
import { createSession } from '$lib/server/auth.js';

export const actions = {
  default: async ({ request, cookies }) => {
    const form = await request.formData();
    const name  = String(form.get('name')  ?? '').trim();
    const email = String(form.get('email') ?? '').trim().toLowerCase();
    const pass  = String(form.get('password') ?? '');

    if (!name || !email || !pass) {
      return fail(400, { error: 'Tous les champs sont requis.', name, email });
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return fail(400, { error: 'Adresse email invalide.', name, email });
    }
    if (pass.length < 8) {
      return fail(400, { error: 'Le mot de passe doit comporter au moins 8 caractères.', name, email });
    }

    const existing = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
    if (existing) {
      return fail(409, { error: 'Un compte existe déjà avec cet email.', name, email });
    }

    const hash = await bcrypt.hash(pass, 12);
    const { lastInsertRowid } = db.prepare(
      'INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)'
    ).run(email, name, hash);

    const { id, expiresAt } = createSession(Number(lastInsertRowid));
    cookies.set('session', id, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      expires: new Date(expiresAt)
    });

    redirect(303, '/account');
  }
};
