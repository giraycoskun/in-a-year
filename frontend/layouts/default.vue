<template>
  <div class="min-h-screen flex flex-col bg-slate-900 text-slate-100">
    <header class="flex justify-between items-center px-8 py-4 bg-surface border-b border-white/10">
      <NuxtLink to="/" class="text-2xl font-bold">📊 In a Year</NuxtLink>
      <nav class="flex gap-6">
        <NuxtLink to="/" class="text-slate-400 hover:text-primary transition-colors">Home</NuxtLink>
        <NuxtLink to="/trakt" class="text-slate-400 hover:text-primary transition-colors">Trakt</NuxtLink>
      </nav>
    </header>
    <main class="flex-1 p-8 max-w-6xl mx-auto w-full">
      <slot />
    </main>
  </div>
</template>
