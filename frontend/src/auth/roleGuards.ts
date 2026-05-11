import type { User } from "../api/types";

export function canCreateRun(user: User | null) {
  return user?.role === "admin" || user?.role === "researcher";
}

export function canStartRun(user: User | null) {
  return canCreateRun(user);
}

export function canManageUsers(user: User | null) {
  return user?.role === "admin";
}

export function canEditDictionaries(user: User | null) {
  return user?.role === "admin" || user?.role === "researcher";
}

export function canDelete(user: User | null) {
  return user?.role === "admin";
}
