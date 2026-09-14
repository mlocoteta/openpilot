const SLUG_RE = /^[A-Za-z0-9]{16}$/

export const DevicePicker = {
  name: "DevicePicker",
  data() {
    return {
      devices: [],
      activeSlug: "",
      loading: true,
    }
  },
  computed: {
    hasMultipleDevices() { return this.devices.length > 1 },
  },
  methods: {
    async loadDevices() {
      try {
        const response = await fetch("/_gateway/devices", { cache: "no-store" })
        if (!response.ok) return
        const data = await response.json()
        this.activeSlug = SLUG_RE.test(data?.activeSlug || "") ? data.activeSlug : ""
        this.devices = Array.isArray(data?.devices)
          ? data.devices.filter((device) => SLUG_RE.test(device?.slug || "") && device?.path)
          : []
      } catch (error) {
        // Local Galaxy instances do not have the gateway directory endpoint.
      } finally {
        this.loading = false
      }
    },
    selectDevice(device) {
      if (!device?.path || device.slug === this.activeSlug) return
      window.location.assign(device.path)
    },
  },
  mounted() {
    this.loadDevices()
  },
  template: `
    <div v-if="!loading && hasMultipleDevices" class="gx-nav-section gx-device-picker">
      <div class="gx-nav-section__title">Commas</div>
      <a v-for="device in devices" :key="device.slug" class="gx-nav-item gx-device-picker__item"
        :class="{ active: device.slug === activeSlug }" :href="device.path"
        :aria-current="device.slug === activeSlug ? 'page' : undefined"
        @click.prevent="selectDevice(device)">
        <i class="bi bi-cpu"></i>
        <span class="gx-device-picker__name">{{ device.name }}</span>
        <span v-if="device.slug === activeSlug" class="gx-device-picker__current">Current</span>
      </a>
    </div>
  `,
}
