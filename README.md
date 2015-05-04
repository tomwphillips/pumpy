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

## You will need
* Python 2.7.3 or higher
* [PySerial](http://pyserial.sourceforge.net) 2.6 or higher
* Computer with RS-232 port or a USB-serial adapter
* Cable to connect your pump. See the pump manual for the correct wiring.

## Usage
Download source code then run `python setup.py install` to install. Use `import pumpy` in your code or run `python -m pumpy --help` to see command line options.

## Known Issues
1. Harvard PHD2000 supports higher precision when setting flow rates/diameters than the Pump 11. At present everything is truncated for compatibility with the Pump 11.
2. PHD2000 requires "withdraw, stop, infuse" rather than "withdraw, infuse" otherwise it doesn't respond.
3. PHD2000 will only take notice of target volumes when it has been put into volume mode using the keypad.
4. No proper unit tests. In theory, big changes could break everything. However, I'm not exactly sure how I would go about implementing unit tests for pumpy. In general, I run ``example.py`` and the command line interface to check I don't break stuff. Suggestions for tests are welcome.

## Acknowledgements

Thanks to [Sam Macbeth](https://github.com/sammacbeth) for adding support for the Mighty Mini.