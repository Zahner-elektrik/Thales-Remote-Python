'''
  ____       __                        __    __   __      _ __
 /_  / ___ _/ /  ___  ___ ___________ / /__ / /__/ /_____(_) /__
  / /_/ _ `/ _ \/ _ \/ -_) __/___/ -_) / -_)  '_/ __/ __/ /  '_/
 /___/\_,_/_//_/_//_/\__/_/      \__/_/\__/_/\_\\__/_/ /_/_/\_\

Copyright 2021 ZAHNER-elektrik I. Zahner-Schiller GmbH & Co. KG

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import socket

class BCMuxInterface():
    """ BC-Mux control class.
    
    With this class the `BC-MUX Multiplexer <http://zahner.de/products/multiplexer/bc-mux.html>`_ can
    be controlled remotely without the BC-Mux Controller software.
    
    The USB interface of the BC Mux is not supported by Python. Also the network settings must be
    done with the program BC-Mux Network Config before using python.
    
    The BC-MUX is an extension which makes it possible to separate up to 16 channels of a cyclizer
    individually with switch boxes from the cyclizer and to switch them to the Zennium for e.g.
    impedance measurements. This allows the cyclizer to be extended up to 16 channels with sequential
    impedance measurements. Only one channel at a time can be switched to the Zennium for a measurement,
    no parallel impedance measurements are possible.

    This class makes it possible to control the Zennium and the Multiplexer from one Python instance
    via Remote2, which makes the use more flexible than with the BC-Mux Controller.
    Also, if the cyclizer supports it, the complete system can be controlled from a single Python software.
    
    :param ip: SerialCommandInterface object to control the device.
    :type ip: str
    :param port: SerialDataInterface object for online data.
    :type port: int
    """
    
    BUFFER_SIZE = 1024
    
    def __init__(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.socket.connect((self.ip, self.port))
        return
        
    def close(self):
        """ Closing the connection.
        
        Disconnects the TCP/IP connection to the BC-MUX.
        """
        self.socket.close()
        return
        
    def connectChannel(self, channel):
        """ Connects the channel to the zennium.
        
        With this command, a channel is disconnected from the cyclizer and switched to the Zennium,
        for example for impedance measurements.
        
        :param channel: The channel to connect to the zennium.
        :returns: The response string from the device.
        :rtype: string
        """
        command = "ch {}"
        return self._executeCommandAndReadReply(command.format(channel))
    
    def disconnectChannel(self):
        """ Disconnects all channels from the zennium.
        
        All channels are disconnected from the Zennium and switched to the specific cyclizer channel.
        
        :returns: The response string from the device.
        :rtype: string
        """
        command = "ch 0"
        return self._executeCommandAndReadReply(command)
    
    def setPulseLength(self, length):
        """ Setting the relais control.
        
        The BC-MUX supports switchboxes containing monostable or bistable relais. With this command,
        the control of the relais is set.
        
        If a number other than 0 is set, the relay is switched with a pulse.
        The pulse is then the number in milliseconds long.
        
        :param length: The length of the switching pulse in milliseconds. 0 for monostable relays.
        :returns: The response string from the device.
        :rtype: string
        """
        command = "puls {}"
        return self._executeCommandAndReadReply(command.format(length))
        
    def _executeCommandAndReadReply(self, command):
        """ Private function to send a command to the device and read a string.
        
        This command sends the command to the device and returns the response from the device.
        
        :returns: Response string from the device.    
        :rtype: string
        """
        command += "\r\n"
        self.socket.send(command.encode("utf-8"))
        data = self.socket.recv(BCMuxInterface.BUFFER_SIZE)
        return data.decode("utf-8")
        

if __name__ == '__main__':
    """
    This is a short example to switch each of the 16 channels to the Zennium.
    """
    TCP_IP = "192.192.192.192" #IP of the BC-MUX
    TCP_PORT = 4223
    
    bcMux = BCMuxInterface(TCP_IP, TCP_PORT)
    
    bcMux.setPulseLength(250)
    bcMux.disconnectChannel()
    
    for i in range(16):
        print(f"Channel: {i+1}")
        bcMux.connectChannel(i)
        bcMux.disconnectChannel()
    
    
    bcMux.close()
        
    
