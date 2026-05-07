import { defineStore } from "pinia";
import { computed, ref } from "vue";

import * as authApi from "@/api/auth";
import * as usersApi from "@/api/users";
import { ApiError } from "@/api/http";
import type { UserCreate, UserLogin, UserResponse } from "@/api/types";

const ACCESS_KEY = "quorum_access_token";
const REFRESH_KEY = "quorum_refresh_token";

export const useAuthStore = defineStore("auth", () => {
  const accessToken = ref<string | null>(localStorage.getItem(ACCESS_KEY));
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY));
  const user = ref<UserResponse | null>(null);
  const initialized = ref(false);

  const isAuthenticated = computed(() => !!accessToken.value);

  function persistTokens(access: string | null, refresh: string | null) {
    accessToken.value = access;
    refreshToken.value = refresh;
    if (access) localStorage.setItem(ACCESS_KEY, access);
    else localStorage.removeItem(ACCESS_KEY);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    else localStorage.removeItem(REFRESH_KEY);
  }

  async function fetchUser() {
    if (!accessToken.value) {
      user.value = null;
      return;
    }
    try {
      user.value = await usersApi.fetchCurrentUser();
    } catch (e) {
      if (e instanceof ApiError && e.status === 401 && refreshToken.value) {
        await tryRefresh();
        if (accessToken.value) {
          user.value = await usersApi.fetchCurrentUser();
          return;
        }
      }
      clearSession();
    }
  }

  async function tryRefresh(): Promise<boolean> {
    const rt = refreshToken.value;
    if (!rt) return false;
    try {
      const tokens = await authApi.refresh(rt);
      persistTokens(tokens.access_token, tokens.refresh_token);
      return true;
    } catch {
      clearSession();
      return false;
    }
  }

  function clearSession() {
    user.value = null;
    persistTokens(null, null);
  }

  async function initialize() {
    if (initialized.value) return;
    initialized.value = true;
    await fetchUser();
  }

  async function login(payload: UserLogin) {
    const tokens = await authApi.login(payload);
    persistTokens(tokens.access_token, tokens.refresh_token);
    await fetchUser();
  }

  async function register(payload: UserCreate) {
    return authApi.register(payload);
  }

  async function logout() {
    const rt = refreshToken.value;
    if (rt) {
      try {
        await authApi.logout(rt);
      } catch {
        /* still clear locally */
      }
    }
    clearSession();
  }

  return {
    accessToken,
    refreshToken,
    user,
    initialized,
    isAuthenticated,
    initialize,
    login,
    register,
    logout,
    fetchUser,
    tryRefresh,
    clearSession,
  };
});
