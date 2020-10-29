"""
A base class reacting on a constrast streamrecorders zmq stream 
if a scan starts, finishes or is interrupted.
It can be used to write all sorts of tools that shall run automatically.
"""

import os
import sys
import zmq
import h5py
import json
import numpy as np


class zmq_on_scan_end_do(object):
    """
    base class subscribing to a contrast streamrecorders zmq stream and
    reacting on:
        the start of scans
        the proper finnishing of scans
        the interruption of scans
    """

    ############################################################################
    # these are the three methods you will have to fill with life
    ############################################################################

    def do_on_scan_started(self, _message):
        pass

    def do_on_scan_finished(self, _message):
        pass

    def do_on_scan_interrupted(self, _message):
        pass

    ############################################################################

    def __init__(self, port=5556, host='localhost'):
        context = zmq.Context()
        self.sock = context.socket(zmq.SUB)
        self.sock.connect ("tcp://%s:%u" % (host, port))
        self.sock.setsockopt(zmq.SUBSCRIBE, b"")
        print('#'*80)
        print('# started to listen to %s:%u' % (host, port))
        print('#'*80)

    def run(self):
        while True:
            ### get a message from the stream
            try:
                _message = self.sock.recv_pyobj()

                #check what the message said
                if 'scannr' in _message.keys():        # scan either started, finished or interrupted
                    
                    scannr      = _message['scannr']
                    status      = _message['status']
                    path        = _message['path']
                    snapshot    = _message['snapshot']
                    description = _message['description']

                    if status=='finished': # scan finished properly                        
                        self.pretty_print_message('scan #'+str(scannr)+' has finished', '')
                        self.do_on_scan_finished(_message)

                    elif status=='interrupted': # scan was interrupted
                        self.pretty_print_warning('scan #'+str(scannr)+' interrupted')
                        self.do_on_scan_interrupted(self, _message)

                    elif _message['status']=='started': # scan has just started
                        self.pretty_print_message('scan #'+str(scannr)+' has started', '')
                        self.do_on_scan_started(self, _message)

            except Exception as e: print(e)

    ############################################################################

    def make_color_code(self, style='none', text_color='black', background_color='white'):
        dict_style = {'none':'0', 'bold':'1', 'underline':'2', 'negative1':'3', 'negative2':'5'}
        dict_c     = {'black':'30',  'k':'30', 
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
        line  = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','r') + '\u25B6 '
        line += self.make_color_code('none','k','r') + 'error '
        line += self.make_color_code('none','r','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + error_message
        print(line)

    def pretty_print_warning(self, warning_message):
        line  = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','y') + '\u25B6 '
        line += self.make_color_code('none','k','y') + 'warning '
        line += self.make_color_code('none','y','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + warning_message
        print(line)

    def pretty_print_message(self, header, message):
        line  = self.make_color_code('bold','k','c') + ' ' + sys.argv[0] + ' '
        line += self.make_color_code('none','c','g') + '\u25B6 '
        line += self.make_color_code('none','k','g') + header+' '
        line += self.make_color_code('none','g','w') + '\u25B6 '
        line += self.make_color_code('none','k','w') + message
        print(line)                      

################################################################################

class zmq_push_ptycho_rec_on_cluster(zmq_on_scan_end_do):
    """ 
    my EXAMPLE class, reacting on properly finnishing scans, checking for
    a keyword argument in the scan command and pushing a ptycho reconstruction
    to the cluster.
    """

    def do_on_scan_finished(self, _message):

        scannr       = _message['scannr']
        status       = _message['status']
        path         = _message['path']
        snapshot     = _message['snapshot']
        scan_command = _message['description']

        if 'slurm_rec=True' in scan_command:

            ### run the script that creates the slurm shell script
            print('   ', '# creating the slurm sbatch script')
            command = 'python3 /data/visitors/nanomax/20191087/2020102408/macros/slurm_create_sh.py '+str(scannr)
            print('   ', command)
            os.system(command)

            ### and push the job to the cluster
            print('   ', '# pushing it to slurm')
            command = 'sbatch /data/visitors/nanomax/20191087/2020102408/process/0005_Ni552nm_tomo/scan_'+str(scannr).zfill(6)+'/ptycho_ptypy/slurm_ptycho_scan_'+str(scannr).zfill(6)+'.sh'
            print('   ', command)
            os.system(command)

################################################################################

if __name__ == "__main__":

    known_hosts = {}
    known_hosts['cc1'] = '172.16.125.11'
    known_hosts['cc2'] = '172.16.125.18'

    recv = zmq_push_ptycho_rec_on_cluster(host=known_hosts['cc2'], port=5556) 
    recv.run()
