import { api, showSnackbar } from "../api.js"
import { GalaxySection } from "../components/GalaxySection.js"
import { MapsPanel } from "../components/MapsPanel.js"
import { NavigationKeysPanel } from "../components/NavigationKeysPanel.js"
import { SpeedLimitsPanel } from "../components/SpeedLimitsPanel.js"
import { GalaxyTabs } from "../components/GalaxyTabs.js"
import { useTabRouting } from "../composables.js"

const TABS = {
  nav: "Destination",
  maps: "Maps",
  keys: "App Keys",
  speeds: "Speed Limits",
}

export const Navigation = {
  name: "Navigation",
  components: { GalaxySection, MapsPanel, NavigationKeysPanel, SpeedLimitsPanel, GalaxyTabs },
  data() {
    return { TABS, destination: "", favorites: [], navLoading: true }
  },
  setup() {
    return useTabRouting("/navigation", {
      nav: "", maps: "maps", keys: "keys", speeds: "speeds",
    })
  },
  mounted() { this.loadNavigation() },
  methods: {
    async loadNavigation() {
      this.navLoading = true
      try {
        const data = await api.getNavigation()
        this.destination = data?.destination || data?.name || ""
        this.favorites = Array.isArray(data?.favorites) ? data.favorites : []
      } catch (e) {
        this.favorites = []
      } finally {
        this.navLoading = false
      }
    },
    async setDestination() {
      if (!this.destination) return
      try {
        const payload = await api.setNavigation({ destination: this.destination })
        showSnackbar(payload?.message || "Destination set.")
      } catch (e) {
        showSnackbar(e?.message || "Failed to set destination.", "error")
      }
    },
  },
  template: `
    <div class="gx-view">
      <h2 style="margin-top:0;">Navigation & Maps</h2>

      <GalaxyTabs :items="TABS" :active="tab" @select="selectTab" />

      <template v-if="tab === 'nav'">
        <GalaxySection title="Navigation Destination" icon="bi-geo-alt-fill">
          <div style="padding: var(--sp-3); display:grid; gap:8px;">
            <input class="gx-field" v-model="destination" placeholder="Destination address or name" />
            <button type="button" class="gx-btn" @click="setDestination"><i class="bi bi-send"></i> Send to Device</button>
            <div v-if="favorites.length">
              <h4 style="margin:12px 0 8px;">Favorites</h4>
              <div v-for="fav in favorites" :key="fav.name" class="gx-row">
                <span class="gx-row__label">{{ fav.name }}</span>
                <button type="button" class="gx-btn gx-btn--tonal" @click="destination = fav.name; setDestination()">Use</button>
              </div>
            </div>
          </div>
        </GalaxySection>
      </template>

      <template v-if="tab === 'maps'">
        <MapsPanel />
      </template>

      <template v-if="tab === 'keys'">
        <NavigationKeysPanel />
      </template>

      <template v-if="tab === 'speeds'">
        <SpeedLimitsPanel />
      </template>
    </div>
  `,
}
