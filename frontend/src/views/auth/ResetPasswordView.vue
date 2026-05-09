<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import * as authApi from "@/api/auth";
import { ApiError } from "@/api/http";

const route = useRoute();

const token = computed(() => (route.query.token as string) || "");
const password = ref("");
const password2 = ref("");
const error = ref("");
const done = ref(false);
const loading = ref(false);

async function submit() {
  error.value = "";
  if (password.value !== password2.value) {
    error.value = "Passwords do not match.";
    return;
  }
  if (!token.value) {
    error.value = "Missing reset token. Open the link from your email.";
    return;
  }
  loading.value = true;
  try {
    await authApi.resetPassword(token.value, password.value);
    done.value = true;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Reset failed.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
    <div class="w-full max-w-md">
      <RouterLink to="/login" class="text-gray-400 hover:text-white mb-4 block">← Sign in</RouterLink>
      <AuthCard title="Reset password" subtitle="Set a new password for your account.">
        <div v-if="done" class="text-center">
          <p class="text-green-400 mb-4">Password updated. You can sign in now.</p>
          <RouterLink
            to="/login"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >Sign in</RouterLink
          >
        </div>
        <form v-else class="space-y-6" @submit.prevent="submit">
          <p v-if="!token" class="text-yellow-400 text-sm">
            Add <code>?token=…</code> from your reset email.
          </p>
          <div>
            <label for="password" class="block text-sm font-medium text-gray-300"
              >New password</label
            >
            <input
              v-model="password"
              id="password"
              type="password"
              autocomplete="new-password"
              required
              minlength="8"
              class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
            />
          </div>
          <div>
            <label for="password2" class="block text-sm font-medium text-gray-300"
              >Confirm password</label
            >
            <input
              v-model="password2"
              id="password2"
              type="password"
              autocomplete="new-password"
              required
              minlength="8"
              class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
            />
          </div>
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          <button
            type="submit"
            :disabled="loading || !token"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ loading ? "Saving…" : "Update password" }}
          </button>
        </form>
      </AuthCard>
    </div>
  </div>
</template>
