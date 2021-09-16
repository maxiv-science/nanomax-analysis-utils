"""
A simple terminal tool, nicely plotting all messages send by contrast over ZeroMQ as text.
"""


import os
import sys
import zmq
import h5py
import json
import time
import numpy as np


class zmq_listener(object):
    """
    Subscribes to a contrast stream recordes zmq stream.
    Prints the zmq streamed dictionaries in a nice way.
    """

    ############################################################################

    def __init__(self, port=5556, host='localhost'):
        context = zmq.Context()
        self.sock = context.socket(zmq.SUB)
        self.sock.connect("tcp://%s:%u" % (host, port))
        self.sock.setsockopt(zmq.SUBSCRIBE, b"")
        self.running = True
        self.pretty_print_message('started to listen to', '%s:%u' % (host, port))

    def run(self):
        while self.running:
            try:

                # listen for a message
                _metadata = self.sock.recv_pyobj()

                #do something with the data
                self.pretty_print_message('message recieved', self.date_time_string())
                self.pretty_print_dict(_metadata, indent=1)

                # a tiny delay to let the computer breath
                time.sleep(0.01)
 
            except KeyboardInterrupt:
                self.stop()
                
            except Exception as err:
                self.pretty_print_error('')
                print(err)
                self.stop()

    def stop(self):
        self.sock.close()
        self.running = False
 
    ############################################################################

    def date_time_string(self):
        return time.strftime('%Y-%m-%d_%H:%M:%S')

    def pretty_print_dict(self, d, indent=0):
        for key, value in d.items():
            if isinstance(value, dict):
                print('\t' * indent + str(key)+ ' : ')
                self.pretty_print_dict(value, indent+1)
            else:
                print('\t' * indent + str(key) + ' : '+str(value))
                #print('\t' * (indent+1) + str(value))    def run(self):

    def make_color_code(self, style='none', text_color='black', background_color='white'):
        dict_style = {'none':'0', 'bold':'1', 'underline':'2', 'negative1':'3', 'negative2':'5'}
        dict_c = {'black':'30',  'k':'30', 
                  'red':'31',    'r':'31',
                  'green':'32',  'g':'32',
                  'yellow':'33', 'y':'33',
                  'blue':'34',   'b':'34',
                  'purple':'35', 'm':'35',
                  'cyan':'36',   'c':'36',
                  'gray':'37',   'gr':'37',
                  'white':'38',  'w':'38'} 
        return '\033['+dict_style[style]+';'+dict_c[text_color]+';4'+dict_c[background_color][1]+'m'

    def pretty_print_error(self, error_message):
        line = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','r') + '\u25B6 '
        line += self.make_color_code('none','k','r') + 'error '
        line += self.make_color_code('none','r','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + error_message
        print(line)

    def pretty_print_warning(self, warning_message):
        line = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','y') + '\u25B6 '
        line += self.make_color_code('none','k','y') + 'warning '
        line += self.make_color_code('none','y','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + warning_message
        print(line)

    def pretty_print_message(self, header, message):
        line = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','g') + '\u25B6 '
        line += self.make_color_code('none','k','g') + header+' '
        line += self.make_color_code('none','g','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + message
        print(line)                      


###############################################################################

if __name__ == "__main__":

    known_hosts = {}
    known_hosts['cc1'] = '172.16.125.11'
    known_hosts['cc2'] = '172.16.125.18'

    recv = zmq_listener(host=known_hosts['cc2'], port=5556) 
    recv.run()
