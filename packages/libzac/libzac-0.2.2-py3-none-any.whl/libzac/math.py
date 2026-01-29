import numpy as np

def i4_to_i3u1(i4):
    """Unpack [u]int32 numpy array, turn lower 3 bytes into a uint8 array (endianness matters).

    NOTE: By default it works on 24 bit data stored in 32 bit integers, simply drop the highest byte and no sign extend.
    
    Examples
    --------
    >>> i4 = np.array([0x01020304, 0x05060708], dtype=">u4") # big-endian
    >>> i4_to_i3u1(i4)
    array([2, 3, 4, 6, 7, 8], dtype=uint8)
    >>> i4 = np.array([0x01020304, 0x05060708], dtype="<u4") # little-endian
    >>> i4_to_i3u1(i4)
    array([4, 3, 2, 8, 7, 6], dtype=uint8)
    >>> i4 = np.array([0xf1020304, 0xf5060708], dtype="<u4") # negative value < -2**23 may give wrong result
    >>> i4_to_i3u1(i4)
    array([4, 3, 2, 8, 7, 6], dtype=uint8)
    >>> i4 = np.random.randint(0, 2**24, 100, dtype="<u4")
    >>> i3u1 = i4_to_i3u1(i4)
    >>> np.allclose(i4,i3u1_to_i4(i3u1, "<", sign=False))
    True
    """
    offset = 1 if i4.dtype.byteorder == ">" else 0    
    return i4.view("u1").reshape(-1,4)[:, 0+offset:3+offset].ravel()

def i3u1_to_i4(i3u1, endian="<", sign=True):
    """pack every 3 items of a uint8 array as lower 3 bytes of int32 array (endianness matters)
    
    Examples
    --------
    >>> i3u1 = np.array([2, 3, 4, 6, 7, 8], dtype="u1")
    >>> i3u1_to_i4(i3u1,">",False) == np.array([0x020304, 0x060708], dtype=">u4")
    array([ True,  True])
    >>> i3u1 = np.array([4, 3, 2, 8, 7, 6], dtype="u1")
    >>> i3u1_to_i4(i3u1,"<",False) == np.array([0x020304, 0x060708], dtype="<u4")
    array([ True,  True])
    >>> i3u1 = np.array([4, 3, 255, 8, 7, 255], dtype="u1")
    >>> i3u1_to_i4(i3u1,"<",True) == np.array([0xffff0304, 0xffff0708], dtype="<u4").astype('i4')
    array([ True,  True])
    >>> i3u1 = np.random.randint(0, 2**8, 100*3, dtype="u1")
    >>> i4 = i3u1_to_i4(i3u1, "<", sign=False)
    >>> np.allclose(i3u1, i4_to_i3u1(i4))
    True
    """
    i4 = np.zeros(i3u1.size//3, dtype="i4")
    i4.view("u1").reshape(-1,4)[:,:3] = i3u1.reshape(-1,3)[:,::(-1 if endian == ">" else 1)]
    return u2i(i4, 24) if sign else i4

def u2i(x, width, overflow_warning=True):
    """
    Convert unsigned integer to signed integer (2's complement) with any bit width.

    Examples
    --------
    >>> u2i(np.array([0x7f, 0x80, 0xff], dtype="u1"), 8)
    array([ 127, -128,   -1], dtype=int8)
    >>> u2i(np.arange(8,dtype="u1"), 3)
    array([ 0,  1,  2,  3, -4, -3, -2, -1], dtype=int8)
    >>> u = np.random.randint(0, 2**24, 100, dtype="u4")
    >>> i = u2i(u, 24)
    >>> np.allclose(u,i2u(i, 24))
    True
    """
    y = x.astype(np.int64)
    overflow = (x >> width).astype(bool)
    if overflow_warning and overflow.any():
        print("Overflow")
    y[x >= (1<<(width-1))] -= (1<<width)
    y[overflow] = -1
    return y.astype(f"i{y.dtype.itemsize}")

def i2u(x, width, overflow_warning=True):
    """
    Convert signed integer (2's complement) to unsigned integer with any bit width.
    
    Examples
    --------
    >>> i2u(np.array([127, -128, -1], dtype="i1"), 8)
    array([127, 128, 255], dtype=uint8)
    >>> i2u(np.arange(-4,4,dtype="i1"), 3)
    array([4, 5, 6, 7, 0, 1, 2, 3], dtype=uint8)
    >>> u = np.random.randint(0, 2**24, 100, dtype="u4")
    >>> i = u2i(u, 24)
    >>> np.allclose(u,i2u(i, 24))
    True
    """
    y = np.copy(x)
    upper = y >  (1<<(width-1))-1
    lower = y < -(1<<(width-1))
    if overflow_warning and (upper.any() or lower.any()):
        print("Overflow")
    y[upper] =   (1<<(width-1))-1
    y[lower] =  -(1<<(width-1))
    y[y < 0] +=  (1<<(width))
    return y.astype(f"u{y.dtype.itemsize}")
    
def byte2int(byte, dtype="<i4"):
    """Mainly for converting byte string to 24 bit("i3") numpy array, 
    for common dtypes(8/16/32/64) just call np.frombuffer."""
    if isinstance(dtype, str) and dtype[-1]=='3':
        u3u1 = np.frombuffer(byte,"u1").copy()
        endianness = ">" if dtype[0]==">" else "<"
        return i3u1_to_i4(u3u1, endianness, dtype[-2]=='i')
    else:
        return np.frombuffer(byte,dtype=dtype).copy()
    
def wrap(x, th, inplace=False):
    """Wrap x to the range [-th, th)."""
    if not inplace:
        x = x.copy()
    q = (x <= -th) | (th <= x)
    if q.any():
        x[q] = np.mod(x[q]+th, 2*th) - th;
    return x