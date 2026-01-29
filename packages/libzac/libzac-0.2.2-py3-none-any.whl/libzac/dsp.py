import numpy as np
import scipy
from packaging import version

def rolling_window(array:np.ndarray, window:int, step:int=1):
    """
    return rolling window matrix of input 1d `array` with `step`,
    drop tails that not enough for one window. 
        
    NOTE: THIS FUNCTION RETURN A READ-ONLY "VIEW" OF `array`, THEY SHARE THE SAME MEMORY!
    
    Examples
    --------
    >>> x = np.arange(20)
    >>> rolling_window(x,9,3)
    array([[ 0,  1,  2,  3,  4,  5,  6,  7,  8],
           [ 3,  4,  5,  6,  7,  8,  9, 10, 11],
           [ 6,  7,  8,  9, 10, 11, 12, 13, 14],
           [ 9, 10, 11, 12, 13, 14, 15, 16, 17]])
    >>> # 18/19 is dropped
    
    >>> rolling_window(x,9,-3) 
    array([[11, 12, 13, 14, 15, 16, 17, 18, 19],
           [ 8,  9, 10, 11, 12, 13, 14, 15, 16],
           [ 5,  6,  7,  8,  9, 10, 11, 12, 13],
           [ 2,  3,  4,  5,  6,  7,  8,  9, 10]])
    >>> # 0/1 is dropped

    >>> rolling_window(x,9,-3).flags
      C_CONTIGUOUS : False
      F_CONTIGUOUS : False
      OWNDATA : False
      WRITEABLE : False
      ALIGNED : True
      WRITEBACKIFCOPY : False
    <BLANKLINE>
    """
    if version.parse(np.version.version) < version.parse('1.20.0'):
        # before numpy 1.20.0
        shape = array.shape[:-1] + (array.shape[-1] - window + 1, window)
        strides = array.strides + (array.strides[-1],)
        return np.lib.stride_tricks.as_strided(array, shape=shape, strides=strides)[::step]
    else:
        # sliding_window_view() added after numpy 1.20.0
        return np.lib.stride_tricks.sliding_window_view(array, window)[::step]

def sig2frames(array:np.ndarray, window:int, step:int=0, **pad_kwarg):
    """
    same as `rolling_window()`, but padding zeros to tails to fill up a window.
    Thus return a copy of `array` instead of a view. `**pad_kwarg` is passed to `np.pad()`.
    
    Examples
    --------
    >>> x = np.arange(20)
    >>> sig2frames(x, 9, 3)
    array([[ 0,  1,  2,  3,  4,  5,  6,  7,  8],
           [ 3,  4,  5,  6,  7,  8,  9, 10, 11],
           [ 6,  7,  8,  9, 10, 11, 12, 13, 14],
           [ 9, 10, 11, 12, 13, 14, 15, 16, 17],
           [12, 13, 14, 15, 16, 17, 18, 19,  0]])
    >>> # note the last frame is padded with 0

    >>> sig2frames(x, 9, -3) 
    array([[11, 12, 13, 14, 15, 16, 17, 18, 19],
           [ 8,  9, 10, 11, 12, 13, 14, 15, 16],
           [ 5,  6,  7,  8,  9, 10, 11, 12, 13],
           [ 2,  3,  4,  5,  6,  7,  8,  9, 10],
           [ 0,  0,  1,  2,  3,  4,  5,  6,  7]])
    >>> # when step is negative, pad to head
    """
    n_step = abs(step)
    n_window = (array.size - window)//n_step + 1
    if window+(n_window-1)*n_step < array.size:
        pad_size = window + n_window*n_step - array.size
        array = np.pad(array, (0, pad_size) if step>0 else (pad_size,0), **pad_kwarg)
    return rolling_window(array, window, step)


def enbw(windowCol,fs):
    bw_t = np.mean(windowCol**2)/((np.mean(windowCol))**2)
    bw = bw_t * fs / len(windowCol)
    return bw

def bandpower(Sfund,Ffund):
    width = np.concatenate([[(Ffund[-1]-Ffund[0])/(len(Ffund)-1)], np.diff(Ffund)])
    power = np.dot(Sfund, width)
    return power

def idx2psddb(Pxx, F, idx):
    psd = 10*np.log10(Pxx[idx]+1e-40)
    freq = F[idx]
    return psd, freq

def getToneFromPSD(Pxx, F, rbw=None, toneFreq=None):
    """
    Retrieve the power and frequency of a windowed sinusoid
    This function is for internal use only and may be removed in a future
    release of MATLAB
    """

    idxTone = idxLeft = idxRight = None

    # force column vector
    colPxx = np.reshape(Pxx, -1)
    colF = np.reshape(F, -1)

    if toneFreq is None:
        idxTone = np.argmax(colPxx)
    elif colF[0] <= toneFreq and toneFreq <= colF[-1]:
        # find closest bin to specified freq
        idxTone = np.argmin(np.abs(colF-toneFreq))
        # look for local peak in vicinity of tone
        iLeftBin = max(0, idxTone-1)
        iRightBin = min(idxTone+1, len(colPxx)-1)
        idxMax = np.argmax(colPxx[iLeftBin:iRightBin+1])
        idxTone = iLeftBin + idxMax
    else:
        power = np.nan
        freq = np.nan
        idxTone = idxLeft = idxRight = None
        return power, freq, idxTone, idxLeft, idxRight

    idxToneScalar = idxTone

    # sidelobes treated as noise
    idxLeft = idxToneScalar - 1
    idxRight = idxToneScalar + 1

    # roll down slope to left
    while idxLeft > -1 and colPxx[idxLeft] <= colPxx[idxLeft+1]:
        idxLeft -= 1

    # roll down slope to right
    while idxRight <= len(colPxx)-1 and colPxx[idxRight-1] >= colPxx[idxRight]:
        idxRight += 1

    # provide indices to the tone border (inclusive)
    idxLeft = idxLeft+1
    idxRight = idxRight

    idxLeftScalar = idxLeft
    idxRightScalar = idxRight

    # compute the central moment in the neighborhood of the peak
    Ffund = colF[idxLeftScalar:idxRightScalar]
    Sfund = colPxx[idxLeftScalar:idxRightScalar]
    if np.sum(Sfund) == 0:
        freq = 0
    else:
        freq = np.dot(Ffund, Sfund) / np.sum(Sfund)

    # report back the integrated power in this band
    if idxLeftScalar<idxRightScalar:
        # more than one bin
        power = bandpower(Sfund, Ffund)
    elif 1 < idxRightScalar and idxRightScalar < len(colPxx):
        # otherwise just use the current bin
        power = colPxx[idxRightScalar] * (colF[idxRightScalar+1] - colF[idxRightScalar-1])/2
    else:
        # otherwise just use the average bin width
        power = colPxx[idxRightScalar] * np.mean(np.diff(colF))

    # protect against nearby tone invading the window kernel
    if rbw is not None and power < rbw*colPxx[idxToneScalar]:
        power = rbw*colPxx[idxToneScalar]
        freq = colF[idxToneScalar]

    return power, freq, idxTone, idxLeft, idxRight

def snr(x,fs=1,nHarmScalar=6):
    colX = x.reshape(-1)
    colX = colX - np.mean(colX)
    n = len(colX)
    w = scipy.signal.windows.kaiser(n, 38)
    rbw = enbw(w,fs)
    F,Pxx = scipy.signal.periodogram(colX,fs,w,n)

    origPxx = Pxx.copy()

    Pxx[0] = 2*Pxx[0]
    _, _, _, iLeft, iRight = getToneFromPSD(Pxx, F, rbw, 0)
    if iLeft is not None and iRight is not None:
        Pxx[iLeft:iRight] = 0

    # psdHarmPow = np.zeros(nHarmScalar)
    # psdHarmFreq = np.zeros(nHarmScalar)

    Pfund, Ffund, iFund, iLeft, iRight = getToneFromPSD(Pxx, F, rbw)
    # psdHarmPow[0], psdHarmFreq[0] = idx2psddb(Pxx, F, iFund)
    if iLeft is not None and iRight is not None:
        Pxx[iLeft:iRight] = 0

    for i in range(2,nHarmScalar+1):
        toneFreq = i*Ffund
        harmPow, _, iHarm, iLeft, iRight = getToneFromPSD(Pxx, F, rbw, toneFreq)
        # psdHarmPow[i-1], psdHarmFreq[i-1] = idx2psddb(Pxx, F, iHarm)
        if not np.isnan(harmPow) and iLeft is not None and iRight is not None:
            Pxx[iLeft:iRight] = 0

    estimatedNoiseDensity = np.median(Pxx[Pxx>0])
    Pxx[Pxx==0] = estimatedNoiseDensity
    Pxx = np.min([Pxx,origPxx],0)
    totalNoise = bandpower(Pxx, F)
    r = 10*np.log10(Pfund / totalNoise)
    noisePow = 10*np.log10(totalNoise)
    return r


if __name__ == '__main__':
    import doctest
    doctest.testmod()