"""
A tool to plot the maps of choosen XRF ROIs live as the scan is being recorded.
Requires the xspress3 do run the ZMQ streamer and contrast to have the
zmqrecorder active.
Shown maps are automatically reset once a new scan is started.

The ROIs can be defined by a ini file created by the scanViewer.
I suggest to limit yourself to a few ROIs for this liveViewer.
Better run on a cluster compute node, as the repeated calculation of the maps can
be computationally demanding.
"""

import os
import sys
import zmq
import math
import time
import socket
import configparser
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt 

# Todo:
#   ... using the indexing of the data points in the streamed messag
#       -> when the streamer is started during the scan, there is no confusion between 
#       the individually streamed spectra and the positions streamed as lines
#       -> would also allow for a progressbar and time estimate to scan end
#   ... figure out why it is blocking between the updates ... maybe use plt.ion()  and plt.draw()/plt.pause()
#   ... checking with the latest matplotlib version ... otherwise maybe also use silx widgets

class XRF_scanliveview():
    """ 
    A live viewer for the NanoMAX beamline showing a 2D XRF map as it is scanned
    """
    
    def __init__(self, 
                 fpath_ROI_ini, 
                 host_xspress3='172.16.126.70', #b303a-a100380-cab-dia-detxfcu-01
                 port_xspress3=9999,
                 host_contrast='172.16.125.30', #b-nanomax-controlroom-cc-3
                 port_contrast=5556,
                 channel_xspress3=3,
                 plot_intervall_s=2, 
                 plot_min_data_n=5,
                 save_png=False,
                 verbosity=5):

        # checking that the listener is running on a compute nope
        if not self.running_on_compute_node():
            self.pretty_print_warning('You are not running this on a compute node. Consider starting it there')

        # where to listen for new spectra
        self.host_xspress3 = host_xspress3
        self.port_xspress3 = port_xspress3

        # where to read the respective positions from
        self.host_contrast = host_contrast
        self.port_contrast = port_contrast

        # setup the streaming connections
        context = zmq.Context()
        self.sock_xspress3 = context.socket(zmq.SUB)
        self.sock_xspress3.connect ("tcp://%s:%u" % (self.host_xspress3, self.port_xspress3))
        self.sock_xspress3.setsockopt(zmq.SUBSCRIBE, b"")

        self.sock_contrast = context.socket(zmq.SUB)
        self.sock_contrast.connect ("tcp://%s:%u" % (self.host_contrast, self.port_contrast))
        self.sock_contrast.setsockopt(zmq.SUBSCRIBE, b"")

        self.poller = zmq.Poller()
        self.poller.register(self.sock_contrast, zmq.POLLIN)
        self.poller.register(self.sock_xspress3, zmq.POLLIN)

        # where to read the ROI settings
        self.fpath_ROI_ini = fpath_ROI_ini     # which file to read the ROIs from
        self.channel_xspress3 = channel_xspress3 

        # how often and how much to output
        self.plot_intervall_s = plot_intervall_s  # wait how many data points before replotting
        self.plot_min_data_n = plot_min_data_n   # minimum number of data points before maps are plottet
        self.verbosity = verbosity         # how much print
        self.save_png = save_png

        # what to expect
        self.max_spectrum_length = 4096         

        self.load_ROI_ini()
        self.empty_data()
        self.init_plots()
        self.run()

    def run(self):
        while True:
            events = dict(self.poller.poll())

            # xspress3 did send a message
            if self.sock_xspress3 in events and events[self.sock_xspress3] == zmq.POLLIN:
                meta = self.sock_xspress3.recv_json()

                if meta['htype'] == 'image':
                    self.get_new_data(meta)


            # contrast did send a message
            if self.sock_contrast in events and events[self.sock_contrast] == zmq.POLLIN:
                meta = self.sock_contrast.recv_pyobj()

                # a scan has started
                if meta['status'] == 'started':
                    # throw away the (now) old data from the previous scan 
                    self.empty_data()
                    if self.verbosity >=3:
                        self.pretty_print_message('new scan', 'old data deleted')

                    self.current_scan = meta['scannr']
                    self.update_scannumber_in_plots()
                    if self.verbosity >=3:
                        self.pretty_print_message('new scan', 'number #'+str(self.current_scan))

                    # set a new directory for data to be written
                    self.set_out_dir_from_path(meta['path'])
                        

                # scan has finished / interrupted / aborted
                elif meta['status'] in ['finished', 'interrupted']:
                    if self.verbosity >=3:
                        self.pretty_print_message('scan over', 'updating one last time')

                    # update the plots one last time as there will be no more data for this plot
                    try:
                        self.calc_elemental_maps()
                        self.update_image_plots()
                        self.update_line_plots()
                    except:
                        self.pretty_print_error('could not update maps at the end of the scan')

                    # save the last status of the shown figures
                    try:
                        self.save_both_plots()
                    except:
                        pass

                    # clear the data 
                    # ... there might be a live view afterwards that we do not want to to mix into the scan
                    try:
                        self.empty_data()
                    except:
                        self.pretty_print_error('could not clear data at the end of the scan')

                # a data point was send
                elif meta['status'] == 'running':
                    sx, sy = meta['pseudo']['x'], meta['pseudo']['y']
                    for i, x in enumerate(sx):
                        self.add_new_position([sy[i],sx[i]])
            
                # just a heartbeat
                elif meta['status'] == 'heartbeat':
                    pass

            #####
            #   checking various things that would make an update of the plots unecessary 
            ####

            # is it not yet time to plot again?
            if not( self.time_of_last_plot==None or (time.time() - self.time_of_last_plot) >= self.plot_intervall_s):
                continue # start the loop from the beginning 
                    
            # are there not enough data points to plot?
            if not(self.n_data_points_xrf>=self.plot_min_data_n and self.n_data_points_xrf >= self.plot_min_data_n and self.n_data_points_pos >= self.plot_min_data_n):
                continue # start the loop from the beginning 
                    
            # has the data not changed since the last time the plot was done?
            if self.data_has_changed == False:
                continue # start the loop from the beginning 

            # ... update everything
            self.calc_elemental_maps()
            self.update_image_plots()
            self.update_line_plots()
            self.time_of_last_plot = time.time() 

            # ... and save the plots
            self.save_both_plots()
            

    ############################################################################
    #### methods for loading / getting and handling data
    ############################################################################

    def get_new_data(self, meta):
        # read the two buffered objects from the xspress3 stream
        buff = self.sock_xspress3.recv()
        extra = self.sock_xspress3.recv_pyobj()

        # form the image from the buffer
        m, n = meta['shape'][:2]
        frame = np.frombuffer(buff, dtype=meta['type']).reshape((m, n))
        frame_number = meta['frame']
        new_spectrum = frame[self.channel_xspress3, :]
        self.add_new_spectrum(new_spectrum)

        if self.verbosity >= 5:
            message = 'scan '+str(self.current_scan)+', frame '+str(frame_number)
            self.pretty_print_message('new spectrum', message)

    def load_ROI_ini(self):
        self.ROIs = {}    

        # if the given file exists ... read the ROIs defined in it
        if os.path.isfile(self.fpath_ROI_ini):
            config = configparser.ConfigParser()
            config.read(self.fpath_ROI_ini)
            section_keys = [x for x in config.sections() if 'ROI.roidict.' in x]
            for section_key in section_keys:
                name = config[section_key]['name']
                channel_from = int(math.floor(self.calibration_kev_to_channel(float(config[section_key]['from']))))
                channel_to = int(math.ceil(self.calibration_kev_to_channel(float(config[section_key]['to']))))
                if channel_to > self.max_spectrum_length: channel_to = self.max_spectrum_length
                self.ROIs[name] = [channel_from, channel_to] # in channels
            self.pretty_print_message('loaded ROI file', self.fpath_ROI_ini)
        # if there is no such file... just take the total sum
        else:
            self.pretty_print_warning('Could not find file: '+str(self.fpath_ROI_ini)+' to read specified ROIs. Taking the total sum of all channels as one ROI.')
            self.ROIs['Sum_all'] = [0,self.max_spectrum_length] # in channels

        # print the defined ROIs
        self.pretty_print_message('defined ROIs','')
        for key in self.ROIs.keys():
            print('\t', key.ljust(10), self.ROIs[key])

    def calibration_kev_to_channel(self, keV):
        channel = keV*100.
        if channel > self.max_spectrum_length: channel = self.max_spectrum_length
        if channel < 0: channel = 0
        return channel

    def empty_data(self):
        # empty the stored data and parmeters
        self.current_scan = None
        self.element_data = {}
        for ROI_name in self.ROIs.keys():
            self.element_data[ROI_name] = []
        self.positions = []
        self.element_maps = {}
        self.average_spectrum = None
        self.last_spectrum = None
        self.n_data_points_xrf = 0
        self.n_data_points_pos = 0
        self.time_of_last_plot = 0
        self.data_has_changed = False
        self.out_dir = None 
        self.pixel_resolution_nm = None  

    def get_resolution(self, f=0.25):
        # define a resolution to be used as pixel size in the interpolated maps
        # currently: a fraction of the distance between the first data points
        positions = np.array(self.positions)
        d_12 = np.sqrt( (positions[1,0]-positions[0,0])**2 + (positions[1,1]-positions[0,1])**2 )
        self.pixel_resolution_nm = f*d_12*1000.
        self.pretty_print_message('resolution set', str(self.pixel_resolution_nm)+' nm')

    def calc_elemental_maps(self):
        positions = np.array(self.positions)
        if self.pixel_resolution_nm==None: 
            self.get_resolution()

        # get minimum and maximum position in each direaction
        xmin = np.min(positions[:,1])-self.pixel_resolution_nm/1000.
        xmax = np.max(positions[:,1])+self.pixel_resolution_nm/1000.
        ymin = np.min(positions[:,0])-self.pixel_resolution_nm/1000.
        ymax = np.max(positions[:,0])+self.pixel_resolution_nm/1000.
        self.extent = [xmin, xmax, ymax, ymin]
        lpos = len(positions)

        # decide on many pixels to use for the maps
        dx_um = xmax-xmin
        dy_um = ymax-ymin
        nx = int(dx_um*1000./self.pixel_resolution_nm)
        ny = int(dy_um*1000./self.pixel_resolution_nm)
        #grid_x, grid_y = np.mgrid[xmin:xmax:nx*1j, ymin:ymax:ny*1j]
        grid_y, grid_x = np.mgrid[ymin:ymax:ny*1j, xmin:xmax:nx*1j]

        # interpolate the map for each ROI
        for key in self.ROIs.keys():
            values = np.array(self.element_data[key])
            lpos = len(positions)
            ldat = len(values)
            l = min(lpos,ldat)
            self.element_maps[key] = griddata(positions[:l], values[:l], (grid_y, grid_x), method='nearest')

    def add_new_spectrum(self, new_spectrum):
        # update the last buffered spectrum
        self.last_spectrum = new_spectrum.copy()
        # update the (running) average spectrum
        if self.n_data_points_xrf==0:
            self.average_spectrum = new_spectrum.copy()
        else:
            self.average_spectrum = (self.average_spectrum * self.n_data_points_xrf + new_spectrum)/(1. + self.n_data_points_xrf)
        # sum up according to the ROIs and attach to data lists
        for key in self.ROIs.keys():
            channel_from = self.ROIs[key][0]
            channel_to = self.ROIs[key][1]
            self.element_data[key].append(np.sum(new_spectrum[channel_from:channel_to]))
        # increase the counter for the number of recieved data points
        self.n_data_points_xrf +=1
        self.data_has_changed = True

    def add_new_position(self, new_position):
        # add the new position to the position list
        self.positions.append(new_position)
        self.n_data_points_pos +=1
        self.data_has_changed = True

    def running_on_compute_node(self):
        # define a check function to make sure the viewer is running on a machine
        # suited for the computational task
        if socket.gethostname().startswith('cn'):
            return True
        else:
            return False

    ############################################################################
    #### methods for outputting figures
    ############################################################################

    def init_plots(self):
        plt.ion()
        # create two figures and make the parts that need updadting easily
        # accessable through the class

        # one figure for plotting the average spectrum
        self.fig_0 = plt.figure(figsize=(8,4), facecolor='white')
        self.fig_0_ax = plt.subplot(1,1,1)
        self.fig_0_line_avg, = self.fig_0_ax.plot(np.arange(self.max_spectrum_length), lw=1, c='b')
        self.fig_0_line_last, = self.fig_0_ax.plot(np.arange(self.max_spectrum_length), lw=1, c='r', alpha=0.5)
        self.fig_0_title = plt.title('scan #'+str(self.current_scan))
        self.fig_0.canvas.set_window_title('average and most recent spectrum')
        # also plot the ROIs
        for key in self.ROIs.keys():
            if not key in ('ICR', 'Sum_all'):
                channel_from = self.ROIs[key][0]
                channel_to = self.ROIs[key][1]
                plt.axvspan(self.ROIs[key][0], self.ROIs[key][1], facecolor='y', alpha=0.4)
        plt.xlim(0,self.max_spectrum_length)
        plt.yscale('log')
        plt.xlabel('channel')
        plt.ylabel('counts')
        plt.grid()
        
        #figure out how many subplots lines and rows are needed for the elemental maps
        l = len(self.ROIs.keys())
        m = math.floor(np.sqrt(l))
        if m**2 < l:
            n = m+1
            if n*m < l:
                m = m+1
        else:
            n = m
                
        # one figure for the evolving maps
        self.fig_1 = plt.figure(figsize=(8,8), facecolor='white')
        self.fig_1_ax = {}
        self.fig_1_im = {}
        self.fig_1_title = {}
        for i, key in enumerate(sorted(self.ROIs.keys())):
            self.fig_1_ax[key] = plt.subplot(n,m,i+1)
            self.fig_1_im[key] = plt.imshow(np.zeros((2,2)), interpolation='None')
            self.fig_1_title[key] =  plt.title(key+' '+str(self.ROIs[key]))
            self.fig_1_ax[key].set_aspect('equal') 
        self.fig_1_suptitle = plt.suptitle('scan #'+str(self.current_scan))
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.fig_1.canvas.set_window_title('elemental maps')

        # draw the figures
        plt.draw()
        plt.pause(0.001)

    def update_line_plots(self):
        # update the line for the last recorded spectrum
        self.fig_0_line_last.set_data(np.arange(len(self.last_spectrum)), self.last_spectrum)
        # update the line for the average spectrum
        self.fig_0_line_avg.set_data(np.arange(len(self.average_spectrum)), self.average_spectrum)
        # update the y limits of the plot (lowest non 0 value and a bit more than the max value)
        ymax = max(np.max(self.last_spectrum), np.max(self.average_spectrum))
        #ymin = min(np.min(self.last_spectrum[self.last_spectrum>0]), np.min(self.average_spectrum[self.average_spectrum>0]))
        ymin = 0.01
        self.fig_0_ax.set_ylim(ymin, 1.1*ymax)

        # print a message
        if self.verbosity>=5:
            self.pretty_print_message('spectra updated', '')    

        # draw the figures
        plt.draw()
        plt.pause(0.001)
        self.data_has_changed = False

    def update_image_plots(self):
        # update the average and last recorded spectrum plot
        for i, key in enumerate(sorted(self.ROIs.keys())):
            # replace the image data
            self.fig_1_im[key].set_data(self.element_maps[key])  
            #update the extent of the image ... to show proper positions 
            self.fig_1_im[key].set_extent(self.extent)  
            # set new updated color limits, as max/min value in the image could have changed
            self.fig_1_im[key].set_clim([np.min(self.element_maps[key]),np.max(self.element_maps[key])])       

        # print a message
        if self.verbosity>=5:
            self.pretty_print_message('elemental maps updated', '')

        # draw the figures
        plt.draw()
        plt.pause(0.001)
        self.data_has_changed = False

    def update_scannumber_in_plots(self):
        self.fig_0_title.set_text('scan #'+str(self.current_scan))
        self.fig_1_suptitle.set_text('scan #'+str(self.current_scan))
        plt.draw()
        plt.pause(0.001)


    ############################################################################
    #   methods for saving the plots
    ############################################################################

    def set_out_dir_from_path(self, path):
        sample = path.split('/')[-1]
        base_visit = path.split('raw')[0]
        self.out_dir = base_visit+'process/'+sample+'/scan_' + str(self.current_scan).zfill(6) + '/zmq_xrf_livemap/'
        if self.verbosity >=5:
            self.pretty_print_message('set new save path', self.out_dir)

        if os.path.exists(self.out_dir):
            pass
        else:
            try: 
                os.makedirs(self.out_dir, exist_ok=True)
            except:
                self.pretty_print_error('could not create directory: '+str(self.out_dir))
                self.pretty_print_warning('plots will not be saved')
                self.out_dir = None

    def save_both_plots(self):
        if self.save_png and self.out_dir!=None:
            time_str = time.strftime("%Y-%m-%d_%H%M%S") 
            fout_path0 = self.out_dir+'fig0_XRF_spectrum_'+time_str+'.png'
            fout_path1 = self.out_dir+'fig0_XRF_maps_'+time_str+'.png'

            try:
                self.fig_0.savefig(fout_path0, dpi=300)
            except:
                if self.verbosity>=5:
                    self.pretty_print_error('could not save plot of the XRF spectrum: '+str(fout_path0))

            try:
                self.fig_1.savefig(fout_path1, dpi=300)
            except:
                if self.verbosity>=5:
                    self.pretty_print_error('could not save plot of the XRf maps: '+str(fout_path1))

    ############################################################################
    #### methods for outputting text stuff
    ############################################################################

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

################################################################################
#   run an instance of the XRF_scanliveview class
################################################################################

if __name__ == "__main__":

    # check if a file path to a ini file for XRF ROIs was given
    if len(sys.argv)>=2:
        fpath = sys.argv[1]
    else:
        fpath = './ROIs_test.ini'            

    # start the actual liveViewer
    liveviewer = XRF_scanliveview(fpath_ROI_ini=fpath,
                                  host_xspress3='172.16.126.70', #b303a-a100380-cab-dia-detxfcu-01
                                  port_xspress3=9999,
                                  host_contrast='172.16.125.30', #b-nanomax-controlroom-cc-3
                                  port_contrast=5556,
                                  channel_xspress3=3,
                                  plot_intervall_s=2, 
                                  plot_min_data_n=5,
                                  verbosity=5)
    liveviewer.run()
