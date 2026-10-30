// Translate presentation only: Vue's values, requests and technical identifiers stay in English.
const ATTRIBUTES = ["title", "aria-label", "placeholder", "alt"]
const PROTECTED = "script,style,code,pre,textarea,input,option,[contenteditable],[translate=no]"

export function translateText(source, messages) {
  const text = source.trim()
  return Object.hasOwn(messages, text) ? source.replace(text, () => messages[text]) : source
}

export function localizeDocument(root, { language, messages }, records = new WeakMap()) {
  function translate(node, key, source, write) {
    const saved = records.get(node) || {}
    const prior = saved[key]
    const original = prior && prior.output === source ? prior.source : source
    const output = translateText(original, messages)
    saved[key] = { source: original, output }
    records.set(node, saved)
    if (output !== source) write(output)
  }
  function visit(node) {
    if (node.nodeType === 3) {
      if (!node.parentElement?.closest(PROTECTED)) translate(node, "text", node.nodeValue, value => { node.nodeValue = value })
      return
    }
    if (node.nodeType !== 1 || node.matches("script,style,code,pre,[translate=no],[contenteditable]")) return
    for (const key of ATTRIBUTES) {
      if (node.hasAttribute(key)) translate(node, key, node.getAttribute(key), value => node.setAttribute(key, value))
    }
    if (!node.matches(PROTECTED)) for (const child of node.childNodes) visit(child)
  }
  visit(root)
  root.ownerDocument.documentElement.lang = language
  return records
}

export function startLocalization(root = document.body, fetcher = fetch) {
  let state = { language: "en", messages: {} }, stopped = false, timer, scheduled = false
  const records = new WeakMap()
  const dirty = new Set()
  const observer = new MutationObserver(mutations => {
    for (const mutation of mutations) dirty.add(mutation.target)
    if (scheduled) return
    scheduled = true
    queueMicrotask(() => {
      scheduled = false
      const changed = [...dirty].filter(node => node.isConnected)
      dirty.clear()
      if (!stopped) apply(changed)
    })
  })
  function apply(nodes = [root]) {
    observer.disconnect()
    for (const node of nodes) localizeDocument(node, state, records)
    observer.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRIBUTES })
  }
  async function refresh() {
    try {
      const response = await fetcher(`./api/localization?language=${encodeURIComponent(state.language)}`, { cache: "no-store" })
      if (response.ok) {
        const next = await response.json()
        if (!stopped && typeof next.language === "string" && next.messages && typeof next.messages === "object") {
          state = next
          apply()
        }
      }
    } catch { /* Keep the last confirmed language during connection loss. */ }
    if (!stopped) timer = setTimeout(refresh, 2000)
  }
  apply()
  refresh()
  return () => { stopped = true; clearTimeout(timer); observer.disconnect() }
}
