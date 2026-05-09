<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import * as authApi from "@/api/auth";
import { ApiError } from "@/api/http";

const email = ref("");
const error = ref("");
const sent = ref(false);
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await authApi.forgotPassword(email.value.trim());
    sent.value = true;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Request failed.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
    <div class="w-full max-w-md">
      <RouterLink to="/login" class="text-gray-400 hover:text-white mb-4 block">← Sign in</RouterLink>
      <AuthCard
        title="Forgot password"
        subtitle="We’ll email reset instructions if an account exists for that address."
      >
        <div v-if="sent" class="text-center">
          <p class="text-green-400 mb-4">
            If an account exists for that email, reset instructions were sent.
          </p>
          <RouterLink
            to="/login"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >Back to sign in</RouterLink
          >
        </div>
        <form v-else class="space-y-6" @submit.prevent="submit">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-300">Email</label>
            <input
              v-model="email"
              id="email"
              type="email"
              autocomplete="email"
              required
              class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
            />
          </div>
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ loading ? "Sending…" : "Send instructions" }}
          </button>
        </form>
      </AuthCard>
    </div>
  </div>
</template>
