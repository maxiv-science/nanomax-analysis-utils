import zmq
import os

# this sets up the contrast listener
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect ("tcp://172.16.125.30:5556")
socket.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all topics

# loop and listen:
while True:
    message = socket.recv_pyobj()
    if message['status'] == 'finished':
        scan = message['scannr']
        if 'ptycho=true' in message['description'].lower():
            print('starting reconstruction job, scan %u'%scan)
            os.system('sbatch slurm_submit.sh %u'%scan)
    elif message['status'] == 'started':
        print('scan %u started'%message['scannr'])
    elif message['status'] == 'hearbeat':
        print(message)
