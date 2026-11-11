"""card.py feed for the Accord 9G cruise-hold brake deadband (opendbc/car/honda/cruise_brake_deadband.py).

Own SubMaster (longitudinalPlan, radarState, slcState) so card's main SubMaster checks are unchanged. Inputs older
than STALE_NS or invalid make the gate stock (set_plan(False)). Param AccordCruiseBrakeDeadband is re-read about
once a second.
"""
import time

from opendbc.car.honda import cruise_brake_deadband as cbd

PARAM = "AccordCruiseBrakeDeadband"
STALE_NS = 300_000_000
PARAM_INTERVAL = 100
REQUIRED = ('longitudinalPlan', 'radarState')


class CruiseBrakeFeed:
  def __init__(self, gate, params, sm=None):
    self.gate = gate
    self.params = params
    if sm is None:
      import openpilot.cereal.messaging as messaging
      sm = messaging.SubMaster(['longitudinalPlan', 'radarState', 'slcState'])
    self.sm = sm
    self.enabled = True
    self.frame = 0

  def _read_param(self):
    try:
      self.enabled = bool(self.params.get_bool(PARAM))
    except Exception:
      self.enabled = True

  def update(self, CS, now_ns=None):
    now_ns = time.monotonic_ns() if now_ns is None else now_ns
    if self.frame % PARAM_INTERVAL == 0:
      self._read_param()
    self.frame += 1
    try:
      self.sm.update(0)
      sm = self.sm
      fresh = all(sm.seen[s] and sm.valid[s] and sm.alive[s] and 0 <= now_ns - int(sm.logMonoTime[s]) <= STALE_NS
                  for s in REQUIRED)
      if not fresh or not self.enabled:
        self.gate.set_plan(False, enabled=self.enabled)
        return
      slc = sm['slcState'] if (sm.seen['slcState'] and sm.valid['slcState'] and
                               0 <= now_ns - int(sm.logMonoTime['slcState']) <= 1_000_000_000) else None
      inputs = cbd.plan_inputs(float(CS.vEgo), float(CS.vCruise), sm['longitudinalPlan'], sm['radarState'], slc)
      self.gate.set_plan(True, enabled=True, **inputs)
    except Exception:
      self.gate.set_plan(False, enabled=self.enabled)


def install(card):
  """Returns a feed for the Accord 9G pedal car, else None."""
  gate = getattr(card.CI.CC, 'cruise_brake_deadband', None)
  if gate is None or not cbd.eligible(card.CP):
    return None
  return CruiseBrakeFeed(gate, card.params)
