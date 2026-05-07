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
  <div class="wrap">
    <RouterLink to="/login" class="back">← Sign in</RouterLink>
    <AuthCard
      title="Forgot password"
      subtitle="We’ll email reset instructions if an account exists for that address."
    >
      <div v-if="sent" class="success">
        <p>If an account exists for that email, reset instructions were sent.</p>
        <RouterLink to="/login">Back to sign in</RouterLink>
      </div>
      <form v-else class="form" @submit.prevent="submit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="submit" :disabled="loading">
          {{ loading ? "Sending…" : "Send instructions" }}
        </button>
      </form>
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
}

.error {
  color: var(--color-danger);
  font-size: 0.9rem;
  margin: 0;
}

.success {
  text-align: center;
  color: var(--color-text-muted);
}

.success p {
  margin: 0 0 1rem;
}

.submit {
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #0a0e14;
  font-weight: 600;
}

.submit:disabled {
  opacity: 0.6;
}
</style>
