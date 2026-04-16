"use client";

import { useContext } from "react";

import { AuthContext, type AuthContextValue } from "./provider";
import type { Token, User } from "./types";

/**
 * Access the full auth context. Must be used inside an <AuthProvider>.
 *
 * ```tsx
 * const { user, isLoading, signIn, signOut } = useAuth();
 * ```
 */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}

/**
 * Get the current user or null.
 */
export function useUser(): User | null {
  return useAuth().user;
}

/**
 * Get the current token pair or null.
 */
export function useToken(): Token | null {
  return useAuth().token;
}
