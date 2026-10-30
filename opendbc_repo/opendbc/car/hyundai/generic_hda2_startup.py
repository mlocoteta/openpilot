from copy import deepcopy
from typing import Any
import time

from opendbc.car.hyundai.canfd_stock_aol import qualified as stock_qualified, qualified_long
from opendbc.car.hyundai.ecu_continuity import ContinuousECUStartup, StartupKeeper
from opendbc.car.hyundai.ecu_startup import Outcome, stock_copy
from opendbc.car.hyundai.radar_hda2_startup import RadarHDA2Startup
from opendbc.car.hyundai.values import CAR, HyundaiFlags, is_blended

CARS = frozenset((
  CAR.GENESIS_G80_2ND_GEN_FL,
  CAR.HYUNDAI_IONIQ_5_N,
  CAR.HYUNDAI_KONA_2ND_GEN,
  CAR.HYUNDAI_KONA_HEV_2ND_GEN,
  CAR.HYUNDAI_SANTA_CRUZ_1ST_GEN,
  CAR.HYUNDAI_SANTA_CRUZ_2025,
  CAR.HYUNDAI_SONATA_2024,
  CAR.HYUNDAI_SONATA_HEV_2024,
  CAR.HYUNDAI_STARIA_4TH_GEN,
  CAR.HYUNDAI_TUCSON_2025,
  CAR.HYUNDAI_TUCSON_4TH_GEN,
  CAR.HYUNDAI_TUCSON_HEV_2025,
  CAR.HYUNDAI_TUCSON_PHEV_2025,
  CAR.KIA_CARNIVAL_2025,
  CAR.KIA_CARNIVAL_HEV_4TH_GEN,
  CAR.KIA_K4_2025,
  CAR.KIA_K5_2025,
  CAR.KIA_K8_HEV_1ST_GEN,
  CAR.KIA_NIRO_EV_2ND_GEN,
  CAR.KIA_NIRO_HEV_2ND_GEN,
  CAR.KIA_SORENTO_2024,
  CAR.KIA_SPORTAGE_5TH_GEN,
))

EXISTING_OWNERS_OR_DISTINCT_RECEIVERS = frozenset((
  CAR.HYUNDAI_KONA_EV_2ND_GEN,
  CAR.HYUNDAI_IONIQ_5,
  CAR.HYUNDAI_IONIQ_6,
  CAR.KIA_EV6,
  CAR.GENESIS_GV70_ELECTRIFIED_1ST_GEN,
  CAR.GENESIS_GV60_EV_1ST_GEN,
  CAR.HYUNDAI_IONIQ_5_PE,
  CAR.KIA_EV9,
  CAR.KIA_SORENTO_4TH_GEN,
  CAR.KIA_SORENTO_HEV_4TH_GEN,
  CAR.KIA_CARNIVAL_4TH_GEN,
  CAR.GENESIS_GV70_1ST_GEN,
  CAR.GENESIS_GV80,
))

STOCK_WORDS = (0x10, 0x11, 0x12, 0x90, 0x91, 0x92)


def required(cp):
  # Unreviewed future ordinary ECU-disable profiles must fail before publication.
  return (cp.carFingerprint not in EXISTING_OWNERS_OR_DISTINCT_RECEIVERS and not is_blended(cp) and len(cp.safetyConfigs) == 1 and
          cp.openpilotLongitudinalControl and bool(cp.flags & HyundaiFlags.CANFD) and
          not cp.flags & (HyundaiFlags.CANFD_CAMERA_SCC | HyundaiFlags.CANFD_ANGLE_STEERING))


def qualified(cp):
  allowed = (HyundaiFlags.CANFD | HyundaiFlags.EV | HyundaiFlags.HYBRID | HyundaiFlags.CCNC |
             HyundaiFlags.CANFD_LKA_STEER_MSG | HyundaiFlags.CANFD_LKA_STEER_MSG_ALT |
             HyundaiFlags.CANFD_ALT_GEARS | HyundaiFlags.CANFD_ALT_GEARS_2)
  if not required(cp) or cp.carFingerprint not in CARS:
    return False
  factory = CAR(cp.carFingerprint)
  stock = stock_copy(cp)
  return (cp.alphaLongitudinalAvailable and cp.alternativeExperience == 0 and not cp.pcmCruise and
          bool(cp.flags & HyundaiFlags.CANFD_LKA_STEER_MSG) and not int(cp.flags) & ~int(allowed) and
          bool(cp.flags & HyundaiFlags.CCNC) == bool(factory.config.flags & HyundaiFlags.CCNC) and
          stock_qualified(stock) and stock.safetyConfigs[0].safetyParam in STOCK_WORDS and
          cp.safetyConfigs[0].safetyParam == (stock.safetyConfigs[0].safetyParam | 4 |
            (0x2000 if cp.carFingerprint in (CAR.KIA_CARNIVAL_2025, CAR.KIA_CARNIVAL_HEV_4TH_GEN) else 0)))


class GenericHDA2Startup(RadarHDA2Startup):
  def __init__(self, cp, callbacks, *, clock=time.monotonic, keeper_factory=StartupKeeper):
    if not qualified(cp):
      raise ValueError('Exact source-selected ordinary HDA-II LONG configuration required before publication')
    ContinuousECUStartup.__init__(self, cp, callbacks, address=0x730, bus=1,
                                  label='Ordinary HDA-II LONG', clock=clock, keeper_factory=keeper_factory)
    self.stock_cp = stock_copy(cp)

  def continuity_required(self):
    return required(self.cp)

  def finalize_aol_configuration(self, ci):
    if self.published or self.closed or ci is not self.ci or not self.ready:
      raise RuntimeError('Ordinary HDA-II finalization requires configured startup')
    if self.prepared_for(ci.CP):
      return
    long_aol = self.outcome is Outcome.SENT_UNCONFIRMED and qualified_long(ci.CP, marked_only=True)
    if not long_aol and (self.outcome not in (Outcome.STOCK_UNTOUCHED, Outcome.STOCK_RESTORED) or
                         not stock_qualified(ci.CP, marked_only=True)):
      raise RuntimeError('Ordinary HDA-II startup does not admit this AOL configuration')
    expected: Any = deepcopy(self.prepared_cp)
    configs = expected.get('safetyConfigs', [])
    allowed_words = tuple(word | 4 for word in STOCK_WORDS) if long_aol else STOCK_WORDS
    if (len(configs) != 1 or configs[0]['safetyModel'] != 'hyundaiCanfd' or
        configs[0]['safetyParam'] not in allowed_words or expected['alternativeExperience'] != 0):
      raise RuntimeError('Ordinary HDA-II prepared stock profile cannot be finalized')
    configs[0]['safetyParam'] |= 0x800
    if long_aol:
      expected['alternativeExperience'] = 32
    if ci.CP.to_dict() != expected:
      raise RuntimeError('Ordinary HDA-II finalization changed unrelated CarParams')
    self.prepared_cp = expected
