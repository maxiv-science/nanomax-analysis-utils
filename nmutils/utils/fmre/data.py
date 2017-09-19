# Starts d variable as Object
class Data():
    def __init__(self):
        self.dataPath=""
        self.datafile=""
        self.ProbePath=""
        self.ProbeDataFile=""
        self.x=[]
        self.y=[]
        self.pixsize=[]
        self.fluomap=[]
        self.probe=[]
        self.probe_rotate=False
        self.gridx=[]
        self.gridy=[]
        self.EFM=[]
        self.probe_big_fft_forward=[]
        self.probe_big_fft_backward=[]
        self.interp_method=None
        self.initialized=0
        self.reg_param=1.9
        self.show=1
        self.n_iter=30
        self.non_neg=1
        self.method='landweber'
        self.residuals=[]
        self.b=[]
        self.Atb=[]
        self.slowdown=2
        self.obj=[]
        self.roi=[]


