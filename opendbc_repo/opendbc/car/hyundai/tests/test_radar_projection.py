import pytest

from opendbc.car.hyundai import radar_interface
from opendbc.car.hyundai.tests.test_dom_radar_complete_paths import CASES, bank, factory


@pytest.mark.parametrize('name,dbc,bus,start,count,length,lka', [case for case in CASES if 'mrr35' in case[1]])
def test_projected_radar_matches_complete_decoder(monkeypatch, name, dbc, bus, start, count, length, lka):
  cp = factory(name, bus, start, count, length, lka)
  projected = radar_interface.RadarInterface(cp)
  parser = radar_interface.CANParser

  def full_parser(*args, **kwargs):
    kwargs.pop('signals', None)
    return parser(*args, **kwargs)

  with monkeypatch.context() as patch:
    patch.setattr(radar_interface, 'CANParser', full_parser)
    full = radar_interface.RadarInterface(cp)
  assert sum(len(s.signals) for s in projected.rcp.message_states.values()) < sum(len(s.signals) for s in full.rcp.message_states.values())
  for index in range(24):
    frames = bank(dbc, bus, start, count, active=index % 4 != 3, counter=index)
    if index % 6 == 1:
      frames = [(a, d, 1 - b) for a, d, b in frames]
    elif index % 6 == 2:
      frames = frames[:-1]  # Missing trigger must not publish a fresh cycle.
    elif index % 6 == 3:
      frames = [(a, d[:-1], b) for a, d, b in frames]
    timestamp = 1_000_000_000 + index * 50_000_000
    sample = [(timestamp, frames)]
    assert repr(projected.update(sample)) == repr(full.update(sample))
    for addr, state in projected.rcp.message_states.items():
      reference = full.rcp.message_states[addr]
      assert (state.counter, state.counter_fail, list(state.timestamps)) == (reference.counter, reference.counter_fail, list(reference.timestamps))
      for sig in state.signals:
        assert projected.rcp.vl[addr][sig.name] == full.rcp.vl[addr][sig.name]
        assert projected.rcp.vl_all[addr][sig.name] == full.rcp.vl_all[addr][sig.name]
        assert projected.rcp.ts_nanos[addr][sig.name] == full.rcp.ts_nanos[addr][sig.name]
