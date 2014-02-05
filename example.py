import pumpy
p11 = pumpy.Pump('/dev/tty.usbserial-FTWOFH91D',address=10,verbose=True)
p11.setdiameter(25)
p11.setflowrate(2000)
p11.settargetvolume(200)
p11.infuse()
p11.waituntiltarget()
p11.withdraw()
p11.waituntiltarget()