<script setup lang="ts">
import { onMounted } from "vue";
import { RouterLink } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

onMounted(async () => {
  await auth.initialize();
});

const features = [
  {
    title: "When the invite lands at the last minute",
    body:
      "You only have names, titles, and a company—Quorum still builds a usable picture so you are not walking in cold.",
  },
  {
    title: "Minutes of reading, not hours of tabs",
    body:
      "Skip the spiral of LinkedIn, news, and random PDFs. Get a tight brief you can skim before you join the call.",
  },
  {
    title: "Context without the homework",
    body:
      "Enough background to open confidently, spot obvious landmines, and ask smarter questions—without pretending you did a full dossier.",
  },
];

const steps = [
  {
    step: "01",
    title: "Drop in what you know",
    body: "Names, companies, and the outcome you need—even if that is all you have five minutes before the meeting.",
  },
  {
    step: "02",
    title: "Quorum fills the gaps",
    body: "We pull public context on people and organizations and turn it into a clear pre-meeting memo.",
  },
  {
    step: "03",
    title: "Join with confidence",
    body: "Walk in with a little situational awareness instead of being blindsided—then refine with follow-ups in chat if you need more.",
  },
];
</script>

<template>
  <div
    class="min-h-screen flex flex-col text-slate-100 bg-slate-950 selection:bg-cyan-500/30 selection:text-cyan-50"
  >
    <!-- ambient -->
    <div
      class="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      aria-hidden="true"
    >
      <div
        class="absolute -top-1/2 left-1/2 h-[120%] w-[140%] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.14),transparent_55%)]"
      />
      <div
        class="absolute top-1/3 right-0 h-[60%] w-[50%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(139,92,246,0.08),transparent_60%)]"
      />
      <div
        class="absolute bottom-0 left-0 h-[45%] w-[55%] rounded-full bg-[radial-gradient(ellipse_at_center,rgba(15,23,42,0.9),transparent_70%)]"
      />
    </div>

    <header
      class="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-md"
    >
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <RouterLink
          to="/"
          class="landing-display text-xl font-bold tracking-tight text-white hover:text-cyan-200/90 transition-colors"
        >
          Quorum
        </RouterLink>
        <nav class="flex items-center gap-3 sm:gap-6">
          <template v-if="auth.isAuthenticated">
            <RouterLink
              to="/dashboard"
              class="landing-nav-muted text-sm font-medium transition-colors hover:text-white"
            >
              Dashboard
            </RouterLink>
            <RouterLink
              to="/chat"
              class="landing-cta-accent landing-display rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-4 py-2 text-sm font-semibold shadow-lg shadow-cyan-500/25 transition hover:from-cyan-300 hover:to-sky-300 hover:shadow-cyan-500/35"
            >
              Open briefing chat
            </RouterLink>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="landing-nav-muted text-sm font-medium transition-colors hover:text-white"
            >
              Sign in
            </RouterLink>
            <RouterLink
              to="/register"
              class="landing-cta-accent landing-display rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-4 py-2 text-sm font-semibold shadow-lg shadow-cyan-500/25 transition hover:from-cyan-300 hover:to-sky-300 hover:shadow-cyan-500/35"
            >
              Get started
            </RouterLink>
          </template>
        </nav>
      </div>
    </header>

    <main class="flex-1">
      <!-- Hero -->
      <section class="mx-auto max-w-6xl px-4 pb-20 pt-16 sm:px-6 sm:pt-24 md:pb-28">
        <div class="mx-auto max-w-3xl text-center">
          <p
            class="landing-display mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-500/25 bg-cyan-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300/95"
          >
            Pre-meeting intelligence
          </p>
          <h1
            class="landing-display text-4xl font-bold leading-[1.08] tracking-tight text-white sm:text-5xl md:text-6xl lg:text-[3.5rem]"
          >
            Short-notice meeting?
            <span
              class="bg-gradient-to-r from-cyan-300 via-sky-400 to-violet-400 bg-clip-text text-transparent"
            >
              Still show up informed.
            </span>
          </h1>
          <p
            class="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-400 sm:text-xl"
          >
            Calendar packed, zero prep time, and all you have is a name and a company? Quorum
            gathers the public context for you—so you walk in with confidence and a little
            grounding instead of hoping nobody asks a question you cannot answer.
          </p>
          <div
            class="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row sm:gap-5"
          >
            <RouterLink
              v-if="auth.isAuthenticated"
              to="/dashboard"
              class="landing-cta-on-light landing-display w-full rounded-full bg-white px-8 py-3.5 text-center text-base font-semibold shadow-xl shadow-slate-900/40 transition hover:bg-slate-100 sm:w-auto"
            >
              Go to dashboard
            </RouterLink>
            <RouterLink
              v-else
              to="/register"
              class="landing-cta-on-light landing-display w-full rounded-full bg-white px-8 py-3.5 text-center text-base font-semibold shadow-xl shadow-slate-900/40 transition hover:bg-slate-100 sm:w-auto"
            >
              Create free account
            </RouterLink>
            <RouterLink
              v-if="auth.isAuthenticated"
              to="/chat"
              class="landing-cta-ghost w-full rounded-full border border-slate-600 bg-slate-900/40 px-8 py-3.5 text-center text-base font-semibold backdrop-blur-sm transition hover:border-slate-500 hover:bg-slate-800/60 sm:w-auto"
            >
              Open briefing chat
            </RouterLink>
            <RouterLink
              v-else
              to="/login"
              class="landing-cta-ghost w-full rounded-full border border-slate-600 bg-slate-900/40 px-8 py-3.5 text-center text-base font-semibold backdrop-blur-sm transition hover:border-slate-500 hover:bg-slate-800/60 sm:w-auto"
            >
              I already have an account
            </RouterLink>
          </div>
          <p class="mt-8 text-sm text-slate-500">
            For back-to-back days, surprise invites, and anyone who refuses to spend an evening
            researching someone they will meet for twenty minutes.
          </p>
        </div>
      </section>

      <!-- Features -->
      <section
        class="border-y border-slate-800/80 bg-slate-900/30 py-20 backdrop-blur-sm"
      >
        <div class="mx-auto max-w-6xl px-4 sm:px-6">
          <div class="mx-auto max-w-2xl text-center">
            <h2 class="landing-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Built for “I need this in ten minutes”
            </h2>
            <p class="mt-3 text-slate-400">
              Turn a thin invite into enough context to hold your own—without the guilt of doing
              nothing or the grind of doing everything by hand.
            </p>
          </div>
          <ul
            class="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 lg:gap-8"
          >
            <li
              v-for="(f, i) in features"
              :key="i"
              class="group rounded-2xl border border-slate-800 bg-slate-950/60 p-6 shadow-lg shadow-black/20 transition hover:border-cyan-500/30 hover:bg-slate-900/80"
            >
              <div
                class="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 text-sm font-bold text-cyan-400"
              >
                {{ i + 1 }}
              </div>
              <h3 class="landing-display text-lg font-semibold text-white">
                {{ f.title }}
              </h3>
              <p class="mt-2 text-sm leading-relaxed text-slate-400">
                {{ f.body }}
              </p>
            </li>
          </ul>
        </div>
      </section>

      <!-- How it works -->
      <section class="mx-auto max-w-6xl px-4 py-20 sm:px-6 md:py-28">
        <div class="mx-auto max-w-2xl text-center">
          <h2 class="landing-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
            How it works
          </h2>
          <p class="mt-3 text-slate-400">
            From “I barely know who these people are” to “I know enough to steer the room.”
          </p>
        </div>
        <ol
          class="mt-14 grid gap-8 md:grid-cols-3 md:gap-6"
        >
          <li
            v-for="s in steps"
            :key="s.step"
            class="relative rounded-2xl border border-slate-800/90 bg-gradient-to-b from-slate-900/80 to-slate-950/80 p-6 pt-10"
          >
            <span
              class="landing-display absolute -top-3 left-6 rounded-md bg-slate-950 px-2 py-0.5 text-xs font-bold tracking-wider text-cyan-400 ring-1 ring-cyan-500/40"
            >
              {{ s.step }}
            </span>
            <h3 class="landing-display text-lg font-semibold text-white">
              {{ s.title }}
            </h3>
            <p class="mt-2 text-sm leading-relaxed text-slate-400">
              {{ s.body }}
            </p>
          </li>
        </ol>
      </section>

      <!-- CTA band -->
      <section class="border-t border-slate-800 bg-gradient-to-b from-slate-900/50 to-slate-950 py-20">
        <div class="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 class="landing-display text-2xl font-bold text-white sm:text-3xl">
            Next meeting moved up—and you are out of prep time?
          </h2>
          <p class="mt-4 text-slate-400">
            Get a pre-meeting brief that respects your schedule: quick to read, grounded in public
            facts, and focused on what helps you sound sharp when the call starts.
          </p>
          <RouterLink
            v-if="auth.isAuthenticated"
            to="/chat"
            class="landing-cta-accent landing-display mt-8 inline-flex rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-10 py-3.5 text-base font-semibold shadow-lg shadow-cyan-500/25 transition hover:from-cyan-300 hover:to-sky-300"
          >
            Open briefing chat
          </RouterLink>
          <RouterLink
            v-else
            to="/register"
            class="landing-cta-accent landing-display mt-8 inline-flex rounded-full bg-gradient-to-r from-cyan-400 to-sky-400 px-10 py-3.5 text-base font-semibold shadow-lg shadow-cyan-500/25 transition hover:from-cyan-300 hover:to-sky-300"
          >
            Get started free
          </RouterLink>
        </div>
      </section>
    </main>

    <footer class="border-t border-slate-800 bg-slate-950 py-10">
      <div
        class="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-4 sm:flex-row sm:px-6"
      >
        <div class="text-center sm:text-left">
          <div class="landing-display font-bold text-white">Quorum</div>
          <p class="mt-1 text-sm text-slate-500">
            Context for the meetings you cannot fully prepare for.
          </p>
        </div>
        <div class="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
          <template v-if="auth.isAuthenticated">
            <RouterLink to="/dashboard" class="landing-footer-link transition hover:text-cyan-400"
              >Dashboard</RouterLink
            >
            <RouterLink to="/chat" class="landing-footer-link transition hover:text-cyan-400"
              >Briefing chat</RouterLink
            >
          </template>
          <template v-else>
            <RouterLink to="/login" class="landing-footer-link transition hover:text-cyan-400"
              >Sign in</RouterLink
            >
            <RouterLink to="/register" class="landing-footer-link transition hover:text-cyan-400"
              >Create account</RouterLink
            >
          </template>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing-display {
  font-family: "Outfit", "DM Sans", system-ui, sans-serif;
}

/*
 * Global `a` / `a:hover` in base.css use --color-accent and can override Tailwind on RouterLink.
 * Force readable CTA and nav colors.
 */
.landing-cta-accent {
  color: #020617 !important;
}
.landing-cta-accent:hover {
  color: #020617 !important;
}

.landing-cta-on-light {
  color: #020617 !important;
}
.landing-cta-on-light:hover {
  color: #020617 !important;
}

.landing-cta-ghost {
  color: #e2e8f0 !important;
}
.landing-cta-ghost:hover {
  color: #f8fafc !important;
}

.landing-nav-muted {
  color: #94a3b8 !important;
}
.landing-nav-muted:hover {
  color: #f8fafc !important;
}

.landing-footer-link {
  color: #64748b !important;
}
.landing-footer-link:hover {
  color: #22d3ee !important;
}
</style>
