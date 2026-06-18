export function hasAnyPermission(user, permissions = []) {
  if (!permissions.length) return true;
  const owned = new Set(user?.permissions || []);
  return permissions.some((permission) => owned.has(permission));
}

export function hasAnyRole(user, roles = []) {
  if (!roles.length) return true;
  return roles.includes(user?.role);
}

export function canAccess(user, { permissions = [], roles = [] } = {}) {
  return hasAnyPermission(user, permissions) && hasAnyRole(user, roles);
}

export function defaultPathForUser(user) {
  if (!user) return "/login";
  if (hasAnyPermission(user, ["analytics:read"])) return "/";
  if (user.role === "parent") return "/parent";
  if (["student", "teacher", "admin", "manager"].includes(user.role)) return "/lms";
  return "/settings";
}
