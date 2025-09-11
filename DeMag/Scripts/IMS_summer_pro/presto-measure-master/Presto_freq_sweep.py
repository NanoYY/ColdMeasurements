from sweep import Sweep
import numpy as np

experiment = Sweep(
    freq_center=3.79885e9,
    freq_span=6e6,
    df=100e3,
    num_averages=100,
    amp=inputConv(-6,0.7),
    output_port=1,
    input_port=1,
)

presto_address = "169.254.3.14"  # your Presto IP address
save_filename = experiment.run(presto_address)

experiment.analyze()

def inputConv(dBm, amplification): #[Amplification] = dB
    maxP = 1e-3*np.power(10,-6/10) #W
    dBm_val = dBm - amplification
    P = 1e-3*np.power(10,dBm_val/10) #W
    AMP = (P/maxP) #Amplitude of a single peak
    return AMP