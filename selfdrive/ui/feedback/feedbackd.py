#!/usr/bin/env python3
import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.micd import SAMPLE_RATE, SAMPLE_BUFFER

FEEDBACK_MAX_DURATION = 10.0
FEEDBACKD_SERVICES = ('rawAudioData', 'bookmarkButton', 'visionSpeedLimitBookmark')


def main():
  params_memory = Params(memory=True)
  pm = messaging.PubMaster(['userBookmark', 'audioFeedback'])
  sm = messaging.SubMaster(list(FEEDBACKD_SERVICES))
  should_record_audio = False
  block_num = 0
  last_wheel_bookmark_counter = params_memory.get_int("WheelButtonBookmarkCounter")

  while True:
    sm.update()
    bookmark_requests = 0

    if should_record_audio and sm.updated['rawAudioData']:
      raw_audio = sm['rawAudioData']
      msg = messaging.new_message('audioFeedback', valid=True)
      msg.audioFeedback.audio.data = raw_audio.data
      msg.audioFeedback.audio.sampleRate = raw_audio.sampleRate
      msg.audioFeedback.blockNum = block_num
      block_num += 1
      if (block_num * SAMPLE_BUFFER / SAMPLE_RATE) >= FEEDBACK_MAX_DURATION:
        bookmark_requests += 1  # send bookmark at end of audio segment
        should_record_audio = False
        cloudlog.info("10-second recording completed - stopping audio feedback")
      pm.send('audioFeedback', msg)

    if sm.updated['bookmarkButton']:
      cloudlog.info("Bookmark button pressed!")
      bookmark_requests += 1

    if sm.updated['visionSpeedLimitBookmark']:
      cloudlog.info("Vision speed limit bookmark requested!")
      bookmark_requests += 1

    wheel_bookmark_counter = params_memory.get_int("WheelButtonBookmarkCounter")
    if wheel_bookmark_counter > last_wheel_bookmark_counter:
      bookmark_requests += wheel_bookmark_counter - last_wheel_bookmark_counter
      last_wheel_bookmark_counter = wheel_bookmark_counter
      cloudlog.info("Wheel button bookmark requested!")

    for _ in range(bookmark_requests):
      msg = messaging.new_message('userBookmark', valid=True)
      pm.send('userBookmark', msg)


if __name__ == '__main__':
  main()
