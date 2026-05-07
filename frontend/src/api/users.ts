import { apiFetch } from "./http";
import type { UserResponse } from "./types";

export async function fetchCurrentUser(): Promise<UserResponse> {
  return apiFetch<UserResponse>("/users/me");
}
