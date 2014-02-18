import pumpy

chain = pumpy.Chain('COM1')
p11 = pumpy.Pump(chain,address=1,verbose=True) # Pump 11
phd = pumpy.PHD2000(chain,address=4,verbose=True) # PHD2000

p11.setdiameter(25)
phd.setdiameter(24)
p11.setflowrate(2000)
phd.setflowrate(600)

p11.settargetvolume(200)
p11.infuse()
phd.infuse()
p11.waituntiltarget()
phd.stop()
phd.withdraw()
p11.withdraw()
p11.waituntiltarget()
phd.stop()

phd.settargetvolume(100)
phd.infuse()
phd.waituntiltarget()