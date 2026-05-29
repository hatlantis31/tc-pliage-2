import { fail, redirect } from '@sveltejs/kit';
import bcrypt from 'bcryptjs';
import { db } from '$lib/server/db.js';
import { createSession } from '$lib/server/auth.js';

export const actions = {
  default: async ({ request, cookies }) => {
    const form  = await request.formData();
    const email = String(form.get('email') ?? '').trim().toLowerCase();
    const pass  = String(form.get('password') ?? '');

    if (!email || !pass) {
      return fail(400, { error: 'Email et mot de passe requis.', email });
    }

    const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
    const valid = user && await bcrypt.compare(pass, user.password_hash);
    if (!valid) {
      return fail(401, { error: 'Email ou mot de passe incorrect.', email });
    }

    const { id, expiresAt } = createSession(user.id);
    cookies.set('session', id, {
      httpOnly: true,
      sameSite: 'lax',
      path: '/',
      expires: new Date(expiresAt)
    });

    redirect(303, '/account');
  }
};
