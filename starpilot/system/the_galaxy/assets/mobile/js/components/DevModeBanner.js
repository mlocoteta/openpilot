import { navigate } from "../store.js"

export const DevModeBanner = {
  name: "DevModeBanner",
  props: {
    hiddenCount: { type: Number, default: 0 },
    devModeOn: { type: Boolean, default: false },
  },
  computed: {
    visible() { return !this.devModeOn && this.hiddenCount > 0 },
  },
  methods: {
    unlock() { navigate("/settings/developer") },
  },
  template: `
    <div v-if="visible" class="gx-alert gx-alert--warn" role="status">
      <i class="bi bi-shield-lock gx-alert__icon"></i>
      <div class="gx-alert__body">
        <strong>{{ hiddenCount }} advanced setting{{ hiddenCount !== 1 ? "s" : "" }} hidden.</strong>
        <span>Advanced features are tucked away until you enable Developer Mode.</span>
      </div>
      <button type="button" class="gx-btn gx-btn--tonal" @click="unlock">Enable Developer Mode</button>
    </div>
  `,
}
