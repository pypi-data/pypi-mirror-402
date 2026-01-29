import os
import re
import numpy as np
import soundfile as sf
np.set_printoptions(threshold=999999)

def c2np(filename):
    """
    parse c array from file to numpy array
    
    WARNING: this function use `eval()` so not secure, do not use it on untrusted file
    """
    with open(filename,'r') as f:
        raw = f.read()
    dtype_dict = {
        'float':            np.float32,
        'double':           np.float64,

        'unsigned char':    np.uint8,
        'uint8_t':          np.uint8,
        'char':             np.int8,
        'int8_t':           np.int8,

        'unsigned short':   np.uint16,
        'uint16_t':         np.uint16,
        'short':            np.int16,
        'int16_t':          np.int16,
        
        'unsigned int':     np.uint32,
        'uint32_t':         np.uint32,
        'int':              np.int32,
        'int32_t':          np.int32,
    }
    regex = "((?:"+")|(?:".join(list(dtype_dict.keys()))+"))" + r"\s*(\w*)(\[.*\])\s*=\s*(\{[\s\S]*?\});"
    match = re.findall(regex, raw)
    array_dict = {}
    for group in match:
        dtype = dtype_dict[group[0]]
        array_name = group[1]
        data_str = group[3].replace("{","[").replace("}",']')   # change c array {} to python list []
        clean_str = re.sub(r"\/\/[\S\s]*?\\n", '', data_str)    # remove comment //
        clean_str = re.sub(r"\/\*[\S\s]*?\*\/",'', clean_str)   # remove comment /* */
        try:
            data = eval(clean_str) # this is not secure but i dont care
        except Exception as error:
            print(f"parse {array_name} error: ",error)
        array = np.array(data).astype(dtype)
        array_dict[array_name] = array
    return array_dict

def np2c(np_dict_array, filename, addition="", const=True, formatter={"float_kind":lambda f:f"{f:f}f"}, **kwargs):
    """
    write numpy array to `<filename>.h` as c array format

    np_dict_array: {"name":np.ndarray}
    filename: output filename, without extension
    addition: additional text to be added to the header file, usually used to add preprossor macro like `#include <stdint.h>`
    """
    filename = os.path.splitext(filename)[0]
    filename_no_ext = os.path.split(filename)[1]
    with open(filename+".h", "w") as f:
        const = "const " if const else "" 
        f.write(f"#ifndef __{filename_no_ext}__\n#define __{filename_no_ext}__\n#include <stdint.h>\n\n")        
        f.write(addition)        
        for array_name,array in np_dict_array.items():
            dtype = array.dtype
            if np.issubdtype(dtype, np.floating):
                dtype_name = "float" if dtype.itemsize == 4 else "double"
            elif np.issubdtype(dtype, np.integer):
                dtype_name = f"{np.dtype(dtype).base.name}_t"
            else:
                raise TypeError(f"unsupported dtype {dtype} for {array_name}")
            f.write(f"{const}{dtype_name} {array_name}[{array.size}] = {{\n ")
            array_str = np.array2string(array, separator=",", formatter = formatter, **kwargs)[1:-1] # remove []
            f.write(array_str)
            f.write("\n};\n\n")
        f.write(f"\n#endif /* __{filename_no_ext}__ */")           

def file2c(filename_in, filename_out, array_name, dtype=np.uint8, pad_tail=False, **kwargs):
    """read file to byte array then to numpy array with dtype, kwargs pass to np2c"""
    with open(filename_in, "rb") as f:
        raw_byte = f.read()
    byte2c(raw_byte, filename_out, array_name, dtype, pad_tail, **kwargs)

def byte2c(byte, filename, array_name="byte_buf", dtype=np.uint8, pad_tail=False, **kwargs):
    """convert byte array to numpy array with dtype then write to `<filename>.h` as c array format, kwargs pass to np2c"""
    dtype = np.dtype(dtype)
    size = dtype.itemsize
    if len(byte)%size != 0:
        print(f"WARNING: byte size {len(byte)} is not multiple of {size}, ", end="")
        if pad_tail:
            print(f"pad last {size-len(byte)%size} byte")
            byte = byte + b'\x00'*(size-len(byte)%size)
        else:
            print(f"remove last {len(byte)%size} byte")
            byte = byte[:len(byte)//size*size]
    array = np.frombuffer(byte, dtype=dtype)
    np2c({array_name:array}, filename, **kwargs)

def parse_lst(filename:str, names:list, pattern=lambda name: r"([\da-f]{8}) g     O .data	([\da-f]{8}) "+name) -> dict:
    """find global variable in lst file and return a dict of {name:(address, size)}"""
    with open(filename, 'r') as file:
        content = file.read()
    result = {}
    for name in names:
        match = re.search(pattern(name), content)
        if match:
            result[name] = match.groups()
    return result

def get_all_attr(obj:object, condition:callable=lambda x:True) -> list:
    """return all attribute of an object that satisfy the condition"""
    return {name:getattr(obj, name) for name in dir(obj) if condition(getattr(obj, name))}

def format_c_debug(log):
    if os.path.isfile(log):
        with open(log,"r") as f:
            log = f.read()

    findall = [i for i in re.finditer(r"\n\[\d+\]\n",log)]
    rtn = []
    for i in range(len(findall)):
        start = findall[i].start()
        end = findall[i].end()
        next_start = len(log) if i == len(findall)-1 else findall[i+1].start()

        name = log[log[:start].rfind('\n')+1:start]
        raw_data = re.findall(r"(?<=\]: )\S+",log[end:next_start])
        data = np.asarray(raw_data,dtype=np.float64)
        rtn.append((name,data))
    return rtn

def read_dat(filename, dtype="u1"):
    with open(filename,"r") as f:
        raw = f.read()
    x = np.array([int(i,16) for i in raw.split('\n') if i],dtype="u1")
    return x.view(dtype)

def write_dat(filename, x):
    with open(filename, "w", encoding="utf8") as f:
        for i in x.view("u1"):
            f.write(f"{i:02x}\n")

def pcm2wav(filename, fs=8000):
    x = np.fromfile(filename, dtype=np.int16)
    sf.write(filename+".wav", x, fs, "PCM_16")
    return x