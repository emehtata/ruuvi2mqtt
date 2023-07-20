#  56 DD:17:F3:D7:86:CE pakastin
#  74 EA:D5:76:69:70:99 jääkaappi
# 104 EC:67:46:36:EA:60 sauna

import logging
import sys
from ruuvitag_sensor.ruuvi import RuuviTagSensor

logging.basicConfig(level=logging.DEBUG)

macs = [ sys.argv[1] ]
timeout_in_sec = 30

datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)

if sys.argv[1] in datas:
  print(datas[sys.argv[1]])
else:
  print("Data not received for "+sys.argv[1])
  sys.exit(1)

