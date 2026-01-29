from __future__ import annotations
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from .math import byte2int
from subprocess import STDOUT, check_output, CalledProcessError

from typing import TYPE_CHECKING
if TYPE_CHECKING:  # Only imports the below statements during type checking, avoid circular import
    from .bitfield import bitfield

def einput(num, output_int=False):
    """
    convert all kind of input to hex string(default) or integer

    Examples
    --------
    einput(0x1234)
    >>> '1234'
    einput('0x1234')
    >>> '1234'
    einput(1234)
    >>> '4d2'
    einput('1234')
    >>> '1234'
    einput(1234.4)
    >>> '4d2'
    einput(1234.6)
    >>> '4d3'
    einput(0x1234, output_int=True)
    >>> 4660
    """
    if isinstance(num, str):        
        num = int(num,16)
    elif isinstance(num, (int, np.integer)):
        pass
    elif isinstance(num, (float, np.float_)):
        num = int(np.around(num))        
    else:
        raise TypeError(f"Input type [{type(num)}] of [{num}] not supported")
    return num if output_int else f"{num:x}"

def eread(addr, length=1, dtype="u1", ch=0, baud="f0", timeout=3, cwd=None):
    """
    run 'e {addr}l{length}' in cmd, capture the output and convert to numpy array with dtype format

    ch: channel number, default 0
    baud: baud rate, default f0
    timeout: timeout in seconds, default 3
    cwd: current working directory, default the root of calling script.
    """
    addr = einput(addr)
    length = einput(length)
    try:
        raw = check_output(f"e {addr}l{length}", stderr=STDOUT, timeout=timeout, env={"ch":f"{ch}","baud":baud}, cwd=cwd).decode("utf8")
    except CalledProcessError as e:
        print("e.exe error: " + e.output.decode("utf8"))
        raise e
    return e2int(raw, dtype=dtype)[0]

def ewrite(addr, value, ch=0, baud="f0", timeout=3, cwd=None, length=None):
    """
    run 'e {addr} {value}' in cmd

    ch: channel number, default 0
    timeout: timeout in seconds, default 3
    cwd: current working directory, default the root of calling script.
    """
    addr = einput(addr)
    value = einput(value)
    # add heading 0 if length is specified
    value = '0'*(length*2-len(value)) + value if length else value
    try:
        check_output(f"e {addr} {value}", stderr=STDOUT, timeout=timeout, env={"ch":f"{ch}","baud":baud}, cwd=cwd)
    except CalledProcessError as e:
        print("e.exe error: " + e.output.decode("utf8"))
        raise e

def ewrite_block(addr, data):
    """
    write a block of data {data} to start address {addr} with e.exe
    data will be converted to bytes and split into 8-byte blocks
    """
    u1_data = np.frombuffer(data.tobytes(), dtype="u1")
    addr = einput(addr, output_int=True)
    data_length = len(u1_data)
    
    for i in range(0,data_length,8):
        block = u1_data[i:min(i+8,data_length)]
        data = "".join([f"{b:02x}" if isinstance(b,(int,np.integer)) else b for b in block][::-1])
        start_address = f"{addr + i:x}"
        ewrite(start_address, data, length=8)

def e2byte(input, skip_row=1):
    """
    convert the output of e.exe to bytes array and its corresponding address array

    input: can be either string of e.exe output, or a txt file that contains the output of e.exe. (e 4000l20 > a.txt)
    skip_row: skip the first {skip_row} rows of the input, often used to remove the header of e.exe output (0 1 ... e f)
    """
    if os.path.isfile(input):
        with open(input,"r") as f:
            raw = f.read()
    else:
        raw = input
    raw = raw.split("\n")[skip_row:]
    data = []
    addr = []
    start_addr = int(re.search(r"[0-9a-f]+(?= : )", raw[0]).group(), 16)
    start_addr += (re.search(r" [0-9a-f]{2} ", raw[0]).span()[0] - 8)//3
    for r in raw:
        row = re.split(r"(\W*[0-9a-f]+ : )", r)
        if len(row) > 2:
            for d in row[2].split(" "):
                if (len(d)==2):
                    data.append(int(d, 16))
                    addr.append(start_addr)
                    start_addr += 1
    byte = np.asarray(data, dtype=np.uint8).tobytes()
    addr = np.asarray(addr)
    return byte, addr

def e2int(input, dtype="<i4", skip_row=1):
    """use e2byte(), and further convert the bytes array to integer array with dtype format"""
    byte, addr = e2byte(input, skip_row=skip_row)
    itemsize = 1
    if isinstance(dtype, str):
        itemsize = int(dtype[-1])
    else:
        itemsize = np.dtype(dtype).itemsize
    return byte2int(byte, dtype), addr[::itemsize]

def e2plt(data, addr, x_hex=True, y_int=True):
    """plot (data,addr) from e2int with matplotlib"""    
    fig, ax = plt.subplots()
    ax.plot(addr,data)
    if x_hex:
        ax.get_xaxis().set_major_formatter(lambda x, pos: hex(int(x)))
    if y_int:
        ax.get_yaxis().set_major_formatter(lambda x, pos: int(x))
    fig.show()
    return fig,ax

def e2write(input, skip_row=1):
    """use e2int(), and further write data back to its address with ewrite_block()"""
    u1_data, addr = e2int(input, "u1", skip_row=skip_row)
    ewrite_block(addr[0], u1_data)

###############################################
#  wrapper of HREAD/HWRITE macro in yc11xx.h  #
###############################################

HREAD = HREAD2 = HREAD3 = HREAD_INLINE =        lambda reg: eread(reg)[0]
HREADW =                                        lambda reg: eread(reg, length=2, dtype="u2")[0]
HREAD24BIT = HREADADDR3 =                       lambda reg: eread(reg, length=3, dtype="u3")[0]
HREAD4 = HREADL = HREADRV =                     lambda reg: eread(reg, length=4, dtype="u4")[0]

HWRITE = HWRITE2 = HWRITE3 = HWRITE_INLINE =    lambda reg, value: ewrite(reg, value & 0xff,        length=1)
HWRITEW = HWRITEW_INLINE =                      lambda reg, value: ewrite(reg, value & 0xffff,      length=2)
HWRITE24BIT =                                   lambda reg, value: ewrite(reg, value & 0xffffff,    length=3)
HWRITEL = HWRITERV = HWRITE4 =                  lambda reg, value: ewrite(reg, value & 0xffffffff,  length=4)

def HREAD_STRUCT(reg, stc:bitfield):
    if einput(reg) == einput(stc.addr):
        stc.read()
    else:
        raise ValueError(f"reg '{reg}' is different from bitfield '{stc.__class__.__name__} @ {stc.addr}'")

def HWRITE_STRUCT(reg, stc:bitfield):
    if einput(reg) == einput(stc.addr):
        stc.write()
    else:
        raise ValueError(f"reg '{reg}' is different from bitfield '{stc.__class__.__name__} @ {stc.addr}'")
    
HREADW_STRUCT  = HREAD24BIT_STRUCT  = HREADL_STRUCT  = HREAD_STRUCT
HWRITEW_STRUCT = HWRITE24BIT_STRUCT = HWRITEL_STRUCT = HWRITE_STRUCT