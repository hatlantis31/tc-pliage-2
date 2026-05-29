export function load({ locals }) {
  const u = locals.user;
  return {
    user: u ? { id: u.id, name: u.name, email: u.email } : null
  };
}
