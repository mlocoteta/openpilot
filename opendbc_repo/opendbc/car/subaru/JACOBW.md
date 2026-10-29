# jacobw Subaru angle adapter

The explicit `jacobw_angle.py` adapter integrates the Crosstrek angle work from
[Jacob Waller's jul-angle-based fork](https://github.com/jacobwaller/opendbc/tree/8acbeccdab45a47aa7af170d2d17b61f0eb5e4f0).
Jacob integrated the implementation and corrected the VehicleModel limit type.
The low-speed filter comes from lukasloetkolben, and target-before-jerk limiting
from elkoled. Original source authors and titles remain in `ORIGIN_HISTORY.tsv`.

Only `SUBARU_CROSSTREK_2025` selects this adapter, including the Impreza vehicles
identified by that profile. It adds the upstream 6-to-3 degree low-speed
deadzone below 10 m/s, clips the target before jerk limiting, and retains the
190 degree EPS bound. A small native header mirrors that bound for this exact
VM profile. Other Subaru profiles and the shared lateral helper are unchanged.

StarPilot retains its matched platform vehicle model, the stricter 1 degree
per-command rate instead of upstream's 5, and all existing driver handoff,
MAIN/gear/stop/fault, source-health and AOL permission guards. An impossible
intersection of acceleration and jerk limits withdraws the steering request
and follows bounded measured angle; it cannot relax native limits. Neither
Alpha LONG nor initial AOL arming policy changes.

This is a StarPilot adaptation, not byte-for-byte upstream tuning. The original
project/opendbc MIT notices and the root source credits apply.
