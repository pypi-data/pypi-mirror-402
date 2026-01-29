import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm.notebook import trange
from .math import u2i, wrap

def sample_kingst(kingst_csv, fs, length=-1):
    kingst = pd.read_csv(kingst_csv, encoding='gb2312', index_col=0)
    time = kingst.index[-1] - kingst.index[0]
    if length <= 0:
        length = np.ceil(time*fs)
    length = int(length)
    channels = np.zeros((length,kingst.shape[1]),dtype="i4")
    index = kingst.index.to_numpy() * fs
    kingst = kingst.to_numpy()
    j = 0
    for i in trange(channels.shape[0]):
        while i >= index[j+1]:
            j += 1
        channels[i,:] = kingst[j,:]
    return channels

def sample_kingst_clk(kingst_csv, clk_channel):
    kingst = pd.read_csv(kingst_csv, encoding='gb2312', index_col=0)
    idx = np.where(np.diff(kingst[clk_channel].to_numpy())==1)[0]+1
    channels = kingst.iloc[idx,:].to_numpy()
    return channels

def plot_channels(channels):
    nch = channels.shape[1]
    fig,ax = plt.subplots(nch,1,sharex=True,sharey=True)
    for i in range(nch):
        ax[i].plot(channels[:,i])
        ax[i].set_ylim([-0.2,1.2])

def build_sdm(channels, endian="<", sdm_bits=4, th_bits=18):
    endian = '<'
    if endian == '<':
        mul = 2**np.arange(sdm_bits)
    else:
        mul = 2**np.arange(sdm_bits-1,-1,-1)

    sdm = (channels[:,1:] * mul).sum(axis=1)
    sdm = u2i(sdm,sdm_bits)

    TH = 2**th_bits;
    x1 = wrap(np.cumsum(sdm),TH);
    x2 = wrap(np.cumsum(x1),TH);
    x3 = wrap(np.cumsum(x2),TH);
    ds = x3[11::16];
    x4 = wrap(np.concatenate([[ds[0]],np.diff(ds)]),TH);
    x5 = wrap(np.concatenate([[x4[0]],np.diff(x4)]),TH);
    pcm = wrap(np.concatenate([[x5[0]],np.diff(x5)]),TH);

    return pcm

