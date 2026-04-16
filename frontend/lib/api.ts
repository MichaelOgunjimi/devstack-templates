import type { AuthClient } from "./auth/client";

/**
 * Typed API client that auto-attaches JWT auth headers.
 *
 * ```ts
 * const api = createApiClient(authClient);
 * const musicians = await api.get<Musician[]>("/musicians");
 * await api.post("/bookings", { musicianId, date });
 * ```
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public body?: unknown,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

export function createApiClient(auth: AuthClient) {
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await auth.authFetch(path, init);

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new ApiError(
        res.status,
        (body as Record<string, string>).detail ??
          `Request failed: ${res.status}`,
        body,
      );
    }

    if (res.status === 204) return undefined as T;

    return res.json() as Promise<T>;
  }

  return {
    get<T>(path: string, init?: RequestInit): Promise<T> {
      return request<T>(path, { ...init, method: "GET" });
    },

    post<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return request<T>(path, {
        ...init,
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
    },

    put<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return request<T>(path, {
        ...init,
        method: "PUT",
        body: body ? JSON.stringify(body) : undefined,
      });
    },

    patch<T>(path: string, body?: unknown, init?: RequestInit): Promise<T> {
      return request<T>(path, {
        ...init,
        method: "PATCH",
        body: body ? JSON.stringify(body) : undefined,
      });
    },

    delete<T>(path: string, init?: RequestInit): Promise<T> {
      return request<T>(path, { ...init, method: "DELETE" });
    },
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
