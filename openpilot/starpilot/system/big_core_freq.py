"""Onroad ceiling for the comma's big CPU cluster (cpufreq policy4, cores 4-7).

Upstream c01b8be968 ("set max cpu core frequency", #38132) writes scaling_max_freq = 1689600 for both
clusters whenever the device is not in power save. On the big cluster that is ~60% of its 2.8 GHz,
and card (pinned to core 4 with controlsd) runs out of headroom on the Accord 9G: carState drops
below 100 Hz and selfdrived reports lagging.

AccordBigCoreMaxKHz sets the big-cluster ceiling instead (little cluster keeps the upstream cap):
  0          -> upstream behaviour (1689600)
  otherwise  -> clamped to [1689600, 2803200] kHz; the kernel picks the highest table step at or below it.
scaling_max_freq is only the user ceiling: kernel thermal mitigation (cpufreq cooling / LMh) still
lowers the running frequency on heat, and hardwared's thermal status/fan/offroad handling is unchanged.
"""

PARAM = "AccordBigCoreMaxKHz"
UPSTREAM_MAX_KHZ = 1689600
BIG_CLUSTER_MAX_KHZ = 2803200


def big_core_max_khz(params=None) -> int:
  try:
    if params is None:
      from openpilot.common.params import Params
      params = Params()
    value = params.get(PARAM, return_default=True)
    khz = int(value) if value is not None else 0
  except Exception:
    # unknown key on an older build, unreadable param, bad type: never fail set_power_save
    return UPSTREAM_MAX_KHZ
  if khz <= 0:
    return UPSTREAM_MAX_KHZ
  return max(UPSTREAM_MAX_KHZ, min(khz, BIG_CLUSTER_MAX_KHZ))
