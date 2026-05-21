export { AuthClient } from "./client";
export { AuthProvider, AuthContext, type AuthContextValue } from "./provider";
export { useAuth, useUser, useToken } from "./hooks";

export type {
  User,
  Token,
  AuthState,
  SignUpCredentials,
  SignInCredentials,
  OAuthProvider,
  OAuthSignInOptions,
  UserUpdateData,
  MessageResponse,
  MessageErrorResponse,
  MessageResult,
  AuthResponse,
  AuthError,
  AuthErrorResponse,
  AuthResult,
  UserResponse,
  UserErrorResponse,
  UserResult,
  AuthChangeEvent,
  AuthChangeCallback,
  AuthClientOptions,
  Unsubscribe,
} from "./types";
