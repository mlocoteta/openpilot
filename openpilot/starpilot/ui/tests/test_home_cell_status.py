"""Accord: the StarPilot Home sidebar (what the 3X shows) draws the cell line under Wi-Fi/ETH."""
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

import pyray as rl

from openpilot.selfdrive.ui.lib.cell_status import CellStatus
from openpilot.starpilot.ui.presentation import BitmapFonts, Profile
from openpilot.starpilot.ui.shell import ShellMode
from openpilot.starpilot.ui.tests.test_runtime_snapshot import NOW, RuntimeSnapshotAdapter, ui_fake

LTE = {"connected": True, "registration": "home", "network_type": "lte", "signal_quality": 61, "sim": "ready"}
NO_LTE = {"state": "SEARCHING", "registration": "searching", "sim": "ready"}
NO_SIM = {"state": "INITIALIZING", "sim": "absent"}


def rgba(color):
  return tuple(color) if isinstance(color, tuple) else (color.r, color.g, color.b, color.a)


class Modem:
  def __init__(self, value):
    self.value, self.reads = value, 0

  def __call__(self):
    self.reads += 1
    return self.value


class HomeCellSnapshotTests(unittest.TestCase):
  def build(self, network_raw, modem, now_ns=NOW, adapter=None):
    ui = ui_fake()
    ui.started = False
    ui.sm['deviceState'].networkType = NS(raw=network_raw)
    adapter = adapter or RuntimeSnapshotAdapter(ui, modem_state=modem)
    return adapter, adapter.build(ShellMode.HOME, now_ns=now_ns).home

  def test_wifi_states(self):
    for modem, expected in ((LTE, CellStatus("cell", "LTE", 4)), (NO_LTE, CellStatus("no_cell", "No LTE", 0)),
                            (NO_SIM, CellStatus("no_sim", "No SIM", 0))):
      with self.subTest(expected=expected.label):
        self.assertEqual(self.build(1, Modem(modem))[1].cell, expected)

  def test_ethernet_gets_line(self):
    self.assertEqual(self.build(6, Modem(NO_SIM))[1].cell.label, "No SIM")

  def test_cell_primary_and_offline_unchanged_and_modem_not_read(self):
    for raw in (0, 2, 3, 4, 5):
      modem = Modem(LTE)
      with self.subTest(raw=raw):
        self.assertIsNone(self.build(raw, modem)[1].cell)
        self.assertEqual(modem.reads, 0)

  def test_modem_not_read_outside_home(self):
    modem = Modem(LTE)
    ui = ui_fake()
    adapter = RuntimeSnapshotAdapter(ui, modem_state=modem)
    adapter.build(ShellMode.ONROAD, now_ns=NOW)
    self.assertEqual(modem.reads, 0)

  def test_no_modem_output_draws_nothing(self):
    self.assertIsNone(self.build(1, Modem({}))[1].cell)

  def test_modem_errors_are_contained(self):
    def broken():
      raise OSError("gone")
    self.assertIsNone(self.build(1, broken)[1].cell)

  def test_modem_read_throttled_to_two_seconds(self):
    modem = Modem(NO_SIM)
    ticks = iter([NOW, NOW + 500_000_000, NOW + 1_900_000_000, NOW + 2_100_000_000] + [NOW + 2_100_000_000] * 50)
    ui = ui_fake()
    ui.started = False
    adapter = RuntimeSnapshotAdapter(ui, modem_state=modem)
    with patch('openpilot.starpilot.ui.runtime_snapshot.time.monotonic_ns', lambda: next(ticks)):
      for _ in range(4):
        adapter._cell_status("wifi")
    self.assertEqual(modem.reads, 2)


class HomeCellDrawTests(unittest.TestCase):
  def draw(self, cell):
    from openpilot.starpilot.ui.home import HomeView
    from openpilot.starpilot.ui.home_state import HomeMode, HomeState
    view = HomeView.__new__(HomeView)
    view.fonts = Mock(spec=BitmapFonts, profile=Profile.LARGE)
    state = HomeState(version="7", commit="", commit_date="", model_label="", description="", mode=HomeMode.CHILL,
                      experimental_enabled=False, experimental_available=True, stats=None, network="wifi",
                      network_strength=5, temperature_c=40., cell=cell)
    with patch.object(view, '_icon'), patch.object(view, '_text') as text, \
         patch.object(view, '_measure', return_value=NS(width=80, height=35)), \
         patch('openpilot.starpilot.ui.home.rl.draw_circle') as circle, \
         patch('openpilot.starpilot.ui.home.clip.begin_scissor_mode'), patch('openpilot.starpilot.ui.home.clip.end_scissor_mode'), \
         patch('openpilot.starpilot.ui.home.outside_rounded_border'), patch('openpilot.starpilot.ui.home.rl.draw_rectangle_rounded'):
      view._sidebar(state)
    return text.call_args_list, circle.call_args_list

  def test_lte_line_with_bars(self):
    texts, circles = self.draw(CellStatus("cell", "LTE", 3))
    self.assertEqual(texts[0].args[0], "Wi-Fi")
    self.assertEqual(texts[1].args[0], "+ LTE")
    self.assertGreater(texts[1].args[4], texts[0].args[4])  # below the Wi-Fi label
    small = [c for c in circles if c.args[2] == 7]
    self.assertEqual(len(small), 5)
    self.assertEqual(sum(rgba(c.args[3]) == rgba(rl.WHITE) for c in small), 3)

  def test_warning_lines_are_yellow(self):
    for label, kind in (("No LTE", "no_cell"), ("No SIM", "no_sim")):
      with self.subTest(label=label):
        texts, circles = self.draw(CellStatus(kind, label, 0))
        self.assertEqual(texts[1].args[0], label)
        self.assertEqual(rgba(texts[1].args[5]), (218, 202, 37, 255))
        self.assertEqual(len([c for c in circles if c.args[2] == 7]), 0)

  def test_no_cell_status_keeps_stock_sidebar(self):
    texts, _ = self.draw(None)
    self.assertEqual(texts[0].args[0], "Wi-Fi")
    self.assertEqual(texts[1].args[0], "TEMP")


if __name__ == "__main__":
  unittest.main()
