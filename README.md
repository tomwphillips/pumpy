# pumpy: computer control of your syringe pumps

Pumpy allows you to control your Harvard syringe pump or Mighty Mini piston pump from your computer over an RS-232 interface.

## Supported pumps

* Harvard Pump 11
* Harvard Pump 11 Plus
* Harvard PHD2000
* Mighty Mini piston pump

## Features

* For Harvard Pump 11, Pump 11 Plus, and PHD2000:
	* infuse
	* withdraw
	* set diameter
	* set flow rate
	* set target volume
	* wait until target volume 
* For Mighty Mini:
	* set flow rate
	* start
	* top
* Supports [`logging`](https://ocs.python.org/2/library/logging.html) to record all operations.

## Requirements
* Python 2.7.3 or higher
* [PySerial](http://pyserial.sourceforge.net) 2.6 or higher
* Computer with RS-232 port or a USB-serial adapter
* Cable to connect your pump. See the pump manual for the correct wiring.

## Install

`pip install pumpy`

## Usage

Run `python -m pumpy --help` to see command line options.

Alternatively you can use it in your existing code:

```
chain = pumpy.Chain('/dev/tty.usbserial-FTWOFH91A')

p11 = pumpy.Pump(chain,address=1) 
p11.setdiameter(10)  # mm
p11.setflowrate(2000)  ## microL/min
p11.settargetvolume(200)  ## microL
p11.infuse()
p11.waituntiltarget()  ## blocks until target reached
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
```

## Known Issues

1. Harvard PHD2000 supports higher precision when setting flow rates/diameters than the Pump 11. At present everything is truncated for compatibility with the Pump 11.
2. PHD2000 requires "withdraw, stop, infuse" rather than "withdraw, infuse" otherwise it doesn't respond.
3. PHD2000 will only take notice of target volumes when it has been put into volume mode using the keypad.

## Acknowledgements

Thanks to [Sam Macbeth](https://github.com/sammacbeth) for adding support for the Mighty Mini.
