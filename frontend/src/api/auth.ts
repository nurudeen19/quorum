import { apiFetch } from "./http";
import type {
  MessageResponse,
  RegisterResponse,
  TokenResponse,
  UserCreate,
  UserLogin,
} from "./types";

export async function register(body: UserCreate): Promise<RegisterResponse> {
  return apiFetch<RegisterResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
    skipAuth: true,
  });
}

export async function login(body: UserLogin): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
    skipAuth: true,
  });
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
    skipAuth: true,
  });
}

export async function logout(refreshToken: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export async function forgotPassword(email: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email }),
    skipAuth: true,
  });
}

export async function resetPassword(token: string, password: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ token, password }),
    skipAuth: true,
  });
}

export async function verifyEmail(token: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
    skipAuth: true,
  });
}
