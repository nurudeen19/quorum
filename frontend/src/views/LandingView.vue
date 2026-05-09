<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<template>
  <div class="bg-gray-900 text-white min-h-screen flex flex-col">
    <header class="flex justify-between items-center p-4 border-b border-gray-800">
      <div class="text-xl font-bold">Quorum</div>
      <nav class="flex items-center gap-4">
        <RouterLink to="/login" class="text-gray-400 hover:text-white">Sign in</RouterLink>
        <RouterLink to="/register" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Get started</RouterLink>
      </nav>
    </header>

    <main class="flex-grow flex flex-col items-center justify-center text-center p-4">
      <p class="text-blue-400 uppercase tracking-widest text-sm">Pre-meeting intelligence</p>
      <h1 class="text-4xl md:text-6xl font-bold my-4">
        Walk into every meeting
        <span class="text-blue-500">prepared</span>
      </h1>
      <p class="text-gray-400 max-w-2xl mx-auto mb-8">
        Quorum researches attendees and companies, synthesizes an executive briefing, and
        quality-checks the result—so you get a scannable memo before you walk through the door.
      </p>
      <div class="flex gap-4">
        <RouterLink to="/register" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg">Create an account</RouterLink>
        <RouterLink to="/login" class="text-gray-400 hover:text-white font-bold py-3 px-6 rounded-lg text-lg">I already have an account</RouterLink>
      </div>
    </main>

    <footer class="text-center p-4 border-t border-gray-800 text-gray-500">
      <span>Quorum</span>
      <span class="mx-2">·</span>
      <RouterLink to="/login" class="hover:text-white">Sign in</RouterLink>
    </footer>
  </div>
</template>
