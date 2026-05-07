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
  <div class="wrap">
    <RouterLink to="/" class="back">← Home</RouterLink>
    <AuthCard title="Email verification">
      <p v-if="status === 'loading'" class="muted">Verifying…</p>
      <p v-else-if="status === 'ok'" class="ok">{{ message }}</p>
      <p v-else-if="status === 'err'" class="err">{{ message }}</p>
      <p class="footer-links">
        <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </AuthCard>
  </div>
</template>

<style scoped>
.wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.back {
  align-self: flex-start;
  margin-bottom: 1rem;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.muted {
  color: var(--color-text-muted);
}

.ok {
  color: var(--color-success);
}

.err {
  color: var(--color-danger);
}

.footer-links {
  margin-top: 1.25rem;
  font-size: 0.9rem;
}
</style>
