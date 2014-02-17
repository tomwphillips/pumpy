import pumpy

# Pump 11
p11 = pumpy.Pump('/dev/tty.usbserial-FTWOFH91A',address=1,verbose=True)
p11.setdiameter(25)
p11.setflowrate(2000)
p11.settargetvolume(200)
p11.infuse()
p11.waituntiltarget()
p11.withdraw()
p11.waituntiltarget()

# PHD2000
phd = pumpy.PHD2000('/dev/tty.usbserial-FTWOFH91A',address=2,verbose=True)
phd.setdiameter(12)
phd.setflowrate(600)
phd.settargetvolume(50)
phd.infuse()
phd.waituntiltarget()
phd.withdraw()
phd.waituntiltarget()