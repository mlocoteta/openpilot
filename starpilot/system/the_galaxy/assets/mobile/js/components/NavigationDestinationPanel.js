import { api, showSnackbar } from "../api.js"
import { getMapboxSearchContext, addRouteToMap, removeRouteFromMap } from "../../../components/navigation/navigation_utilities.js?v=nav-search-context-2"

const MAPBOX_STYLE = "mapbox://styles/frogsgomoo/cmcfv151j000o01rcdxebhl76"

let mapboxLoadPromise = null

function loadMapboxGL() {
  if (mapboxLoadPromise) return mapboxLoadPromise
  mapboxLoadPromise = new Promise((resolve, reject) => {
    if (window.mapboxgl) return resolve(window.mapboxgl)
    const link = document.createElement("link")
    link.rel = "stylesheet"
    link.href = "https://api.mapbox.com/mapbox-gl-js/v3.0.1/mapbox-gl.css"
    document.head.appendChild(link)
    const script = document.createElement("script")
    script.src = "https://api.mapbox.com/mapbox-gl-js/v3.0.1/mapbox-gl.js"
    script.onload = () => resolve(window.mapboxgl)
    script.onerror = () => reject(new Error("Failed to load Mapbox GL"))
    document.head.appendChild(script)
  })
  return mapboxLoadPromise
}

function number(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function coordinates(value) {
  if (Array.isArray(value) && value.length >= 2) {
    const longitude = number(value[0])
    const latitude = number(value[1])
    return longitude === null || latitude === null ? null : { longitude, latitude }
  }
  const latitude = number(value?.latitude)
  const longitude = number(value?.longitude)
  return latitude === null || longitude === null ? null : { latitude, longitude }
}

function parseJson(value, fallback) {
  if (Array.isArray(value)) return value
  if (typeof value !== "string" || !value.trim()) return fallback
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : fallback
  } catch (e) {
    return fallback
  }
}

function parseObject(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) return value
  if (typeof value !== "string" || !value.trim()) return null
  try {
    const parsed = JSON.parse(value)
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null
  } catch (e) {
    return null
  }
}

function labelFor(place) {
  return String(place?.full_address || place?.place_name || place?.name || place?.address || "").trim()
}

function secondaryLabel(place) {
  const primary = String(place?.name || place?.text || "").trim()
  const full = labelFor(place)
  return full && full.toLowerCase() !== primary.toLowerCase() ? full : ""
}

export const NavigationDestinationPanel = {
  name: "NavigationDestinationPanel",
  data() {
    return {
      loading: true,
      searching: false,
      loadingRoute: false,
      error: "",
      query: "",
      suggestions: [],
      recentDestinations: [],
      favorites: [],
      destination: null,
      mapboxPublic: "",
      language: "",
      lastPosition: null,
      map: null,
      mapReady: false,
      currentMarker: null,
      destinationMarker: null,
      searchTimer: null,
      searchRequest: 0,
      sessionToken: globalThis.crypto?.randomUUID?.() || Math.random().toString(36).slice(2),
    }
  },
  computed: {
    hasMapbox() { return !!this.mapboxPublic },
    recentPlaces() {
      const seen = new Set()
      return [...this.favorites, ...this.recentDestinations].filter((place) => {
        const coords = coordinates(place)
        const key = coords ? `${coords.latitude}:${coords.longitude}` : labelFor(place).toLowerCase()
        if (!key || seen.has(key)) return false
        seen.add(key)
        return true
      }).slice(0, 10)
    },
  },
  methods: {
    secondaryLabel,
  },
  async mounted() {
    await this.load()
  },
  beforeUnmount() {
    clearTimeout(this.searchTimer)
    if (this.map) {
      removeRouteFromMap(this.map)
      this.map.remove()
      this.map = null
    }
  },
  methods: {
    async load() {
      try {
        const [nav, favoritePayload] = await Promise.all([
          api.getNavigation(),
          api.getNavigationFavorites().catch(() => ({ favorites: [] })),
        ])
        this.mapboxPublic = String(nav?.mapboxPublic || "").trim()
        this.language = String(nav?.language || "").trim()
        this.lastPosition = coordinates(nav?.lastPosition)
        this.favorites = Array.isArray(favoritePayload?.favorites) ? favoritePayload.favorites : []
        this.recentDestinations = parseJson(nav?.previousDestinations, [])
        const saved = parseObject(nav?.destination)
        const savedDestination = coordinates(nav?.destination) || coordinates(saved)
        if (savedDestination) {
          const raw = saved || nav?.destination || {}
          this.destination = { ...raw, ...savedDestination, name: labelFor(raw) || "Current destination" }
          this.query = this.destination.name
        }
      } catch (e) {
        this.error = e?.message || "Failed to load navigation."
      } finally {
        this.loading = false
        if (this.hasMapbox) {
          await this.$nextTick()
          await this.setupMap()
        }
      }
    },
    async setupMap() {
      if (!this.hasMapbox || this.map || !this.$refs.map) return
      try {
        const mapboxgl = await loadMapboxGL()
        mapboxgl.accessToken = this.mapboxPublic
        const center = this.lastPosition || coordinates(this.destination) || { longitude: 0, latitude: 0 }
        this.map = new mapboxgl.Map({
          container: this.$refs.map,
          center: [center.longitude, center.latitude],
          zoom: this.lastPosition ? 15 : (this.destination ? 12 : 2),
          style: MAPBOX_STYLE,
          attributionControl: false,
          logoPosition: "bottom-right",
        })
        this.map.on("load", () => {
          this.mapReady = true
          if (this.lastPosition) this.currentMarker = new mapboxgl.Marker().setLngLat([this.lastPosition.longitude, this.lastPosition.latitude]).addTo(this.map)
          if (this.destination) this.previewDestination(this.destination)
        })
      } catch (e) {
        this.error = e?.message || "Failed to load the map."
      }
    },
    searchContext(query) {
      const context = getMapboxSearchContext(query, this.lastPosition, [this.language, ...(navigator.languages || [navigator.language])])
      if (this.lastPosition) context.proximity = `${this.lastPosition.longitude},${this.lastPosition.latitude}`
      return context
    },
    onInput(event) {
      this.destination = null
      this.searchRequest += 1
      this.searching = false
      this.error = ""
      clearTimeout(this.searchTimer)
      const rawValue = event?.target?.value ?? this.query
      this.query = String(rawValue)
      const value = this.query.trim()
      if (value.length < 3 || !this.hasMapbox) {
        this.suggestions = []
        return
      }
      this.searchTimer = setTimeout(() => this.search(value), 350)
    },
    async search(value) {
      const request = ++this.searchRequest
      this.searching = true
      try {
        const payload = await api.mapboxSuggest(value, this.mapboxPublic, this.sessionToken, this.searchContext(value))
        if (request === this.searchRequest) this.suggestions = Array.isArray(payload?.suggestions) ? payload.suggestions : []
      } catch (e) {
        if (request === this.searchRequest) this.error = e?.message || "Destination search failed."
      } finally {
        if (request === this.searchRequest) this.searching = false
      }
    },
    async resolvePlace(place) {
      const placeLabel = labelFor(place) || this.query.trim()
      let coords = coordinates(place?.geometry?.coordinates) || coordinates(place)
      if (!coords && place?.mapbox_id) {
        const payload = await api.mapboxRetrieve(place.mapbox_id, this.mapboxPublic, this.sessionToken)
        coords = coordinates(payload?.features?.[0]?.geometry?.coordinates)
      }
      if (!coords) {
        const payload = await api.mapboxGeocode(placeLabel, this.mapboxPublic, this.searchContext(placeLabel))
        coords = coordinates(payload?.features?.[0]?.geometry?.coordinates)
      }
      if (!coords) throw new Error("Could not determine that location.")
      return { ...coords, name: placeLabel, place_name: placeLabel }
    },
    async chooseSuggestion(place) {
      this.searching = true
      try {
        this.destination = await this.resolvePlace(place)
        this.query = this.destination.name
        this.suggestions = []
        await this.previewDestination(this.destination)
      } catch (e) {
        this.error = e?.message || "Could not determine that location."
        showSnackbar(this.error, "error")
      } finally {
        this.searching = false
      }
    },
    async resolveQuery() {
      const value = this.query.trim()
      if (!value) return null
      if (this.destination && this.destination.name === value) return this.destination
      return this.resolvePlace({ name: value })
    },
    async setDestination(place = null) {
      if (!this.hasMapbox) {
        showSnackbar("Add a Mapbox public key in App Keys first.", "error")
        return
      }
      this.loadingRoute = true
      try {
        this.destination = place || await this.resolveQuery()
        if (!this.destination) throw new Error("Enter a destination first.")
        await api.setNavigation(this.destination)
        this.query = this.destination.name
        this.suggestions = []
        await this.previewDestination(this.destination)
        showSnackbar("Destination set.")
      } catch (e) {
        this.error = e?.message || "Failed to set destination."
        showSnackbar(this.error, "error")
      } finally {
        this.loadingRoute = false
      }
    },
    async previewDestination(place) {
      if (!this.mapReady || !this.map || !place) return
      const mapboxgl = window.mapboxgl
      this.destinationMarker?.remove()
      this.destinationMarker = new mapboxgl.Marker({ color: "#9d72ff" }).setLngLat([place.longitude, place.latitude]).addTo(this.map)
      if (!this.lastPosition) {
        this.map.flyTo({ center: [place.longitude, place.latitude], zoom: 14 })
        return
      }
      try {
        const payload = await api.mapboxDirections(this.lastPosition, place, this.mapboxPublic)
        const routes = Array.isArray(payload?.routes) ? payload.routes : []
        if (routes.length) {
          removeRouteFromMap(this.map)
          addRouteToMap(this.map, routes, [this.lastPosition.longitude, this.lastPosition.latitude], [place.longitude, place.latitude], () => {}, true, () => "main")
        } else {
          this.map.fitBounds([[this.lastPosition.longitude, this.lastPosition.latitude], [place.longitude, place.latitude]], { padding: 80, duration: 500 })
        }
      } catch (e) {
        this.map.fitBounds([[this.lastPosition.longitude, this.lastPosition.latitude], [place.longitude, place.latitude]], { padding: 80, duration: 500 })
      }
    },
    usePlace(place) { this.chooseSuggestion(place) },
  },
  template: `
    <div style="display:grid; gap:12px;">
      <section class="gx-card">
        <div class="gx-section__header"><i class="bi bi-geo-alt-fill"></i><span class="gx-section__title">Navigation Destination</span></div>
        <div style="padding:var(--sp-3); display:grid; gap:8px;">
          <p v-if="!hasMapbox && !loading" class="gx-row__desc" style="margin:0;">Add a Mapbox public key in <a href="#/navigation/keys">App Keys</a> to search destinations and show the map.</p>
          <div style="display:flex; gap:8px;">
            <input class="gx-field" style="flex:1;" v-model="query" @input="onInput" @keyup.enter="setDestination()" placeholder="Search an address or place" autocomplete="off" />
            <button type="button" class="gx-btn" :disabled="loadingRoute || searching || !query.trim()" @click="setDestination()"><i class="bi bi-send"></i> {{ loadingRoute ? 'Setting...' : 'Send' }}</button>
          </div>
          <div v-if="searching" class="gx-row__desc">Searching...</div>
          <div v-if="suggestions.length" style="display:grid; gap:4px;">
            <button v-for="place in suggestions" :key="place.mapbox_id || place.id || place.name" type="button" class="gx-row" style="text-align:left; cursor:pointer;" @click="chooseSuggestion(place)">
              <span class="gx-row__info"><span class="gx-row__label">{{ place.name || place.text || place.place_name || 'Unnamed location' }}</span><span class="gx-row__desc">{{ secondaryLabel(place) }}</span></span>
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
          <div v-if="recentPlaces.length && !suggestions.length && !query" style="display:grid; gap:4px;">
            <div class="gx-row__desc">Recent and favorite destinations</div>
            <button v-for="place in recentPlaces" :key="place.id || place.name" type="button" class="gx-row" style="text-align:left; cursor:pointer;" @click="usePlace(place)">
              <span class="gx-row__info"><span class="gx-row__label">{{ place.name || place.place_name }}</span><span class="gx-row__desc">{{ secondaryLabel(place) }}</span></span>
              <i class="bi bi-clock-history"></i>
            </button>
          </div>
          <p v-if="error" class="gx-row__desc" style="color:var(--error); margin:0;">{{ error }}</p>
        </div>
      </section>
      <section class="gx-card" style="overflow:hidden;">
        <div v-if="loading || !hasMapbox" class="gx-loading" style="min-height:280px; display:grid; place-items:center;">{{ loading ? 'Loading navigation...' : 'Map unavailable until a Mapbox key is configured.' }}</div>
        <div v-else ref="map" style="height:380px; width:100%; min-height:280px;"></div>
      </section>
    </div>
  `,
}
