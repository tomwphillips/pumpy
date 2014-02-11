# pumpy
Python RS–232 interface for Harvard Pump 11/Pump 11 Plus syringe pump. Written by [Thomas W. Phillips][TWP]

## Requirements

Requires [PySerial][]. Developed on Mac OS 10.9.1 with Python 2.7.3 ([Enthought Canopy][] 7.3.1 64-bit) and PySerial 2.6. 

## Usage

Two possibilites:

1. Command line interface. Run `python pumpy.py -h` for options.
2. Using `import pumpy` in another script then calling the functions. For example:

```python
import pumpy
p11 = pumpy.Pump('/dev/tty.usbserial-FTWOFH91D',address=10,verbose=True)
p11.setdiameter(25)
p11.setflowrate(2000)
p11.settargetvolume(200)
p11.infuse()
p11.waituntiltarget()
p11.withdraw()
p11.waituntiltarget()
```

## Licence

[Creative Commons Attribution 4.0 International License (CC-BY 4.0)][CC]

[TWP]: http://www3.imperial.ac.uk/people/thomas.phillips07
[PySerial]: http://pyserial.sourceforge.net
[Enthought Canopy]: https://www.enthought.com/products/canopy/
[CC]: http://creativecommons.org/licenses/by/4.0/deed.en_US