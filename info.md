# Hoymiles MQTT Battery

Custom Home Assistant integration for Hoymiles MS-A2 and HiBattery AC MQTT battery data.

It creates clean battery sensors from existing MQTT topics and adds group sensors for multiple batteries, including combined state of charge, signed Power from/to Battery with negative discharge and positive charge, charge power, discharge power, daily charge energy, and daily discharge energy. Daily energy values are read from MQTT counters such as `chg_e` and `dchg_e` and may appear shortly after the first `quick/state` payload.
