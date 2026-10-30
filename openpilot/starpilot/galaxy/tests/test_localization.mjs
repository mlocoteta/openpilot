import assert from "node:assert/strict"
import { translateText, localizeDocument } from "../web/js/localization.js"

assert.equal(translateText("  Home\n", { Home: "ホーム" }), "  ホーム\n")
assert.equal(translateText("SpeedLimitController", {}), "SpeedLimitController")
assert.equal(translateText("Save", { Save: "$&<text>" }), "$&<text>", "translations remain literal text")

const doc = { documentElement: {} }
class Element {
  constructor(tag, attrs = {}, children = []) {
    this.nodeType = 1; this.tag = tag; this.attrs = { ...attrs }; this.childNodes = children; this.ownerDocument = doc
    for (const child of children) child.parentElement = this
  }
  matches(selector) {
    return selector.split(",").some(value => value.startsWith("[") ?
      value === "[translate=no]" ? this.attrs.translate === "no" : Object.hasOwn(this.attrs, value.slice(1, -1)) : this.tag === value)
  }
  closest(selector) { return this.matches(selector) || this.parentElement?.closest(selector) }
  hasAttribute(key) { return Object.hasOwn(this.attrs, key) }
  getAttribute(key) { return this.attrs[key] }
  setAttribute(key, value) { this.attrs[key] = value }
}
const text = value => ({ nodeType: 3, nodeValue: value })
const label = text("Home"), dynamic = text("Save"), technical = text("Save")
const input = new Element("input", { placeholder: "Search", value: "Home" })
const root = new Element("main", {}, [new Element("button", { title: "Home" }, [label]),
  new Element("span", {}, [dynamic]), new Element("code", {}, [technical]), input,
  new Element("span", { translate: "no" }, [text("Save")])])
const records = new WeakMap()
localizeDocument(root, { language: "ja", messages: { Home: "ホーム", Save: "保存", Search: "検索" } }, records)
assert.equal(label.nodeValue, "ホーム")
assert.equal(input.attrs.placeholder, "検索")
assert.equal(input.attrs.value, "Home")
assert.equal(technical.nodeValue, "Save")
assert.equal(doc.documentElement.lang, "ja")
dynamic.nodeValue = "Home" // Vue changed the source while another language was active.
localizeDocument(root, { language: "fr", messages: { Home: "Accueil", Save: "Enregistrer", Search: "Rechercher" } }, records)
assert.equal(label.nodeValue, "Accueil")
assert.equal(dynamic.nodeValue, "Accueil")
localizeDocument(root, { language: "en", messages: {} }, records)
assert.equal(label.nodeValue, "Home")
assert.equal(dynamic.nodeValue, "Home")
assert.equal(input.attrs.placeholder, "Search")
assert.equal(root.childNodes[0].attrs.title, "Home")
