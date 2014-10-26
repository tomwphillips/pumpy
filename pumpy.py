from __future__ import print_function 
import serial
import argparse
import logging

def remove_crud(string):
    """Return string without useless information.

     Return string with trailing zeros after a decimal place, trailing
     decimal points, and leading and trailing spaces removed.
     """
    if "." in string:
        string = string.rstrip('0')

    string = string.lstrip('0 ')
    string = string.rstrip(' .')

    return string

class Chain(serial.Serial):
    """Create Chain object.

    Harvard syringe pumps are daisy chained together in a 'pump chain'
    off a single serial port. A pump address is set on each pump. You
    must first create a chain to which you then add Pump objects.

    Chain is a subclass of serial.Serial. Chain creates a serial.Serial
    instance with the required parameters, flushes input and output
    buffers (found during testing that this fixes a lot of problems) and
    logs creation of the Chain.
    """
    def __init__(self, port):
        serial.Serial.__init__(self,port=port, stopbits=serial.STOPBITS_TWO, parity=serial.PARITY_NONE, timeout=2)
        self.flushOutput()
        self.flushInput()
        logging.info('Chain created on %s',port)

class Pump:
    """Create Pump object for Harvard Pump 11.

    Argument:
        Chain: pump chain

    Optional arguments:
        address: pump address. Default is 0.
        name: used in logging. Default is Pump 11.
    """
    def __init__(self, chain, address=0, name='Pump 11'):
        self.name = name
        self.serialcon = chain
        self.address = '{0:02.0f}'.format(address)
        self.diameter = None
        self.flowrate = None
        self.targetvolume = None

        """Query model and version number of firmware to check pump is
        OK. Responds with a load of stuff, but the last three characters
        are XXY, where XX is the address and Y is pump status. :, > or <
        when stopped, running forwards, or running backwards. Confirm
        that the address is correct. This acts as a check to see that
        the pump is connected and working."""
        try:
            self.write('VER')
            resp = self.read(17)

            if int(resp[-3:-1]) != int(self.address):
                raise PumpError('No response from pump at address %s' %
                                self.address)
        except PumpError:
            self.serialcon.close()
            raise

        logging.info('%s: created at address %s on %s', self.name,
                      self.address, self.serialcon.port)

    def __repr__(self):
        string = ''
        for attr in self.__dict__:
            string += '%s: %s\n' % (attr,self.__dict__[attr]) 
        return string

    def write(self,command):
        self.serialcon.write(self.address + command + '\r')

    def read(self,bytes=5):
        response = self.serialcon.read(bytes)

        if len(response) == 0:
            raise PumpError('%s: no response to command' % self.name)
        else:
            return response

    def setdiameter(self, diameter):
        """Set syringe diameter (millimetres).

        Pump 11 syringe diameter range is 0.1-35 mm. Note that the pump
        ignores precision greater than 2 decimal places. If more d.p.
        are specificed the diameter will be truncated.
        """
        if diameter > 35 or diameter < 0.1:
            raise PumpError('%s: diameter %s mm is out of range' % 
                            (self.name, diameter))

        # TODO: Got to be a better way of doing this with string formatting
        diameter = str(diameter)

        # Pump only considers 2 d.p. - anymore are ignored
        if len(diameter) > 5:
            if diameter[2] is '.': # e.g. 30.2222222
                diameter = diameter[0:5]
            elif diameter[1] is '.': # e.g. 3.222222
                diameter = diameter[0:4]

            diameter = remove_crud(diameter)
            logging.warning('%s: diameter truncated to %s mm', self.name,
                            diameter)
        else:
            diameter = remove_crud(diameter)

        # Send command   
        self.write('MMD' + diameter)
        resp = self.read(5)

        # Pump replies with address and status (:, < or >)        
        if (resp[-1] == ':' or resp[-1] == '<' or resp[-1] == '>'):
            # check if diameter has been set correctlry
            self.write('DIA')
            resp = self.read(15)
            returned_diameter = remove_crud(resp[3:9])
            
            # Check diameter was set accurately
            if returned_diameter != diameter:
                logging.error('%s: set diameter (%s mm) does not match diameter'
                              ' returned by pump (%s mm)', self.name, diameter,
                              returned_diameter)
            elif returned_diameter == diameter:
                self.diameter = float(returned_diameter)
                logging.info('%s: diameter set to %s mm', self.name,
                             self.diameter)
        else:
            raise PumpError('%s: unknown response to setdiameter' % self.name)

    def setflowrate(self, flowrate):
        """Set flow rate (microlitres per minute).

        Flow rate is converted to a string. Pump 11 requires it to have
        a maximum field width of 5, e.g. "XXXX." or "X.XXX". Greater
        precision will be truncated.

        The pump will tell you if the specified flow rate is out of
        range. This depends on the syringe diameter. See Pump 11 manual.
        """
        flowrate = str(flowrate)

        if len(flowrate) > 5:
            flowrate = flowrate[0:5]
            flowrate = remove_crud(flowrate)
            logging.warning('%s: flow rate truncated to %s uL/min', self.name, 
                             flowrate)
        else:
            flowrate = remove_crud(flowrate)

        self.write('ULM' + flowrate)
        resp = self.read(5)
        
        if (resp[-1] == ':' or resp[-1] == '<' or resp[-1] == '>'):
            # Flow rate was sent, check it was set correctly
            self.write('RAT')
            resp = self.read(150)
            returned_flowrate = remove_crud(resp[2:8])

            if returned_flowrate != flowrate:
                logging.error('%s: set flowrate (%s uL/min) does not match'
                              'flowrate returned by pump (%s uL/min)',
                              self.name, flowrate, returned_flowrate)
            elif returned_flowrate == flowrate:
                self.flowrate = returned_flowrate
                logging.info('%s: flow rate set to %s uL/min', self.name,
                              self.flowrate)
        elif 'OOR' in resp:
            raise PumpError('%s: flow rate (%s uL/min) is out of range' %
                           (self.name, flowrate))
        else:
            raise PumpError('%s: unknown response' % self.name)
            
    def infuse(self):
        """Start infusing pump."""
        self.write('RUN')
        resp = self.read(5)
        while resp[-1] != '>':
            if resp[-1] == '<': # wrong direction
                self.write('REV')
            else:
                raise PumpError('%s: unknown response to to infuse' % self.name)
            resp = self.serialcon.read(5)
        
        logging.info('%s: infusing',self.name)

    def withdraw(self):
        """Start withdrawing pump."""
        self.write('REV')
        resp = self.read(5)
        
        while resp[-1] != '<':
            if resp[-1] == ':': # pump not running
                self.write('RUN')
            elif resp[-1] == '>': # wrong direction
                self.write('REV')
            else:
                raise PumpError('%s: unknown response to withdraw' % self.name)
                break
            resp = self.read(5)

        logging.info('%s: withdrawing',self.name)

    def stop(self):
        """Stop pump."""
        self.write('STP')
        resp = self.read(5)
        
        if resp[-1] != ':':
            raise PumpError('%s: unexpected response to stop' % self.name)
        else:
            logging.info('%s: stopped',self.name)

    def settargetvolume(self, targetvolume):
        """Set the target volume to infuse or withdraw (microlitres)."""
        self.write('MLT' + str(targetvolume))
        resp = self.read(5)

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address
        # Pump11 replies with leading zeros, e.g. 03, but PHD2000 misbehaves and 
        # returns without and gives an extra CR. Use int() to deal with
        if resp[-1] == ':' or resp[-1] == '>' or resp[-1] == '<':
            self.targetvolume = float(targetvolume)
            logging.info('%s: target volume set to %s uL', self.name,
                         self.targetvolume)
        else:
            raise PumpError('%s: target volume not set' % self.name)

    def waituntiltarget(self):
        """Wait until the pump has reached its target volume."""
        logging.info('%s: waiting until target reached',self.name)
        # counter - need it to check if it's the first loop
        i = 0
    
        while True:
            # Read once
            self.serialcon.write(self.address + 'VOL\r')
            resp1 = self.read(15)

            if ':' in resp1 and i == 0:
                raise PumpError('%s: not infusing/withdrawing - infuse or '
                                'withdraw first', self.name)
            elif ':' in resp1 and i != 0:
                # pump has already come to a halt
                logging.info('%s: target volume reached, stopped',self.name)
                break

            # Read again
            self.serialcon.write(self.address + 'VOL\r')
            resp2 = self.read(15)

            # Check if they're the same - if they are, break, otherwise continue
            if resp1 == resp2:
                logging.info('%s: target volume reached, stopped',self.name)
                break

            i = i+1

class PHD2000(Pump):
    """Harvard PHD2000 pump object.

    Inherits from Pump class, but needs its own class as it doesn't
    stick to the Pump 11 protocol with commands to stop and set the
    target volume.
    """
    def stop(self):
        """Stop pump."""
        self.write('STP')
        resp = self.read(5)
        
        if resp[-1] == '*':
            logging.info('%s: stopped',self.name)
        else:
            raise PumpError('%s: unexpected response to stop', self.name)

    def settargetvolume(self, targetvolume):
        """Set the target volume to infuse or withdraw (microlitres)."""

        # PHD2000 expects target volume in mL not uL like the Pump11, so convert to mL
        targetvolume = str(float(targetvolume)/1000.0)

        if len(targetvolume) > 5:
            targetvolume = targetvolume[0:5]
            logging.warning('%s: target volume truncated to %s mL',self.name,targetvolume)

        self.write('MLT' + targetvolume)
        resp = self.read(5)

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address
        # Pump11 replies with leading zeros, e.g. 03, but PHD2000 misbehaves and 
        # returns without and gives an extra CR. Use int() to deal with
        if resp[-1] == ':' or resp[-1] == '>' or resp[-1] == '<':
            # Been set correctly, so put it back in the object (as uL, not mL)
            self.targetvolume = float(targetvolume)*1000.0
            logging.info('%s: target volume set to %s uL', self.name,
                          self.targetvolume)

class MightyMini():
    def __init__(self, chain, name='Mighty Mini'):
        self.name = name
        self.serialcon = chain.serialcon
        logging.info('%s: created on %s',self.name,self.serialcon.port)

    def __repr__(self):
        string = ''
        for attr in self.__dict__:
            string += '%s: %s\n' % (attr,self.__dict__[attr]) 
        return string

    def setflowrate(self, flowrate):
        flowrate = int(flowrate)
        if flowrate > 9999:
            flowrate = 9999
            logging.warning('%s: flow rate limited to %s uL/min', self.name,
                            flowrate)

        self.serialcon.write('FM' + "{:04d}".format(flowrate))
        resp = self.serialcon.read(3)
        self.serialcon.flushInput()
        if len(resp) == 0:
            raise PumpError('%s: no response to set flowrate', self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            # flow rate sent, check it is correct
            self.serialcon.write('CC')
            resp = self.serialcon.read(11)
            returned_flowrate = int(float(resp[5:-1])*1000)
            if returned_flowrate != flowrate:
                raise PumpError('%s: set flowrate (%s uL/min) does not match'
                              ' flowrate returned by pump (%s uL/min)',
                              self.name, flowrate, returned_flowrate)
            elif returned_flowrate == flowrate:
                self.flowrate = returned_flowrate
                logging.info('%s: flow rate set to %s uL/min', self.name, 
                             self.flowrate)
        else:
            raise PumpError('%s: error setting flow rate (%s uL/min)',
                            self.name,flowrate)

    def infuse(self):
        self.serialcon.write('RU')
        resp = self.serialcon.read(3)
        if len(resp) == 0:
            raise PumpError('%s: no response to infuse',self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            logging.info('%s: infusing',self.name)

    def stop(self):
        self.serialcon.write('ST')
        resp = self.serialcon.read(3)
        if len(resp) == 0:
            raise PumpError('%s: no response to stop',self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            logging.info('%s: stopping',self.name)

class PumpError(Exception):
    pass

# Command line options
# Run with -h flag to see help

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line interface to '
                                     'pumpy module for control of Harvard Pump '
                                     '11 (default) or PHD2000 syringe pumps, or'
                                     ' SSI Mighty Mini Pump')
    parser.add_argument('port', help='serial port')
    parser.add_argument('address', help='pump address (Harvard pumps)',type=int,
                         nargs='?', default=0)
    parser.add_argument('-d', dest='diameter', help='set syringe diameter',
                        type=int)
    parser.add_argument('-f', dest='flowrate', help='set flow rate')
    parser.add_argument('-t', dest='targetvolume', help='set target volume')
    parser.add_argument('-w', dest='wait', help='wait for target volume to be'
                        ' reached; use with -infuse or -withdraw',
                        action='store_true')
    
    # TODO: only allow -w if infuse, withdraw or stop have been specified
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-infuse', action='store_true')
    group.add_argument('-withdraw', action="store_true")
    group.add_argument('-stop', action="store_true")

    pumpgroup = parser.add_mutually_exclusive_group()
    pumpgroup.add_argument('-PHD2000', help='To control PHD2000',
                           action='store_true')
    pumpgroup.add_argument('-MightyMini', help='To control Mighty Mini',
                           action='store_true')
    args = parser.parse_args()

    if args.MightyMini:
        chain = Chain(args.port, stopbits=serial.STOPBITS_ONE)
    else:
        chain = Chain(args.port)

    # Command precedence:
    # 1. stop
    # 2. set diameter
    # 3. set flow rate
    # 4. set target
    # 5. infuse|withdraw (+ wait for target volume)

    try:
        if args.PHD2000:
            pump = PHD2000(chain, args.address, name='PHD2000')
        elif args.MightyMini:
            pump = MightyMini(chain, name='MightyMini')
        else:
            pump = Pump(chain,args.address, name='11')

        if args.stop:
            pump.stop()

        if args.diameter:
            pump.setdiameter(args.diameter)

        if args.flowrate:
            pump.setflowrate(args.flowrate)

        if args.targetvolume:
            pump.settargetvolume(args.targetvolume)

        if args.infuse:
            pump.infuse()
            if args.wait:
                pump.waituntiltarget()

        if args.withdraw:
            pump.withdraw()
            if args.wait:
                pump.waituntiltarget()
    finally:
        chain.close()
