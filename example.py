import logging
import pumpy

logging.basicConfig(level=logging.INFO)

chain = pumpy.Chain('/dev/tty.usbserial-FTWOFH91A')

p11 = pumpy.Pump(chain,address=1) 
p11.setdiameter(10)
p11.setflowrate(2000)
p11.settargetvolume(200)
p11.infuse()
p11.waituntiltarget()
p11.withdraw()
p11.waituntiltarget()

phd = pumpy.PHD2000(chain,address=4)
phd.setdiameter(24)
phd.setflowrate(600)
phd.infuse()
phd.stop()
phd.withdraw()
phd.stop()
phd.settargetvolume(100)
phd.infuse()
phd.waituntiltarget()

chain.close()