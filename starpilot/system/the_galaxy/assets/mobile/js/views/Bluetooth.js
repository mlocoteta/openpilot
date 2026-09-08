import { BluetoothPanel } from "../components/BluetoothPanel.js"
import { GalaxySection } from "../components/GalaxySection.js"

export const Bluetooth = {
  name: "Bluetooth",
  components: { BluetoothPanel, GalaxySection },
  template: `
    <div class="gx-view">
      <h2 style="margin-top:0;">Bluetooth</h2>
      <GalaxySection title="Bluetooth Devices" icon="bi-bluetooth" :collapsible="false">
        <BluetoothPanel />
      </GalaxySection>
    </div>
  `,
}
