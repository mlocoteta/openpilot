"""One bounded Legacy AVH ON request; 0x32B is status, never a TX command."""

AVH_REQUEST = 0x6BB
AVH_STATUS = 0x32B
INPUTS = (AVH_REQUEST, AVH_STATUS, 0x40, 0x48, 0x13A, 0x174)


def checksum(address, data):
  return ((address & 0xFF) + (address >> 8) + sum(data[1:])) & 0xFF


def avh_request(template, step):
  if len(template) != 8 or checksum(AVH_REQUEST, template) != template[0] or template[2] & 3 or step not in (1, 2):
    raise ValueError("Invalid AVH template or counter step")
  data = bytearray(template)
  data[1] = (data[1] & 0xF0) | ((data[1] + step) & 0xF)
  data[2] |= 2
  data[0] = checksum(AVH_REQUEST, data)
  return AVH_REQUEST, bytes(data), 1


class AvhStartup:
  def __init__(self):
    self.started = None
    self.last_time = None
    self.stable_since = None
    self.frames = {}
    self.done = False
    self.followup = None

  def update(self, now, frames, enabled, can_valid, controls_active):
    if self.started is None:
      self.started = now
    if self.last_time is not None and now < self.last_time:
      self.done = True
    self.last_time = now
    if self.done:
      return []
    if now - self.started > 30 or controls_active:
      self.done = True
      return []

    for address, (timestamp, data) in frames.items():
      if address not in INPUTS or timestamp <= 0:
        continue
      previous = self.frames.get(address)
      if previous and timestamp == previous[0]:
        continue
      if len(data) != 8 or checksum(address, data) != data[0] or timestamp > now or (previous and timestamp < previous[0]):
        self.done = True
        return []
      if (address == AVH_REQUEST and data[2] & 3) or (address == AVH_STATUS and data[5] & 0x20) or \
         (address == 0x48 and data[3] != 4) or (address == 0x40 and data[4]) or \
         (address == 0x13A and any((int.from_bytes(data, 'little') >> bit) & 0x1FFF for bit in (12, 25, 38, 51))):
        self.done = True
        return []
      if previous and (data[1] & 15) == (previous[1][1] & 15):
        continue  # duplicate counters cannot refresh freshness
      # Controller snapshots can skip 50/100 Hz samples between updates. Panda
      # checks their full counter stream; require consecutive head-unit frames here.
      sequential = bool(previous and (address not in (AVH_REQUEST, AVH_STATUS) or
                                     (data[1] & 15) == ((previous[1][1] + 1) & 15)))
      self.frames[address] = (timestamp, data, sequential)

    fresh = all(a in self.frames and self.frames[a][2] and
                0 <= now - self.frames[a][0] <= (1.5 if a == AVH_REQUEST else 0.3) for a in INPUTS)
    if not enabled or not can_valid or not fresh:
      self.stable_since = None
      if self.followup is not None:
        self.done = True
      return []
    throttle = self.frames[0x40][1]
    rpm = int.from_bytes(throttle[2:4], 'little') & 0x1FFF
    if rpm < 400 or not self.frames[0x174][1][2] & 8:
      self.stable_since = None
      if self.followup is not None:
        self.done = True
      return []
    if self.stable_since is None:
      self.stable_since = now
    if self.followup is not None:
      sent, timestamp, template = self.followup
      if now - sent > 0.075 or self.frames[AVH_REQUEST][0] != timestamp:
        self.done = True
      elif now - sent >= 0.05:
        self.done = True
        return [avh_request(template, 2)]
      return []
    if now - self.started < 10 or now - self.stable_since < 3:
      return []
    timestamp, template, _ = self.frames[AVH_REQUEST]
    if now - timestamp > 0.010:
      return []
    self.followup = (now, timestamp, template)
    return [avh_request(template, 1)]
