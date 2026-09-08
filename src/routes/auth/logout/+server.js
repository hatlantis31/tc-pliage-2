import { redirect } from '@sveltejs/kit';
import { deleteSession } from '$lib/server/auth.js';

export function POST({ cookies }) {
  const sessionId = cookies.get('session');
  if (sessionId) deleteSession(sessionId);
  cookies.delete('session', { path: '/' });
  redirect(303, '/');
}
