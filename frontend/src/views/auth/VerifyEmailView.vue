<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import * as authApi from "@/api/auth";
import { ApiError } from "@/api/http";

const route = useRoute();
const status = ref<"idle" | "loading" | "ok" | "err">("idle");
const message = ref("");

onMounted(async () => {
  const token = (route.query.token as string) || "";
  if (!token) {
    status.value = "err";
    message.value = "Missing token. Use the link from your verification email.";
    return;
  }
  status.value = "loading";
  try {
    const res = await authApi.verifyEmail(token);
    status.value = "ok";
    message.value = res.detail;
  } catch (e) {
    status.value = "err";
    message.value = e instanceof ApiError ? e.message : "Verification failed.";
  }
});
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
    <div class="w-full max-w-md">
      <RouterLink to="/" class="text-gray-400 hover:text-white mb-4 block">← Home</RouterLink>
      <AuthCard title="Email verification">
        <div class="text-center">
          <p v-if="status === 'loading'" class="text-gray-400">Verifying…</p>
          <p v-else-if="status === 'ok'" class="text-green-400">{{ message }}</p>
          <p v-else-if="status === 'err'" class="text-red-500">{{ message }}</p>
          <p class="mt-6">
            <RouterLink
              to="/login"
              class="text-blue-500 hover:text-blue-400"
              >Sign in</RouterLink
            >
          </p>
        </div>
      </AuthCard>
    </div>
  </div>
</template>
