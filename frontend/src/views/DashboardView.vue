<script setup lang="ts">
import { onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

onMounted(async () => {
  if (!auth.user && auth.isAuthenticated) {
    try {
      await auth.fetchUser();
    } catch {
      /* handled in store */
    }
  }
});

async function handleLogout() {
  await auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="flex min-h-screen bg-gray-900 text-white">
    <aside class="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      <div class="p-4 border-b border-gray-700">
        <div class="text-2xl font-bold">Quorum</div>
      </div>
      <nav class="flex-grow p-4">
        <a href="#" class="block py-2 px-4 rounded bg-gray-700 text-white">Dashboard</a>
      </nav>
      <div class="p-4 border-t border-gray-700">
        <button
          type="button"
          class="w-full text-left text-gray-400 hover:text-white"
          @click="handleLogout"
        >
          Sign out
        </button>
      </div>
    </aside>

    <div class="flex-grow flex flex-col">
      <header class="bg-gray-800 border-b border-gray-700 p-4">
        <h1 class="text-2xl font-bold">Dashboard</h1>
      </header>

      <main class="flex-grow p-6 space-y-6">
        <section class="bg-gray-800 rounded-lg p-6" v-if="auth.user">
          <h2 class="text-xl font-semibold mb-4">Account</h2>
          <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div>
              <dt class="text-sm font-medium text-gray-400">Username</dt>
              <dd class="mt-1 text-white">{{ auth.user.username }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-400">Email</dt>
              <dd class="mt-1 text-white">{{ auth.user.email }}</dd>
            </div>
            <div v-if="auth.user.full_name">
              <dt class="text-sm font-medium text-gray-400">Name</dt>
              <dd class="mt-1 text-white">{{ auth.user.full_name }}</dd>
            </div>
            <div>
              <dt class="text-sm font-medium text-gray-400">Email verified</dt>
              <dd class="mt-1 text-white">{{ auth.user.is_verified ? "Yes" : "No" }}</dd>
            </div>
          </dl>
        </section>

        <section class="bg-gray-800 rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">Briefings</h2>
          <p class="text-gray-400">
            Meeting briefings and chat will appear here once connected to the agent pipeline.
          </p>
          <RouterLink to="/" class="text-blue-500 hover:text-blue-400 mt-4 inline-block"
            >← Back to landing</RouterLink
          >
        </section>

        <p v-if="!auth.user && auth.isAuthenticated" class="text-gray-400">Loading profile…</p>
        <p v-else-if="!auth.isAuthenticated" class="text-red-500">
          Session expired.
          <RouterLink to="/login" class="text-blue-500 hover:text-blue-400"
            >Sign in again</RouterLink
          >
        </p>
      </main>
    </div>
  </div>
</template>
