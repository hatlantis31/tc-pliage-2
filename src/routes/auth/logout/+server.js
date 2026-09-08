import { redirect } from '@sveltejs/kit';
import { deleteSession } from '$lib/server/auth.js';

export async function POST({ cookies }) {
  const sessionId = cookies.get('session');
  if (sessionId) await deleteSession(sessionId);
  cookies.delete('session', { path: '/' });
  redirect(303, '/');
}
