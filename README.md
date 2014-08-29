# pumpy
Python RS–232 interface for Harvard Pump 11, Pump 11 Plus and PHD2000 syringe pumps. Written by [Thomas W. Phillips][TWP], Imperial College London.

## Requirements

Requires [PySerial][]. Developed/tested on Mac OS 10.9.1 and Windows 7 with Python 2.7.3 ([Enthought Canopy][] 7.3.1 64-bit) and PySerial 2.6.

## Usage

Three possibilites:

1. Command line interface. Run `python pumpy.py -h` for options.
2. Copy pumpy into your working directory and then use `import pumpy.pumpy` in your script to callthe functions. See `example.py`. I suggest you use `git submodule` if working in a git repository.
3. Use the included LabVIEW VI, which calls ``pumpy.py``.

## Issues

1. Harvard PHD2000 supports higher precision when setting flow rates/diameters than the Pump 11. At present everything is truncated for compatibility with the Pump 11.
2. PHD2000 requires "withdraw, stop, infuse" rather than "withdraw, infuse" otherwise it doesn't respond.
3. PHD2000 will only take notice of target volumes when it has been put into voluime mode using the keypad.

## Licence

[Creative Commons Attribution 4.0 International License (CC-BY 4.0)][CC]

[TWP]: http://www3.imperial.ac.uk/people/thomas.phillips07
[PySerial]: http://pyserial.sourceforge.net
[Enthought Canopy]: https://www.enthought.com/products/canopy/
[CC]: http://creativecommons.org/licenses/by/4.0/deed.en_US
