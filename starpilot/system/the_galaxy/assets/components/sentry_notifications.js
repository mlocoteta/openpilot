const STORAGE_KEY = "starpilot.sentry.last-event"
const POLL_INTERVAL_MS = 5000

let started = false
let initialized = false

function lastSeenEventId() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || ""
  } catch {
    return ""
  }
}

function rememberEvent(eventId) {
  try {
    window.localStorage.setItem(STORAGE_KEY, eventId)
  } catch {
  }
}

async function pollSentryEvent() {
  try {
    const response = await fetch("/api/sentry/status", { cache: "no-store" })
    if (!response.ok) return
    const payload = await response.json()
    const event = payload?.lastEvent
    const eventId = String(event?.eventId || "")
    if (!eventId) return

    const previous = lastSeenEventId()
    rememberEvent(eventId)
    if (!initialized || eventId === previous) return
    if (typeof Notification === "undefined" || Notification.permission !== "granted") return

    new Notification("StarPilot Sentry Mode", {
      body: String(event.message || "Movement detected while parked."),
      tag: `starpilot-sentry-${eventId}`,
    })
  } catch (error) {
    console.debug("Sentry notification poll failed:", error)
  } finally {
    initialized = true
  }
}

export async function requestSentryNotificationPermission() {
  if (typeof Notification === "undefined") return "unsupported"
  return Notification.requestPermission()
}

export function startSentryNotifications() {
  if (started) return
  started = true
  pollSentryEvent()
  window.setInterval(pollSentryEvent, POLL_INTERVAL_MS)
}
