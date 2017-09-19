# -*- coding: utf-8 -*-
"""
Created on Mon Aug 28 14:33:07 2017
Landweber iteration method and Conjugate Gradient method algorithms for solving 
linear system of equations. The 'forward' and 'backward' operations are performed
by the projectors 'forwardfluo' and 'backwardfluo' (see documentation if required)
In the Landweber algorithm the first principal value (required for step-size 
computation of the optimization routine) is calculated using the Simple Power Method

The conjugate gradient method (CGM) is equivalent to the CGLs algorithm when
no regularization term is used (or regularization parameter=0).
The function regterm computes the Tikhonov or Total Variation regularization terms
to be applied in the CGM algorithm if desired
@author: tiagoj
"""
from __future__ import print_function  #So you can use it with python 3
from time import clock as tic
import projectors as p
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import convolve2d

def landweber(self):
    if self.initialized==0:
        self=p.initialize(self)
    #CALCULATE LARGEST SINGULAR VALUE - sigma1 - Power method for approximate sigma1
    print('Starting eigenvalue computation...')
    t=tic() 
    numiter=20
    tol=1e-6
    sigma_old=-float('Inf')
    aux=self
    aux.EFM=np.ones(np.shape(aux.EFM))#aux.EFM*0#np.zeros((len(self.EFM.flatten()),1))
    aux.b=np.ones(np.shape(aux.fluomap))#aux.fluomap*0
    for k in range(0,numiter):
        #Do not forget after running forwardfluo 'b' is updated in the data class. So compute b2 first and then b1
        b2=p.backwardfluo(aux).Atb
        b1=p.forwardfluo(aux).b
        B=np.concatenate((b1.flatten(),b2.flatten()))
        sigma1=np.sqrt(np.dot(B,B))
        aux.EFM=b2/sigma1
        aux.b=b1/sigma1
        rel_dif=abs(sigma1-sigma_old)/(sigma_old)
        if np.isnan(rel_dif):
            rel_dif=tol
        if rel_dif<tol:
            break
        sigma_old=sigma1
    t=tic()-t
    print ('Done in',round(t),'secs. sigma1=',round(sigma1*1000)/1000)
    #-------------------------------------------------------------------------#
    #Open figure if show=1
    if self.show:
        plt.close("all")
        fig=plt.figure(figsize=(17,5))
        plt.ion()
#        plt.show()
    
    #START ITERATION LOOP
    lambd=self.reg_param/(sigma1*sigma1)
    self.residuals=[]
    for k in range(0,self.n_iter):
        print("Iteration %d" % k)
        #Compute residual vector and check its norm
        r=p.forwardfluo(self).b-self.fluomap
        self.residuals=np.append(self.residuals,0.5*np.dot(r,r))
        if k<0 and self.residuals[k]>self.residuals[k-1]:
            print('The residual became higher at this iteration. Stopping at current iteration :',k)
            self.EFM=self.EFM_previous
            break
        self.EFM_previous=self.EFM
        self.b=r
        self.EFM=self.EFM-lambd*p.backwardfluo(self).Atb
        #APPLY NON NEGATIVITY CONSTRAINT
        if self.non_neg:
            self.EFM[self.EFM<=0]=0
        
        if self.show:
            imageEFM(self,fig,k)
    
    self.EFM[self.EFM<0]=0
    return self

def CGM(self):
    #Please note that the conjugate gradient method does not solve Ax=b, but A'Ax=A'b
    #Initialize
    if self.initialized==0:
        self=p.initialize(self)
    self.residuals=[]
    self.EFM=self.EFM*0
    aux=self
    b=aux.fluomap
    aux.b=b
    r0=p.backwardfluo(aux).Atb-aux.reg_param*regterm(self.EFM,aux.method)
    pp=r0
    rk=r0
    #Open figure if show=1
    if self.show:
        plt.close("all")
        fig=plt.figure(figsize=(17,5))
    #------------------------------------------------------------------------#
    for k in range(0,self.n_iter-1):
        print("Iteration %d" % k)
        aux.EFM=pp
        App=p.forwardfluo(aux).b
                         
        alpha=np.dot(rk.flatten(),rk.flatten())/np.dot(App.flatten(),App.flatten())
        alpha=alpha/self.slowdown # I reduced the stepsize so it can converge slower
        self.EFM_previous=self.EFM
        self.EFM=self.EFM+alpha*pp
        if aux.non_neg:
            self.EFM[self.EFM<0]=0
        
        aux.b=App
        AtApp=p.backwardfluo(aux).Atb+aux.reg_param*regterm(self.EFM,aux.method)
        rk=rk-alpha*AtApp
        
        beta=np.dot(rk.flatten(),rk.flatten())/np.dot(r0.flatten(),r0.flatten())
        if beta>1 and k>0:
            print('The residual became higher at this iteration. Stopping at current iteration :',k)
            self.EFM=self.EFM_previous
            break
        r0=rk
        pp=rk+beta*pp
        
        self.residuals=np.append(self.residuals,np.dot(rk.flatten(),rk.flatten()))
                
        if self.show:
            imageEFM(self,fig,k)
    
    self.EFM[self.EFM<0]=0                    
    return self

def regterm(EFM,method):
    if method=='Tik':
#        reg=np.dot(EFM.flatten(),EFM.flatten())
        reg=EFM
    elif method=='TV':
        kern_lap=-np.array([[1,1,1],[1,-8,1],[1,1,1]])*1/3
        reg=convolve2d(EFM,kern_lap,mode='same',boundary='fill',fillvalue=0)
    else:
        reg=0
    return reg

def SIRT(self):
    #USES THE SIRT ALGORITHM TO SOLVE THE SYSTEM OF EQUATIONS AX=b (minimizes |Ax-b|_R) which is a weighted norm
    #Initialize: Compute Weight matrices C and R (or equivalent operation)
    if self.initialized==0:
        self=p.initialize(self)
    aux=self
    aux.b=np.ones_like(aux.b)
    C=p.backwardfluo(aux).Atb
    C=1/C
    C[np.isinf(C)]=0
    aux.EFM=np.ones_like(aux.EFM)
    R=p.forwardfluo(aux).b
    R=1/R
    R[np.isinf(R)]=0
    #Open figure if show=1
    if self.show:
        plt.close("all")
        fig=plt.figure(figsize=(17,5))
        plt.ion()
#        plt.show()
    
    #START ITERATION LOOP
    self.residuals=[]
    for k in range(0,self.n_iter):
        print("Iteration %d" % k)
        #Compute residual vector and check its norm
        r=self.fluomap-p.forwardfluo(self).b
        self.residuals=np.append(self.residuals,0.5*np.dot(r,r))
        if k<0 and self.residuals[k]>self.residuals[k-1]:
            print('The residual became higher at this iteration. Stopping at current iteration :',k)
            self.EFM=self.EFM_previous
            break
        self.EFM_previous=self.EFM
        self.b=np.multiply(R,r)
        self.EFM=self.EFM+np.multiply(C,p.backwardfluo(self).Atb)
        #APPLY NON NEGATIVITY CONSTRAINT
        if self.non_neg:
            self.EFM[self.EFM<=0]=0
        
        if self.show:
            imageEFM(self,fig,k)
    
    self.EFM[self.EFM<0]=0
    return self
            
def imageEFM(self,fig,k):
    plt.ion()
    asize=int(np.sqrt(len(self.probe))/2) #Here divide by 2. The Enhanced Fluorescence Map has a border with side equal to half the probe width (distance to the centre)
    ax1=fig.add_subplot(221)
    ax2=fig.add_subplot(222)
    ax3=fig.add_subplot(223)
    ax4=fig.add_subplot(224)
    ax1.imshow(self.fluomap2d)
    ax1.grid(False)
#    ax1.invert_yaxis()
    ax1.set_title('Measured Fluorescence Map')
#    X=self.EFM
    X=self.EFM[asize:-asize,asize:-asize]
    X[X<0]=0
    ax2.imshow(X)#,cmap='gist_rainbow')#cmap='plasma')
    ax2.grid(False)
#    ax2.invert_yaxis()
    ax2.set_title('Enhanced Fluorescence Map')
    ax3.clear()
    ax3.plot(range(0,k+1),self.residuals)
    ax3.set_title('Residual norm evolution')
    ax3.set_xlabel('Iteration number')
    ax3.set_ylabel('$\sum\||\mathbf{r}\||^2$')
    ax4.imshow(np.angle(self.obj[asize:-asize,asize:-asize]))
    ax4.grid(False)
    ax4.set_title('Phase Object')
    plt.draw()
#    sleep(0.0001)
    plt.pause(0.000001)
#    return X
    
        
        
        
    