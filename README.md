# pumpy
Python RS–232 interface for Harvard Pump 11, Pump 11 Plus, PHD2000 syringe pumps and Mighty Mini piston pump. Written and maintained by [Thomas W. Phillips](https://github.com/tomwphillips). Support for Mighty Mini pump by [Sam Macbeth](https://github.com/sammacbeth).

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

## Licence
[Creative Commons Attribution 4.0 International License (CC-BY 4.0)](http://creativecommons.org/licenses/by/4.0/deed.en_US)

## Requirements
* Python 2.7.3 or higher
* [PySerial](http://pyserial.sourceforge.net) 2.6 or higher

## Usage
1. Command line interface. Run `python pumpy.py -h` for options.
2. Clone pumpy into your working directory and then use `import pumpy.pumpy` in your script to call the functions. See `example.py`. I suggest you use `git submodule` if working in a git repository.
3. Use the included LabVIEW VI, which calls ``pumpy.py``.

## Issues
1. Harvard PHD2000 supports higher precision when setting flow rates/diameters than the Pump 11. At present everything is truncated for compatibility with the Pump 11.
2. PHD2000 requires "withdraw, stop, infuse" rather than "withdraw, infuse" otherwise it doesn't respond.
3. PHD2000 will only take notice of target volumes when it has been put into volume mode using the keypad.
4. No proper unit tests. In theory, big changes could break everything. However, I'm not exactly sure how I would go about implementing unit tests for pumpy. In general, I run ``example.py`` and the command line interface to check I don't break stuff. Suggestions for tests are welcome.