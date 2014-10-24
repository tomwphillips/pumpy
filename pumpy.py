from __future__ import print_function 
import serial
import argparse
import logging

logging.basicConfig(level=logging.INFO)

def remove_crud(string):
    """Return string without useless information.

     Return string with trailing zeros after a decimal place, trailing
     decimal points, and leading and trailing spaces removed.
     """
    # Remove trailing zeros after decimal place
    if "." in string:
        while string[-1] == '0':
            string = string[0:-1]

    # Remove decimal point with nothing after it
    if string[-1] == ".":
        string = string[:-1]
    
    # Remove leading zeros
    while string[0] == '0':
        string = string[1:]

    # Remove leading spaces
    while string[0] == ' ':
        string = string[1:]

    # Remove trailing spaces
    while string[-1] == ' ':
        string = string[:-2]

    return string

class Chain:
    """Create Chain object.

    Harvard syring pumps are daisy chained together in a 'pump chain'
    off a single serial port. A pump address is set on each pump. You
    must first create a chain to which you then add Pump objects.
    """
    def __init__(self, port, stopbits=serial.STOPBITS_TWO):
        self.serialcon = serial.Serial(port=port, stopbits=stopbits,
                                       parity=serial.PARITY_NONE, timeout=2)
        self.serialcon.flushOutput()
        self.serialcon.flushInput()
        if self.serialcon.isOpen():
            logging.info('Chain %s: created',port)
        else:
            logging.critical('Chain %s: unable to create',port)

class Pump:
    """Create Pump object for Harvard Pump 11.

    Argument:
        Chain: pump chain

    Optional arguments:
        address: pump address. Default is 0.
        name: used in logging. Default is None.
    """
    def __init__(self, chain, address=0, name=None):
        self.name = name
        self.serialcon = chain.serialcon
        self.address = '{0:02.0f}'.format(address)
        self.diameter = None
        self.flowrate = None
        self.targetvolume = None

        logging.info('Pump %s: created at address %s on %s',self.name,self.address,self.serialcon.port)

    def __repr__(self):
        string = ''
        for attr in self.__dict__:
            string += '%s: %s\n' % (attr,self.__dict__[attr]) 
        return string

    def setdiameter(self, diameter):
        if diameter > 35 or diameter < 0.1:
            logging.error('Pump %s: %s mm out of diameter range. Must be between 0.1-35 mm.',self.name,diameter)
            return None

        diameter = str(diameter)

        # Pump only considers 2 d.p. - anymore are ignored
        if len(diameter) > 5:
            if diameter[2] is '.': # e.g. 30.2222222
                diameter = diameter[0:5]
            elif diameter[1] is '.': # e.g. 3.222222
                diameter = diameter[0:4]

            diameter = remove_crud(diameter)
            logging.warning('Pump %s: diameter truncated to %s mm',self.name,diameter)
        else:
            diameter = remove_crud(diameter)

        # Send command   
        self.serialcon.write(self.address + 'MMD' + diameter + '\r')
        resp = self.serialcon.read(5)

        # Pump replies with address and status (:, < or >)        
        if len(resp) > 0 and (resp[-1] == ':' or resp[-1] == '<' or resp[-1] == '>'):
            # check if diameter has been set correctlry
            self.serialcon.write(self.address + 'DIA\r')
            resp = self.serialcon.read(15)
            returned_diameter = remove_crud(resp[3:9])
            
            # Check diameter was set accurately
            if returned_diameter != diameter:
                logging.error('Pump %s: set diameter (%s mm) does not match diameter returned by pump (%s mm)',self.name,diameter,returned_diameter)
            elif returned_diameter == diameter:
                self.diameter = float(returned_diameter)
                logging.info('Pump %s: diameter set to %s mm',self.name,self.diameter)
        else:
            logging.error('Pump %s: unknown response',self.name)

    def setflowrate(self, flowrate):
        flowrate = str(flowrate)

        if len(flowrate) > 5:
            flowrate = flowrate[0:5]
            flowrate = remove_crud(flowrate)
            logging.warning('Pump %s: flow rate truncated to %s uL/min',self.name,flowrate)
        else:
            flowrate = remove_crud(flowrate)

        self.serialcon.write(self.address + 'ULM' + flowrate + '\r')
        resp = self.serialcon.read(5)
        
        if len(resp) > 0 and (resp[-1] == ':' or resp[-1] == '<' or resp[-1] == '>'):
            # Flow rate was sent, check it was set correctly
            self.serialcon.write(self.address + 'RAT\r')
            resp = self.serialcon.read(150)
            returned_flowrate = remove_crud(resp[2:8])

            if returned_flowrate != flowrate:
                logging.error('Pump %s: set flowrate (%s uL/min) does not match flowrate returned by pump (%s uL/min)',self.name,flowrate,returned_flowrate)
            elif returned_flowrate == flowrate:
                self.flowrate = returned_flowrate
                logging.info('Pump %s: flow rate set to %s uL/min',self.name,self.flowrate)
        elif 'OOR' in resp:
            logging.error('Pump %s: flow rate (%s uL/min) is out of range',self.name,flowrate)
        else:
            logging.error('Pump %s: unknown response',self.name)
            
    def infuse(self):
        self.serialcon.write(self.address + 'RUN\r')
        resp = self.serialcon.read(5)
        if len(resp) > 0:
            while resp[-1] != '>':
                if resp[-1] == '<': # wrong direction
                    self.serialcon.write(self.address + 'REV\r')
                else:
                    logging.error('Pump %s: unexpected response to infuse',self.name)
                    break

                resp = self.serialcon.read(5)
                logging.info('Pump %s: infusing',self.name)
        else:
            logging.error('Pump %s: empty response to infuse',self.name)

    def withdraw(self):
        self.serialcon.write(self.address + 'REV\r')
        resp = self.serialcon.read(5)
        
        if len(resp) > 0:
            while resp[-1] != '<':
                if resp[-1] == ':': # pump not running
                    self.serialcon.write(self.address + 'RUN\r')
                elif resp[-1] == '>': # wrong direction
                    self.serialcon.write(self.address + 'REV\r')
                else:
                    logging.error('Pump %s: unexpected response to withdraw',self.name)
                    break

                resp = self.serialcon.read(5)
                logging.info('Pump %s: withdrawing',self.name)
        else:
            logging.error('Pump %s: empty response to withdraw',self.name)

    def stop(self):
        self.serialcon.write(self.address + 'STP\r')
        resp = self.serialcon.read(5)
        
        if len(resp) == 0 or resp[-1] != ':':
            logging.error('Pump %s: unexpected response to stop',self.name)
        else:
            logging.info('Pump %s: stopped',self.name)

    def settargetvolume(self, targetvolume):
        self.serialcon.write(self.address + 'MLT' + str(targetvolume) + '\r')
        resp = self.serialcon.read(5)

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address
        # Pump11 replies with leading zeros, e.g. 03, but PHD2000 misbehaves and 
        # returns without and gives an extra CR. Use int() to deal with
        if len(resp) == 0:
            logging.error('Pump %s: empty response',self.name)
        elif int(resp[-3:-1]) != int(self.address):
            logging.error('Pump %s: response has incorrect address',self.name)
        elif resp[-1] == ':' or resp[-1] == '>' or resp[-1] == '<':
            self.targetvolume = float(targetvolume)
            logging.info('Pump %s: target volume set to %s uL',self.name,self.targetvolume)

    def waituntiltarget(self):
        logging.info('Pump %s: waiting until target reached',self.name)
        # counter - need it to check if it's the first loop
        i = 0
    
        while True:
            # Read once
            self.serialcon.write(self.address + 'VOL\r')
            resp1 = self.serialcon.read(15)

            if ':' in resp1 and i == 0:
                logging.error('Pump %s: not infusing/withdrawing - infuse or withdraw first',self.name)
            elif ':' in resp1 and i != 0:
                # pump has already come to a halt
                logging.info('Pump %s: target volume reached, stopped',self.name)
                break

            # Read again
            self.serialcon.write(self.address + 'VOL\r')
            resp2 = self.serialcon.read(15)

            # Check if they're the same - if they are, break, otherwise continue
            if resp1 == resp2:
                logging.info('Pump %s: target volume reached, stopped',self.name)
                break

            i = i+1

# PHD2000 subclass because it behaves badly    
class PHD2000(Pump):
    def stop(self):
        self.serialcon.write(self.address + 'STP\r')
        resp = self.serialcon.read(5)
        
        if resp[-1] != '*':
            logging.error('Pump %s: unexpected response to stop',self.name)
        else:
            logging.info('Pump %s: stopped',self.name)

    def settargetvolume(self, targetvolume):
        # PHD2000 expects target volume in mL not uL like the Pump11, so convert to mL
        targetvolume = str(float(targetvolume)/1000.0)

        if len(targetvolume) > 5:
            targetvolume = targetvolume[0:5]
            logging.warning('Pump %s: target volume truncated to %s mL',self.name,targetvolume)

        self.serialcon.write(self.address + 'MLT' + targetvolume  + '\r')
        resp = self.serialcon.read(5)

        # response should be CRLFXX:, CRLFXX>, CRLFXX< where XX is address
        # Pump11 replies with leading zeros, e.g. 03, but PHD2000 misbehaves and 
        # returns without and gives an extra CR. Use int() to deal with
        if int(resp[-3:-1]) != int(self.address):
            logging.error('Pump %s: response has incorrect address',self.name)
        elif resp[-1] == ':' or resp[-1] == '>' or resp[-1] == '<':
            # Been set correctly, so put it back in the object (as uL, not mL)
            self.targetvolume = float(targetvolume)*1000.0
            logging.info('Pump %s: target volume set to %s uL',self.name,self.targetvolume)

class MightyMini():

    def __init__(self, chain, name=None):
        self.name = name
        self.serialcon = chain.serialcon

        logging.info('Pump %s: created on %s',self.name,self.serialcon.port)

    def __repr__(self):
        string = ''
        for attr in self.__dict__:
            string += '%s: %s\n' % (attr,self.__dict__[attr]) 
        return string

    def setdiameter(self, diameter):
        logging.error('Set diameter not applicable to pump %s', self.name)
        return None

    def setflowrate(self, flowrate):
        flowrate = int(flowrate)
        if flowrate > 9999:
            flowrate = 9999
            logging.warning('Pump %s: flow rate truncated to %s uL/min',self.name,flowrate)

        self.serialcon.write('FM' + "{:04d}".format(flowrate))
        resp = self.serialcon.read(3)
        self.serialcon.flushInput()
        if len(resp) == 0:
            logging.error('Pump %s: no response to setflowrate',self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            # flow rate sent, check it is correct
            self.serialcon.write('CC')
            resp = self.serialcon.read(11)
            returned_flowrate = int(float(resp[5:-1])*1000)
            if returned_flowrate != flowrate:
                logging.error('Pump %s: set flowrate (%s uL/min) does not match flowrate returned by pump (%s uL/min)',self.name,flowrate,returned_flowrate)
            elif returned_flowrate == flowrate:
                self.flowrate = returned_flowrate
                logging.info('Pump %s: flow rate set to %s uL/min',self.name,self.flowrate)
        else:
            logging.error('Pump %s: error setting flow rate (%s uL/min)',self.name,flowrate)

    def infuse(self):
        self.serialcon.write('RU')
        resp = self.serialcon.read(3)
        if len(resp) == 0:
            logging.error('Pump %s: no response to infuse',self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            logging.info('Pump %s: infusing',self.name)

    def withdraw(self):
        logging.error('Set withdraw not applicable to pump %s', self.name)
        return None

    def stop(self):
        self.serialcon.write('ST')
        resp = self.serialcon.read(3)
        if len(resp) == 0:
            logging.error('Pump %s: no response to stop',self.name)
        elif resp[0] == 'O' and resp[1] == 'K':
            logging.info('Pump %s: stopping',self.name)

    def settargetvolume(self, targetvolume):
        logging.error('Set target volume not applicable to pump %s', self.name)
        return None

    def waituntiltarget(self):
        logging.error('waituntiltarget not applicable to pump %s', self.name)
        return None

# Command line options
# Run with -h flag to see help

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line interface to pumpy module for control of Harvard Pump 11 (default) or PHD2000 syringe pumps, or SSI Mighty Mini Pump')
    parser.add_argument('port',help='serial port')
    parser.add_argument('address',help='pump address (Harvard pumps)',type=int,nargs='?',default=0)
    parser.add_argument('-d',dest='diameter',help='set syringe diameter',type=int)
    parser.add_argument('-f',dest='flowrate',help='set flow rate')
    parser.add_argument('-t',dest='targetvolume',help='set target volume')
    parser.add_argument('-w',dest='wait',help='wait for target volume to be reached; use with -infuse or -withdraw',action='store_true')
    # TODO: only allow -w if infuse, withdraw or stop have been specified
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-infuse',action='store_true')
    group.add_argument('-withdraw',action="store_true")
    group.add_argument('-stop',action="store_true")

    pumpgroup = parser.add_mutually_exclusive_group()
    pumpgroup.add_argument('-PHD2000',help='To control PHD2000',action='store_true')
    pumpgroup.add_argument('-MightyMini',help='To control Mighty Mini',action='store_true')
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

    if args.PHD2000:
        pump = PHD2000(chain,args.address,name='PHD2000')
    elif args.MightyMini:
        pump = MightyMini(chain,name='MightyMini')
    else:
        pump = Pump(chain,args.address,name='11')

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
