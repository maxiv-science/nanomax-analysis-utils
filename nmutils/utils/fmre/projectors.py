# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 09:39:49 2017
Definition of Forward and Backward operators for the "Fluorescence Mapping" 
operation. The class Data to be used as input is constantly being updated when
necessary
There are 3 functions defined in this file:
    forwardfluo: takes the (current) Enhanced Fluorescence Map (EFM) and 
                computes 'synthetic' fluorescence measurements by applying a 
                convolution with the measured probe intensity function 
                (via FFT theorem) and evaluating the fluorescence measurement 
                at the coordinates self.x and self.y. Since the convolution 
                operation is performed using the Fourier Transform convolution
                theorem, the FFT of the probe array is computed once.
                Computes b=Ax
    backfluo:   Takes the current 'synthetic' fluorescence map, (or residual 
                vector) and applies the transpose operation A'b (or A'r). This 
                projector operator is also computed in 2 different steps. First
                a 'back-sampling' operation assigns the values of the synthetic
                fluorescence map or residual vector to the scanning coordinates
                Then a 2D convolution with the probe function (rotated by 180 deg)
                is applied.
@author: Tiago Ramos (tiagoj@dtu.dk)
"""
#Define forward and backward projectors for optimization functions
import numpy as np
from scipy.interpolate import griddata
from scipy import ndimage

def forwardfluo(self):
    if self.initialized==0:
        self=initialize(self)
    #Compute convolution by Fourier Theorem
    b=np.fft.ifft2(np.fft.fft2(self.EFM)*self.probe_big_fft_forward)
    b=np.real(b)
    #Compute syntetic measurement at coordinates (Self.x,self.y)
    ##COMPUTE SAMPLING
    self.b=ndimage.map_coordinates(b,(self.y,self.x),order=3)
    self.b[np.isnan(self.b)]=0
    return self

def backwardfluo(self):
    if self.initialized==0:
        self=initialize(self)
    #Re-sample operation
    if self.interp_method=='None':
        b2=backsample(self.x,self.y,self.b,self.gridx,self.gridy)
    else:
        a=int(self.asize/2)
        b2=griddata((self.x,self.y),self.b,(self.gridx,self.gridy),method=self.interp_method,fill_value=0)
#        b2[0:a-1,:]=0
#        b2[-a+1:-1,:]=0
#        b2[:,0:a-1]=0
#        b2[:,-a+1:-1]=0
        b2=b2*sum(self.b.flatten())/(sum(b2.flatten())+1e-30) #This should be here to correct the measurements intensities
    #Compute convolution by Fourier Theorem
    Atb=np.fft.ifft2(np.fft.fft2(b2)*self.probe_big_fft_backward)
    self.Atb=np.real(Atb)
    self.Atb[np.isnan(self.Atb)]=0
    return self
    
def backsample(x,y,b,gridx,gridy):
    ix=x.astype(int)
    iy=y.astype(int)
    b2=np.zeros(np.shape(gridx))
    b2[iy,ix]=b
    return b2

def initialize(self):
    #Convert probe to abs and normalize its sum to 1
    self.probe=abs(self.probe)
    self.probe=self.probe/sum(self.probe.flatten())
    #Correct scan pos vector by probe size
    self.probe=self.probe.flatten()
    asize=np.floor(np.sqrt(len(self.probe)))
    mxy=np.subtract([np.min(self.x),np.min(self.y)],[np.floor(asize/2),np.floor(asize/2)])
    offsets=np.empty(len(self.x))
    offsets.fill(mxy[0])
    self.x=self.x-offsets
    offsets.fill(mxy[1])
    self.y=self.y-offsets
    # Reshape to 2D array
    N=np.floor(np.max(self.x)+np.ceil(asize/2))
    M=np.floor(np.max(self.y)+np.ceil(asize/2))
    
    #CALCULATE MESHGRIDS 
    if len(self.gridx)*len(self.gridy)==0:
        xx,yy=np.meshgrid(list(range(int(N))),list(range(int(M))))
        self.gridx=xx
        self.gridy=yy
    if len(self.EFM)==0:
        self.EFM=self.fluomap
        self.EFM=griddata((self.x,self.y),self.EFM,(self.gridx,self.gridy))
        self.EFM[np.isnan(self.EFM)]=0

    # Rotate probe if necessary    
    probe=np.reshape(self.probe,[asize.astype(int),asize.astype(int)])
    if self.probe_rotate:
            probe=np.rot90(probe,2)
            
    #Make Probe 2D (if unexistent), large and store its fft2
    if len(self.probe_big_fft_forward)==0:
        probe_big=np.pad(probe,((0,int(M-asize)),(0,int(N-asize))),mode='constant',constant_values=0)
        # Probe center in [0,0] position
        probe_big=np.roll(probe_big,-int(np.floor(asize/2)),axis=0)
        probe_big=np.roll(probe_big,-int(np.floor(asize/2)),axis=1)
        self.probe_big_fft_forward=np.fft.fft2(probe_big)
    
    #Make Probe 2D, large and store its fft2. Note here that the kernel is 
    #rotated 180 degrees in comparison with the forward operator
    if len(self.probe_big_fft_backward)==0:
        probe=np.rot90(probe,2)
        probe_big=np.pad(probe,((0,int(M-asize)),(0,int(N-asize))),mode='constant',constant_values=0)
        # Probe center in [0,0] position
        probe_big=np.roll(probe_big,-int(np.floor(asize/2)),axis=0)
        probe_big=np.roll(probe_big,-int(np.floor(asize/2)),axis=1)
        self.probe_big_fft_backward=np.fft.fft2(probe_big)
    
    self.b=self.fluomap
    #IN CASE THE FLUOMAP WAS INTRODUCED AS VECTOR:
    asize=int(np.sqrt(len(self.probe))/2) #Here divide by 2. The Enhanced Fluorescence Map has a border with side equal to half the probe width (distance to the centre)
    self.fluomap2d=griddata((self.x,self.y),self.b,(self.gridx,self.gridy),method='nearest',fill_value=0)
    self.fluomap2d=self.fluomap2d[asize:-asize,asize:-asize]
    self.asize=np.sqrt(len(self.probe))
    self.initialized=1
    return self    

 