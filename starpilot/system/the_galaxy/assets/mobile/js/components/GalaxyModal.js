export const GalaxyModal = {
  name: "GalaxyModal",
  props: {
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: "Are you sure?" },
    message: { type: String, default: "" },
    confirmLabel: { type: String, default: "Confirm" },
    cancelLabel: { type: String, default: "Cancel" },
    danger: { type: Boolean, default: false },
    sheet: { type: Boolean, default: true },
  },
  emits: ["update:modelValue", "confirm", "cancel"],
  methods: {
    close() { this.$emit("update:modelValue", false) },
    cancel() { this.close(); this.$emit("cancel") },
    confirm() { this.$emit("confirm"); this.close() },
  },
  template: `
    <transition name="gx-fade">
      <div v-if="modelValue" class="gx-scrim" @click.self="cancel">
        <transition name="gx-slide" appear>
          <div class="gx-sheet" role="dialog" :aria-label="title">
            <h3 class="gx-sheet__title">{{ title }}</h3>
            <p v-if="message" style="color: var(--text-muted); line-height: 1.5;">{{ message }}</p>
            <div class="gx-dialog__actions">
              <button type="button" class="gx-btn gx-btn--text" @click="cancel">{{ cancelLabel }}</button>
              <button type="button" class="gx-btn" :style="danger ? 'background: var(--error); color: var(--on-error);' : ''" @click="confirm">{{ confirmLabel }}</button>
            </div>
          </div>
        </transition>
      </div>
    </transition>
  `,
}

export function GalaxyConfirm({ title, message, confirmLabel = "Confirm", danger = false } = {}) {
  return new Promise((resolve) => {
    const host = document.createElement("div")
    document.body.appendChild(host)
    const { createApp, h } = window.__galaxyVue
    let app
    let settled = false
    const finish = (value) => {
      if (settled) return
      settled = true
      resolve(value)
      try { app?.unmount?.() } catch (e) {}
      host.remove()
    }
    app = createApp({
      render() {
        return h(GalaxyModal, {
          modelValue: true,
          title,
          message,
          confirmLabel,
          danger,
          "onUpdate:modelValue": (v) => { if (!v) finish(false) },
          onConfirm: () => finish(true),
          onCancel: () => finish(false),
        })
      },
    })
    app.mount(host)
  })
}
