<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">🎬 Trakt</h1>

    <!-- User ID Input -->
    <div class="mb-6">
      <label class="block text-sm text-slate-400 mb-2">User ID</label>
      <input
        v-model="userId"
        type="text"
        placeholder="Enter your user ID"
        class="bg-slate-900 border border-white/20 rounded-lg px-4 py-2 text-white w-full max-w-xs focus:border-primary focus:outline-none"
      />
    </div>

    <!-- Auth Section -->
    <section class="bg-surface rounded-xl p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Authentication</h2>

      <div v-if="!isAuthenticated">
        <button
          @click="startAuth"
          :disabled="loading || !userId"
          class="bg-primary text-white rounded-lg px-6 py-2 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
        >
          {{ loading ? 'Loading...' : 'Connect Trakt Account' }}
        </button>

        <div v-if="deviceCode" class="mt-4 p-4 bg-slate-900 rounded-lg">
          <p class="mb-2">
            Go to
            <a :href="deviceCode.verification_url" target="_blank" class="text-primary hover:underline">
              {{ deviceCode.verification_url }}
            </a>
          </p>
          <p class="mb-4">
            Enter code: <strong class="text-2xl tracking-wider text-primary">{{ deviceCode.user_code }}</strong>
          </p>
          <button
            @click="pollForToken"
            :disabled="polling"
            class="bg-primary text-white rounded-lg px-6 py-2 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
          >
            {{ polling ? 'Waiting for authorization...' : "I've authorized" }}
          </button>
        </div>
      </div>

      <p v-else class="text-green-500 font-medium">✅ Connected to Trakt</p>
    </section>

    <!-- Sync Section -->
    <section v-if="isAuthenticated" class="bg-surface rounded-xl p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Sync History</h2>

      <div class="flex items-center gap-4 mb-4">
        <label class="text-sm text-slate-400">
          Year:
          <input
            v-model.number="syncYear"
            type="number"
            min="2000"
            max="2100"
            class="ml-2 bg-slate-900 border border-white/20 rounded-lg px-3 py-1.5 text-white w-24 focus:border-primary focus:outline-none"
          />
        </label>
        <button
          @click="syncHistory"
          :disabled="syncing"
          class="bg-primary text-white rounded-lg px-6 py-2 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
        >
          {{ syncing ? 'Syncing...' : 'Sync Year' }}
        </button>
      </div>

      <div v-if="syncTask" class="p-4 bg-slate-900 rounded-lg">
        <p class="text-sm text-slate-400">Task ID: {{ syncTask.task_id }}</p>
        <p class="font-medium">
          Status:
          <span :class="syncTask.status === 'SUCCESS' ? 'text-green-500' : 'text-yellow-500'">
            {{ syncTask.status }}
          </span>
        </p>
        <div v-if="syncTask.result" class="mt-2 text-sm">
          <p>Fetched: {{ syncTask.result.total_fetched }} entries</p>
          <p>New: {{ syncTask.result.new_entries }} entries</p>
        </div>
        <button
          v-if="syncTask.status === 'PENDING' || syncTask.status === 'STARTED'"
          @click="checkTaskStatus"
          class="mt-3 bg-slate-700 text-white rounded-lg px-4 py-1.5 text-sm hover:bg-slate-600 transition-colors"
        >
          Refresh Status
        </button>
      </div>
    </section>

    <!-- Stats Section -->
    <section v-if="isAuthenticated" class="bg-surface rounded-xl p-6 mb-6">
      <h2 class="text-xl font-semibold mb-4">Year Stats</h2>

      <div class="flex items-center gap-4 mb-4">
        <label class="text-sm text-slate-400">
          Year:
          <input
            v-model.number="statsYear"
            type="number"
            min="2000"
            max="2100"
            class="ml-2 bg-slate-900 border border-white/20 rounded-lg px-3 py-1.5 text-white w-24 focus:border-primary focus:outline-none"
          />
        </label>
        <button
          @click="fetchStats"
          :disabled="loadingStats"
          class="bg-primary text-white rounded-lg px-6 py-2 font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
        >
          {{ loadingStats ? 'Loading...' : 'Get Stats' }}
        </button>
      </div>

      <div v-if="stats" class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
        <div class="bg-slate-900 rounded-lg p-4 text-center">
          <h3 class="text-slate-400 text-sm mb-1">Movies</h3>
          <p class="text-4xl font-bold">{{ stats.movies.count }}</p>
          <p class="text-slate-400 text-sm">{{ stats.movies.total_hours }} hours</p>
        </div>
        <div class="bg-slate-900 rounded-lg p-4 text-center">
          <h3 class="text-slate-400 text-sm mb-1">Episodes</h3>
          <p class="text-4xl font-bold">{{ stats.episodes.count }}</p>
          <p class="text-slate-400 text-sm">{{ stats.episodes.total_hours }} hours</p>
          <p class="text-slate-400 text-sm">{{ stats.episodes.unique_shows }} shows</p>
        </div>
        <div class="bg-gradient-to-br from-primary to-purple-500 rounded-lg p-4 text-center">
          <h3 class="text-white/80 text-sm mb-1">Total Watch Time</h3>
          <p class="text-4xl font-bold">{{ stats.total.total_hours }}h</p>
          <p class="text-white/80 text-sm">{{ stats.total.count }} items watched</p>
        </div>
      </div>
    </section>

    <p v-if="error" class="text-red-500 mt-4">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
const { fetchApi } = useApi()

const userId = ref('')
const loading = ref(false)
const polling = ref(false)
const syncing = ref(false)
const loadingStats = ref(false)
const error = ref('')
const isAuthenticated = ref(false)
const deviceCode = ref<{ user_code: string; verification_url: string; device_code: string } | null>(null)
const syncYear = ref(new Date().getFullYear())
const statsYear = ref(new Date().getFullYear())
const syncTask = ref<{ task_id: string; status: string; result?: any } | null>(null)
const stats = ref<any>(null)

const checkAuthStatus = async () => {
  if (!userId.value) return
  try {
    const data = await fetchApi<{ authenticated: boolean }>(`/trakt/auth/status?user_id=${userId.value}`)
    isAuthenticated.value = data.authenticated
  } catch {
    isAuthenticated.value = false
  }
}

watch(userId, () => {
  if (userId.value) checkAuthStatus()
})

const startAuth = async () => {
  loading.value = true
  error.value = ''
  try {
    deviceCode.value = await fetchApi('/trakt/auth/device-code')
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const pollForToken = async () => {
  if (!deviceCode.value) return
  polling.value = true
  error.value = ''
  try {
    await fetchApi(`/trakt/auth/token?device_code=${deviceCode.value.device_code}&user_id=${userId.value}`, {
      method: 'POST',
    })
    isAuthenticated.value = true
    deviceCode.value = null
  } catch (e: any) {
    if (e.message.includes('pending')) {
      error.value = 'Still waiting for authorization...'
    } else {
      error.value = e.message
    }
  } finally {
    polling.value = false
  }
}

const syncHistory = async () => {
  syncing.value = true
  error.value = ''
  try {
    const data = await fetchApi<{ task_id: string }>(`/trakt/sync/year/${syncYear.value}?user_id=${userId.value}`, {
      method: 'POST',
    })
    syncTask.value = { task_id: data.task_id, status: 'STARTED' }
  } catch (e: any) {
    error.value = e.message
  } finally {
    syncing.value = false
  }
}

const checkTaskStatus = async () => {
  if (!syncTask.value) return
  try {
    const data = await fetchApi<{ status: string; result?: any }>(`/trakt/sync/status/${syncTask.value.task_id}`)
    syncTask.value = { ...syncTask.value, ...data }
  } catch (e: any) {
    error.value = e.message
  }
}

const fetchStats = async () => {
  loadingStats.value = true
  error.value = ''
  try {
    stats.value = await fetchApi(`/trakt/stats/${statsYear.value}?user_id=${userId.value}`)
  } catch (e: any) {
    error.value = e.message
  } finally {
    loadingStats.value = false
  }
}
</script>
