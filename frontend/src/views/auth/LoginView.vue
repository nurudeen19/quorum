<script setup lang="ts">
import { ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AuthCard from "@/components/AuthCard.vue";
import { ApiError } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login({ email: email.value.trim(), password: password.value });
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
  <div class="wrap">
    <RouterLink to="/" class="back">← Home</RouterLink>
    <AuthCard title="Sign in" subtitle="Use the email and password for your Quorum account.">
      <form class="form" @submit.prevent="submit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label class="field">
          <span>Password</span>
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="submit" :disabled="loading">
          {{ loading ? "Signing in…" : "Sign in" }}
        </button>
      </form>
      <p class="footer-links">
        <RouterLink to="/forgot-password">Forgot password?</RouterLink>
        <span> · </span>
        <RouterLink to="/register">Create account</RouterLink>
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

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.field input {
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
}

.field input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2);
}

.error {
  color: var(--color-danger);
  font-size: 0.9rem;
  margin: 0;
}

.submit {
  margin-top: 0.25rem;
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #0a0e14;
  font-weight: 600;
}

.submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.footer-links {
  margin-top: 1.25rem;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  text-align: center;
}
</style>
