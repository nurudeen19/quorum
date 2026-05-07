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
  <div class="wrap">
    <RouterLink to="/" class="back">← Home</RouterLink>
    <AuthCard
      title="Create account"
      subtitle="Matches POST /api/v1/auth/register — username and email must be unique."
    >
      <div v-if="successDetail" class="success">
        <p>{{ successDetail }}</p>
        <button type="button" class="submit" @click="goLogin">Go to sign in</button>
      </div>
      <form v-else class="form" @submit.prevent="submit">
        <label class="field">
          <span>Email</span>
          <input v-model="email" type="email" autocomplete="email" required />
        </label>
        <label class="field">
          <span>Username</span>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            required
            minlength="2"
          />
        </label>
        <label class="field">
          <span>Full name (optional)</span>
          <input v-model="fullName" type="text" autocomplete="name" />
        </label>
        <label class="field">
          <span>Password</span>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            minlength="8"
          />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="submit" :disabled="loading">
          {{ loading ? "Creating…" : "Register" }}
        </button>
      </form>
      <p v-if="!successDetail" class="footer-links">
        Already have an account?
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

.success {
  text-align: center;
}

.success p {
  color: var(--color-success);
  margin: 0 0 1rem;
}

.submit {
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: var(--color-accent);
  color: #0a0e14;
  font-weight: 600;
  width: 100%;
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
