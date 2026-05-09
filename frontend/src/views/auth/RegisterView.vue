<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import { ApiError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const email = ref("");
const username = ref("");
const password = ref("");
const fullName = ref("");
const error = ref("");
const successDetail = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  successDetail.value = "";
  loading.value = true;
  try {
    const res = await auth.register({
      email: email.value.trim(),
      username: username.value.trim(),
      password: password.value,
      full_name: fullName.value.trim() || undefined,
    });
    successDetail.value = res.detail;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "Registration failed.";
  } finally {
    loading.value = false;
  }
}

function goLogin() {
  router.push({ name: "login" });
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
    <div class="w-full max-w-md">
      <RouterLink to="/" class="text-gray-400 hover:text-white mb-4 block">← Home</RouterLink>
      <AuthCard
        title="Create account"
        subtitle="Pick a username and email for your Quorum account. Each must be unique—we’ll tell you if either is already in use."
      >
        <div v-if="successDetail" class="text-center">
          <p class="text-green-400 mb-4">{{ successDetail }}</p>
          <button
            type="button"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            @click="goLogin"
          >
            Go to sign in
          </button>
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
          <div>
            <label for="username" class="block text-sm font-medium text-gray-300">Username</label>
            <input
              v-model="username"
              id="username"
              type="text"
              autocomplete="username"
              required
              minlength="2"
              class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
            />
          </div>
          <div>
            <label for="fullName" class="block text-sm font-medium text-gray-300"
              >Full name (optional)</label
            >
            <input
              v-model="fullName"
              id="fullName"
              type="text"
              autocomplete="name"
              class="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-gray-700 text-white"
            />
          </div>
          <div>
            <label for="password" class="block text-sm font-medium text-gray-300">Password</label>
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
          <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ loading ? "Creating…" : "Register" }}
          </button>
        </form>
        <p v-if="!successDetail" class="mt-6 text-center text-sm text-gray-400">
          Already have an account?
          <RouterLink to="/login" class="hover:text-white">Sign in</RouterLink>
        </p>
      </AuthCard>
    </div>
  </div>
</template>
