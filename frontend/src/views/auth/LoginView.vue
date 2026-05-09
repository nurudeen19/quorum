<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import { ApiError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const login = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login({ login: login.value.trim(), password: password.value });
    const redirect = (route.query.redirect as string) || "/dashboard";
    router.push(redirect);
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Sign in failed.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
    <div class="w-full max-w-md">
      <RouterLink to="/" class="text-gray-400 hover:text-white mb-4 block">← Home</RouterLink>
      <AuthCard
        title="Sign in"
        subtitle="Use the email or username you registered with, plus your password."
      >
        <form class="space-y-6" @submit.prevent="submit">
          <div>
            <label for="login" class="block text-sm font-medium text-gray-300"
              >Email or username</label
            >
            <div class="mt-1">
              <input
                v-model="login"
                id="login"
                name="login"
                type="text"
                autocomplete="username"
                required
                placeholder="you@company.com or johndoe"
                class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-300">Password</label>
            <div class="mt-1">
              <input
                v-model="password"
                id="password"
                name="password"
                type="password"
                autocomplete="current-password"
                required
                class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
              />
            </div>
          </div>

          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>

          <div>
            <button
              type="submit"
              :disabled="loading"
              class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {{ loading ? "Signing in…" : "Sign in" }}
            </button>
          </div>
        </form>
        <p class="mt-6 text-center text-sm text-gray-400">
          <RouterLink to="/forgot-password" class="hover:text-white">Forgot password?</RouterLink>
          <span class="mx-2">·</span>
          <RouterLink to="/register" class="hover:text-white">Create account</RouterLink>
        </p>
      </AuthCard>
    </div>
  </div>
</template>
