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
  <div class="wrap">
    <RouterLink to="/login" class="back">← Sign in</RouterLink>
    <AuthCard title="Reset password" subtitle="Set a new password for your account.">
      <div v-if="done" class="success">
        <p>Password updated. You can sign in now.</p>
        <RouterLink to="/login" class="btn">Sign in</RouterLink>
      </div>
      <form v-else class="form" @submit.prevent="submit">
        <p v-if="!token" class="warn">Add <code>?token=…</code> from your reset email.</p>
        <label class="field">
          <span>New password</span>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          />
        </label>
        <label class="field">
          <span>Confirm password</span>
          <input
            v-model="password2"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="submit" :disabled="loading || !token">
          {{ loading ? "Saving…" : "Update password" }}
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

.warn {
  color: var(--color-danger);
  font-size: 0.9rem;
}

.warn code {
  font-size: 0.85rem;
}

.error {
  color: var(--color-danger);
  font-size: 0.9rem;
  margin: 0;
}

.success {
  text-align: center;
}

.success p {
  color: var(--color-success);
  margin: 0 0 1rem;
}

.btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  background: var(--color-accent);
  color: #0a0e14;
  border-radius: 8px;
  font-weight: 600;
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
