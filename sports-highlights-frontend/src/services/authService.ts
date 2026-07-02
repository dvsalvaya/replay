import { apiFetch, getAuthToken, setAuthToken } from "@/lib/api";
import type { LoginResponse } from "@/types";

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const data = await apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setAuthToken(data.access_token);
    return data;
  },

  logout(): void {
    setAuthToken(null);
  },

  getToken(): string | null {
    return getAuthToken();
  },
};
