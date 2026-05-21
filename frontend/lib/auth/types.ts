// ─── User & Token ──────────────────────────────────────────────────────────

/** Authenticated user profile returned by the backend `/auth/me` endpoint. */
export interface User {
  id: string;
  email: string;
  fullName: string | null;
  role: "user" | "admin";
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
}

/** JWT token pair issued by the backend on login, registration, or refresh. */
export interface Token {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}

/** Reactive auth state exposed by the AuthProvider context. */
export interface AuthState {
  user: User | null;
  token: Token | null;
  isLoading: boolean;
}

// ─── API request / response shapes ──────────────────────────────────────────

/** Credentials required for new account registration. */
export interface SignUpCredentials {
  email: string;
  password: string;
  fullName: string;
  role?: "user" | "admin";
}

/** Credentials required for email/password login. */
export interface SignInCredentials {
  email: string;
  password: string;
}

/** Supported third-party OAuth providers. */
export type OAuthProvider = "google" | "facebook" | "github";

/** Options for initiating an OAuth sign-in flow. */
export interface OAuthSignInOptions {
  provider: OAuthProvider;
  /** URL to redirect to after auth completes (default: current page) */
  redirectTo?: string;
}

/** Fields that can be updated on the current user's profile. */
export interface UserUpdateData {
  fullName?: string;
  email?: string;
}

/** Successful message response returned by account action endpoints. */
export interface MessageResponse {
  message: string;
  error: null;
}

/** Failed message response returned by account action endpoints. */
export interface MessageErrorResponse {
  message: null;
  error: AuthError;
}

/** Discriminated union returned by password and verification actions. */
export type MessageResult = MessageResponse | MessageErrorResponse;

// ─── Responses ───────────────────────────────────────────────────────────────

/** Successful auth response containing a token pair and optional user. */
export interface AuthResponse {
  token: Token;
  user: User | null;
  error: null;
}

/** Structured error returned by auth operations. */
export interface AuthError {
  message: string;
  status: number;
}

/** Failed auth response — token and user are null, error is populated. */
export interface AuthErrorResponse {
  token: null;
  user: null;
  error: AuthError;
}

/** Discriminated union returned by sign-in, sign-up, and refresh operations. */
export type AuthResult = AuthResponse | AuthErrorResponse;

/** Successful user fetch/update response. */
export interface UserResponse {
  user: User;
  error: null;
}

/** Failed user fetch/update response. */
export interface UserErrorResponse {
  user: null;
  error: AuthError;
}

/** Discriminated union returned by getUser and updateUser operations. */
export type UserResult = UserResponse | UserErrorResponse;

// ─── Events ──────────────────────────────────────────────────────────────────

/**
 * Events emitted by `onAuthStateChange`.
 * - `SIGNED_IN` — user signed in (email/password or OAuth)
 * - `SIGNED_OUT` — user signed out or token expired
 * - `TOKEN_REFRESHED` — access token was silently refreshed
 * - `USER_UPDATED` — user profile was updated
 * - `INITIAL_SESSION` — first check on mount (token may be null)
 */
export type AuthChangeEvent =
  | "SIGNED_IN"
  | "SIGNED_OUT"
  | "TOKEN_REFRESHED"
  | "USER_UPDATED"
  | "INITIAL_SESSION";

/** Callback invoked when the auth state changes. */
export type AuthChangeCallback = (
  event: AuthChangeEvent,
  token: Token | null,
) => void;

/** Handle returned by `onAuthStateChange` to stop listening. */
export type Unsubscribe = { unsubscribe: () => void };

// ─── Client options ──────────────────────────────────────────────────────────

export interface AuthClientOptions {
  /** Backend API base URL (e.g. "http://localhost:3101") */
  apiUrl: string;
  /** API version prefix prepended to all routes (default: "/api/v1") */
  apiPrefix?: string;
  /** Storage key prefix (default: "<projectname>_auth") */
  storagePrefix?: string;
  /** Auto-refresh tokens before expiry (default: true) */
  autoRefresh?: boolean;
}
