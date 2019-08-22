import numpy as np

# CXRO table of transmission through 1 m air at 1 atm and 293K
# N1.562O.42C.0003Ar.0094 Pressure=760. Path=100. cm],
# Photon Energy (eV), Transmission],
air_table=np.array([
     [5000.0, 0.81598E-02],
     [5050.0, 0.94049E-02],
     [5100.0, 0.10781E-01],
     [5150.0, 0.12294E-01],
     [5200.0, 0.13950E-01],
     [5250.0, 0.15755E-01],
     [5300.0, 0.17713E-01],
     [5350.0, 0.19828E-01],
     [5400.0, 0.22104E-01],
     [5450.0, 0.24546E-01],
     [5500.0, 0.27155E-01],
     [5550.0, 0.29934E-01],
     [5600.0, 0.32884E-01],
     [5650.0, 0.36004E-01],
     [5700.0, 0.39299E-01],
     [5750.0, 0.42765E-01],
     [5800.0, 0.46405E-01],
     [5850.0, 0.50214E-01],
     [5900.0, 0.54194E-01],
     [5950.0, 0.58340E-01],
     [6000.0, 0.62650E-01],
     [6050.0, 0.67122E-01],
     [6100.0, 0.71754E-01],
     [6150.0, 0.76540E-01],
     [6200.0, 0.81476E-01],
     [6250.0, 0.86558E-01],
     [6300.0, 0.91780E-01],
     [6350.0, 0.97139E-01],
     [6400.0, 0.10263],
     [6450.0, 0.10825],
     [6500.0, 0.11399],
     [6550.0, 0.11984],
     [6600.0, 0.12582],
     [6650.0, 0.13189],
     [6700.0, 0.13806],
     [6750.0, 0.14433],
     [6800.0, 0.15068],
     [6850.0, 0.15711],
     [6900.0, 0.16362],
     [6950.0, 0.17021],
     [7000.0, 0.17685],
     [7050.0, 0.18356],
     [7100.0, 0.19032],
     [7150.0, 0.19713],
     [7200.0, 0.20399],
     [7250.0, 0.21089],
     [7300.0, 0.21782],
     [7350.0, 0.22478],
     [7400.0, 0.23176],
     [7450.0, 0.23877],
     [7500.0, 0.24579],
     [7550.0, 0.25282],
     [7600.0, 0.25986],
     [7650.0, 0.26691],
     [7700.0, 0.27395],
     [7750.0, 0.28099],
     [7800.0, 0.28802],
     [7850.0, 0.29505],
     [7900.0, 0.30205],
     [7950.0, 0.30904],
     [8000.0, 0.31601],
     [8050.0, 0.32295],
     [8100.0, 0.32988],
     [8150.0, 0.33677],
     [8200.0, 0.34364],
     [8250.0, 0.35047],
     [8300.0, 0.35727],
     [8350.0, 0.36403],
     [8400.0, 0.37075],
     [8450.0, 0.37743],
     [8500.0, 0.38407],
     [8550.0, 0.39066],
     [8600.0, 0.39721],
     [8650.0, 0.40371],
     [8700.0, 0.41016],
     [8750.0, 0.41657],
     [8800.0, 0.42292],
     [8850.0, 0.42922],
     [8900.0, 0.43547],
     [8950.0, 0.44166],
     [9000.0, 0.44780],
     [9050.0, 0.45389],
     [9100.0, 0.45992],
     [9150.0, 0.46589],
     [9200.0, 0.47181],
     [9250.0, 0.47766],
     [9300.0, 0.48346],
     [9350.0, 0.48921],
     [9400.0, 0.49490],
     [9450.0, 0.50052],
     [9500.0, 0.50609],
     [9550.0, 0.51160],
     [9600.0, 0.51705],
     [9650.0, 0.52245],
     [9700.0, 0.52778],
     [9750.0, 0.53306],
     [9800.0, 0.53828],
     [9850.0, 0.54344],
     [9900.0, 0.54854],
     [9950.0, 0.55358],
     [10000., 0.55857],
     [10050., 0.56350],
     [10100., 0.56837],
     [10150., 0.57319],
     [10200., 0.57795],
     [10250., 0.58266],
     [10300., 0.58731],
     [10350., 0.59190],
     [10400., 0.59644],
     [10450., 0.60092],
     [10500., 0.60535],
     [10550., 0.60972],
     [10600., 0.61404],
     [10650., 0.61831],
     [10700., 0.62252],
     [10750., 0.62669],
     [10800., 0.63080],
     [10850., 0.63486],
     [10900., 0.63886],
     [10950., 0.64282],
     [11000., 0.64673],
     [11050., 0.65059],
     [11100., 0.65440],
     [11150., 0.65816],
     [11200., 0.66187],
     [11250., 0.66554],
     [11300., 0.66916],
     [11350., 0.67274],
     [11400., 0.67626],
     [11450., 0.67974],
     [11500., 0.68318],
     [11550., 0.68658],
     [11600., 0.68993],
     [11650., 0.69323],
     [11700., 0.69650],
     [11750., 0.69972],
     [11800., 0.70290],
     [11850., 0.70604],
     [11900., 0.70913],
     [11950., 0.71219],
     [12000., 0.71521],
     [12050., 0.71819],
     [12100., 0.72113],
     [12150., 0.72403],
     [12200., 0.72690],
     [12250., 0.72972],
     [12300., 0.73252],
     [12350., 0.73527],
     [12400., 0.73799],
     [12450., 0.74067],
     [12500., 0.74332],
     [12550., 0.74594],
     [12600., 0.74852],
     [12650., 0.75106],
     [12700., 0.75358],
     [12750., 0.75606],
     [12800., 0.75851],
     [12850., 0.76093],
     [12900., 0.76331],
     [12950., 0.76567],
     [13000., 0.76799],
     [13050., 0.77029],
     [13100., 0.77255],
     [13150., 0.77479],
     [13200., 0.77700],
     [13250., 0.77918],
     [13300., 0.78133],
     [13350., 0.78345],
     [13400., 0.78555],
     [13450., 0.78762],
     [13500., 0.78966],
     [13550., 0.79168],
     [13600., 0.79367],
     [13650., 0.79563],
     [13700., 0.79757],
     [13750., 0.79949],
     [13800., 0.80138],
     [13850., 0.80325],
     [13900., 0.80509],
     [13950., 0.80691],
     [14000., 0.80871],
     [14050., 0.81048],
     [14100., 0.81224],
     [14150., 0.81397],
     [14200., 0.81567],
     [14250., 0.81736],
     [14300., 0.81903],
     [14350., 0.82067],
     [14400., 0.82230],
     [14450., 0.82390],
     [14500., 0.82548],
     [14550., 0.82705],
     [14600., 0.82859],
     [14650., 0.83012],
     [14700., 0.83162],
     [14750., 0.83311],
     [14800., 0.83458],
     [14850., 0.83603],
     [14900., 0.83746],
     [14950., 0.83888],
     [15000., 0.84028],
     [15050., 0.84166],
     [15100., 0.84303],
     [15150., 0.84438],
     [15200., 0.84572],
     [15250., 0.84703],
     [15300., 0.84834],
     [15350., 0.84962],
     [15400., 0.85089],
     [15450., 0.85215],
     [15500., 0.85339],
     [15550., 0.85462],
     [15600., 0.85583],
     [15650., 0.85702],
     [15700., 0.85821],
     [15750., 0.85937],
     [15800., 0.86053],
     [15850., 0.86167],
     [15900., 0.86280],
     [15950., 0.86391],
     [16000., 0.86501],
     [16050., 0.86610],
     [16100., 0.86717],
     [16150., 0.86823],
     [16200., 0.86928],
     [16250., 0.87032],
     [16300., 0.87134],
     [16350., 0.87235],
     [16400., 0.87336],
     [16450., 0.87434],
     [16500., 0.87532],
     [16550., 0.87629],
     [16600., 0.87724],
     [16650., 0.87819],
     [16700., 0.87912],
     [16750., 0.88004],
     [16800., 0.88095],
     [16850., 0.88186],
     [16900., 0.88275],
     [16950., 0.88363],
     [17000., 0.88450],
     [17050., 0.88536],
     [17100., 0.88621],
     [17150., 0.88705],
     [17200., 0.88788],
     [17250., 0.88870],
     [17300., 0.88952],
     [17350., 0.89032],
     [17400., 0.89112],
     [17450., 0.89190],
     [17500., 0.89268],
     [17550., 0.89345],
     [17600., 0.89421],
     [17650., 0.89496],
     [17700., 0.89570],
     [17750., 0.89643],
     [17800., 0.89716],
     [17850., 0.89788],
     [17900., 0.89859],
     [17950., 0.89929],
     [18000., 0.89999],
     [18050., 0.90067],
     [18100., 0.90135],
     [18150., 0.90203],
     [18200., 0.90269],
     [18250., 0.90335],
     [18300., 0.90400],
     [18350., 0.90464],
     [18400., 0.90528],
     [18450., 0.90591],
     [18500., 0.90653],
     [18550., 0.90715],
     [18600., 0.90776],
     [18650., 0.90836],
     [18700., 0.90896],
     [18750., 0.90955],
     [18800., 0.91013],
     [18850., 0.91071],
     [18900., 0.91128],
     [18950., 0.91184],
     [19000., 0.91240],
     [19050., 0.91296],
     [19100., 0.91350],
     [19150., 0.91405],
     [19200., 0.91458],
     [19250., 0.91511],
     [19300., 0.91564],
     [19350., 0.91616],
     [19400., 0.91667],
     [19450., 0.91718],
     [19500., 0.91768],
     [19550., 0.91818],
     [19600., 0.91867],
     [19650., 0.91916],
     [19700., 0.91964],
     [19750., 0.92012],
     [19800., 0.92059],
     [19850., 0.92106],
     [19900., 0.92152],
     [19950., 0.92197],
     [20000., 0.92243],
     [20050., 0.92288],
     [20100., 0.92332],
     [20150., 0.92377],
     [20200., 0.92421],
     [20250., 0.92464],
     [20300., 0.92507],
     [20350., 0.92550],
     [20400., 0.92592],
     [20450., 0.92634],
     [20500., 0.92675],
     [20550., 0.92716],
     [20600., 0.92757],
     [20650., 0.92797],
     [20700., 0.92837],
     [20750., 0.92876],
     [20800., 0.92915],
     [20850., 0.92953],
     [20900., 0.92992],
     [20950., 0.93030],
     [21000., 0.93067],
     [21050., 0.93104],
     [21100., 0.93141],
     [21150., 0.93177],
     [21200., 0.93213],
     [21250., 0.93249],
     [21300., 0.93284],
     [21350., 0.93319],
     [21400., 0.93354],
     [21450., 0.93388],
     [21500., 0.93422],
     [21550., 0.93456],
     [21600., 0.93489],
     [21650., 0.93523],
     [21700., 0.93555],
     [21750., 0.93588],
     [21800., 0.93620],
     [21850., 0.93652],
     [21900., 0.93683],
     [21950., 0.93714],
     [22000., 0.93745],
     [22050., 0.93776],
     [22100., 0.93806],
     [22150., 0.93836],
     [22200., 0.93866],
     [22250., 0.93896],
     [22300., 0.93925],
     [22350., 0.93954],
     [22400., 0.93983],
     [22450., 0.94011],
     [22500., 0.94039],
     [22550., 0.94067],
     [22600., 0.94095],
     [22650., 0.94122],
     [22700., 0.94150],
     [22750., 0.94177],
     [22800., 0.94203],
     [22850., 0.94230],
     [22900., 0.94256],
     [22950., 0.94282],
     [23000., 0.94308],
     [23050., 0.94333],
     [23100., 0.94358],
     [23150., 0.94384],
     [23200., 0.94408],
     [23250., 0.94433],
     [23300., 0.94457],
     [23350., 0.94481],
     [23400., 0.94505],
     [23450., 0.94529],
     [23500., 0.94553],
     [23550., 0.94576],
     [23600., 0.94599],
     [23650., 0.94622],
     [23700., 0.94645],
     [23750., 0.94667],
     [23800., 0.94690],
     [23850., 0.94712],
     [23900., 0.94734],
     [23950., 0.94755],
     [24000., 0.94777],
     [24050., 0.94798],
     [24100., 0.94820],
     [24150., 0.94841],
     [24200., 0.94861],
     [24250., 0.94882],
     [24300., 0.94903],
     [24350., 0.94923],
     [24400., 0.94943],
     [24450., 0.94963],
     [24500., 0.94983],
     [24550., 0.95002],
     [24600., 0.95022],
     [24650., 0.95041],
     [24700., 0.95060],
     [24750., 0.95079],
     [24800., 0.95098],
     [24850., 0.95116],
     [24900., 0.95135],
     [24950., 0.95153],
     [25000., 0.95171],
     [25050., 0.95189],
     [25100., 0.95207],
     [25150., 0.95225],
     [25200., 0.95243],
     [25250., 0.95260],
     [25300., 0.95277],
     [25350., 0.95295],
     [25400., 0.95312],
     [25450., 0.95328],
     [25500., 0.95345],
     [25550., 0.95362],
     [25600., 0.95378],
     [25650., 0.95394],
     [25700., 0.95411],
     [25750., 0.95427],
     [25800., 0.95443],
     [25850., 0.95458],
     [25900., 0.95474],
     [25950., 0.95490],
     [26000., 0.95505],
     [26050., 0.95520],
     [26100., 0.95535],
     [26150., 0.95550],
     [26200., 0.95565],
     [26250., 0.95580],
     [26300., 0.95595],
     [26350., 0.95609],
     [26400., 0.95624],
     [26450., 0.95638],
     [26500., 0.95652],
     [26550., 0.95667],
     [26600., 0.95681],
     [26650., 0.95694],
     [26700., 0.95708],
     [26750., 0.95722],
     [26800., 0.95735],
     [26850., 0.95749],
     [26900., 0.95762],
     [26950., 0.95775],
     [27000., 0.95789],
     [27050., 0.95802],
     [27100., 0.95815],
     [27150., 0.95827],
     [27200., 0.95840],
     [27250., 0.95853],
     [27300., 0.95865],
     [27350., 0.95878],
     [27400., 0.95890],
     [27450., 0.95902],
     [27500., 0.95915],
     [27550., 0.95927],
     [27600., 0.95939],
     [27650., 0.95950],
     [27700., 0.95962],
     [27750., 0.95974],
     [27800., 0.95986],
     [27850., 0.95997],
     [27900., 0.96009],
     [27950., 0.96020],
     [28000., 0.96031],
     [28050., 0.96042],
     [28100., 0.96053],
     [28150., 0.96064],
     [28200., 0.96075],
     [28250., 0.96086],
     [28300., 0.96097],
     [28350., 0.96108],
     [28400., 0.96118],
     [28450., 0.96129],
     [28500., 0.96139],
     [28550., 0.96150],
     [28600., 0.96160],
     [28650., 0.96170],
     [28700., 0.96180],
     [28750., 0.96190],
     [28800., 0.96200],
     [28850., 0.96210],
     [28900., 0.96220],
     [28950., 0.96230],
     [29000., 0.96239],
     [29050., 0.96249],
     [29100., 0.96259],
     [29150., 0.96268],
     [29200., 0.96278],
     [29250., 0.96287],
     [29300., 0.96296],
     [29350., 0.96305],
     [29400., 0.96315],
     [29450., 0.96324],
     [29500., 0.96333],
     [29550., 0.96342],
     [29600., 0.96350],
     [29650., 0.96359],
     [29700., 0.96368],
     [29750., 0.96377],
     [29800., 0.96385],
     [29850., 0.96394],
     [29900., 0.96402],
     [29950., 0.96411],
     [30000., 0.96419]])

def air_mu(E):
     """
     Returns the interpolated air attenuation coefficient for the
     given energy (given in eV). The relation between transmission (T),
     attenuation coefficient (mu, in 1/cm) and path length (l, in cm)
     is as follows.

     T = exp(-mu * l)
     """
     T = np.interp(E, air_table[:,0], air_table[:,1])
     return -np.log(T) / 100.0

class Ionchamber(object):

     def __init__(self, length, energy, gas='air'):
          """
          Takes a length in cm and an energy in eV.
          """
          self.length = length
          self.energy = energy
          if gas == 'air':
               self.mu = air_mu
          else:
               raise NotImplementedError('Only air is supported!')

     @property
     def current_per_flux(self):
          e = 1.602e-19
          T = np.exp(-self.mu(self.energy) * self.length)
          return self.energy * e * (1 - T) / 34.4

     def flux(self, current):
          """
          Returns the flux as function of the measured current.
          """
          return current / self.current_per_flux