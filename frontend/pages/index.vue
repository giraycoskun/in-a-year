<template>
  <div class="text-center py-12">
    <h1 class="text-5xl font-bold mb-2">Welcome to In a Year</h1>
    <p class="text-slate-400 text-xl mb-12">Track your year in stats from your favorite services</p>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 max-w-3xl mx-auto">
      <NuxtLink
        to="/trakt"
        class="bg-surface rounded-xl p-8 text-center border border-transparent hover:border-primary hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/20 transition-all"
      >
        <span class="text-5xl block mb-4">🎬</span>
        <h2 class="text-xl font-semibold mb-2">Trakt</h2>
        <p class="text-slate-400 text-sm">Movies & TV shows you watched</p>
      </NuxtLink>
    </div>
  </div>
</template>
