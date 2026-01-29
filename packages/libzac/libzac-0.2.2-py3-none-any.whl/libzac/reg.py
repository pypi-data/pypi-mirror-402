import re
import sys
import numpy as np
import pandas as pd
import xlrd
import openpyxl
from .e import e2int
from typing import Union

if xlrd.__version__ < "2.0.0":
    xlrd.xlsx.ensure_elementtree_imported(False, None)
    xlrd.xlsx.Element_has_iter = True

autoREG = """
e 8000lc29  > bb.txt
e 8900laa   > modem.txt
e 8a00la4   > rf.txt
e 8b00l1c   > codec.txt
"""
addr_name = "addr"
reg_name = "name"
width_name = "width"
domain_name = "domain"
access_name = "access"
init_name = "init"
description_name = "description"
module_name = "module"

__workbook_type = Union[xlrd.book.Book, openpyxl.workbook.workbook.Workbook]

def read_excel(wb:__workbook_type, sheet_name:str) -> pd.DataFrame:
    """read excel from workbook(xlrd/openpyxl), and fill merged cells"""
    if isinstance(wb, xlrd.book.Book):
        table = pd.read_excel(wb,sheet_name=sheet_name,dtype="string")
        for rl, rh, cl, ch in wb.sheet_by_name(sheet_name).merged_cells:
            table.iloc[rl-1:rh-1, cl:ch] = table.iloc[rl-1,cl]
    elif isinstance(wb, openpyxl.workbook.workbook.Workbook):
        table = pd.DataFrame(wb[sheet_name].values,dtype="string")
        col = table.iloc[0].copy()
        col[col.isna()] = "NAN" # otherwise table will use `pandas._libs.missing.NAType` as column name, which is undesirable
        table.columns = col
        table = table[1:]
        for r in wb[sheet_name].merged_cells.ranges:
            rl, rh, cl, ch = r.bounds
            table.iloc[rh-2:ch-1,rl-1:cl] = table.iloc[rh-2,rl-1]
    return table

def keep_rename_columns(table:pd.DataFrame) -> None:
    """only keep columns in `names`, and rename them to dict keys"""
    names = {
        "write addr":["Write Address"],
        "read addr":["Read Address"],
        addr_name:[addr_name,"地址","addr","Address"],
        reg_name:[reg_name,"寄存器","reg_name","Type"],
        width_name:[width_name,"位置","width","Bit","Bit location",'bit'],
        domain_name:[domain_name,"域名","field_name","Register Name","name"],
        access_name:[access_name,"RW","access","读写"],
        init_name:[init_name,"original","initVal\n（HEX）","初始值","Default Value","initVal"],
        description_name:[description_name,"Description","描述","Note"],
        module_name:[module_name,"模块","STATUS","Module Name"],
    }
    for col in table.columns:
        for k,v in names.items():
            if col in v:
                table.rename(columns={col:k}, inplace=True)
                break
        else:
            table.drop(col, axis=1, inplace=True, errors="ignore")     

def format_table(table:pd.DataFrame) -> None: # NOTE: not support LPM
    """format table for later use"""
    # item is invalid if either addr or width is nan
    invalid = table[addr_name].isna() | table[width_name].isna()
    invalid |= ~(table[addr_name].str.match(r'^[\da-fA-F]+$'))
    table.drop(labels=table.index[invalid], inplace=True)
    # format addr to int
    table[addr_name] = table[addr_name].str.replace(r"\.\d*","",regex=True)
    # if domain is nan, use reg+reseverd as domain name
    domain_na = table[domain_name].isna()
    table.loc[domain_na,(domain_name)] = table.loc[domain_na,(reg_name)] + "_reserved"
    # replace " " and "[]" with "_" in names
    table[reg_name] = table[reg_name].str.replace(r"[ \[\]:]","_",regex=True)
    table[domain_name] = table[domain_name].str.replace(r"[ \[\]:]","_",regex=True)
    # remove [] from width
    table[width_name] = table[width_name].str.replace(r"[\[\]]","",regex=True)
    # "W"->"WO", "R"->"RO", else->"RW" # disable when use diff compare generated file with original reg_struct.h
    table.loc[table[access_name]=="W",(access_name)] = "WO"
    table.loc[table[access_name]=="R",(access_name)] = "RO"
    table.loc[table[access_name].isna(),(access_name)] = "RW"
    table.loc[~((table[access_name]=="WO") | (table[access_name]=="RO")),(access_name)] = "RW"
    # if description is nan, use "" as default
    table.loc[table[description_name].isna(),(description_name)] = ""
    table[description_name] = table[description_name].str.replace("None","",regex=True)
    # reg is upper case, domain is lower case
    table[reg_name] = table[reg_name].str.upper()
    table[domain_name] = table[domain_name].str.lower()

def read_yc_reg(wb:__workbook_type, sheet_name:str) -> pd.DataFrame:
    """read table from workbook then format it"""
    table = read_excel(wb,sheet_name)
    keep_rename_columns(table)
    format_table(table)
    return table

def read_yc_reg_from_file(filename:str) -> dict[str:pd.DataFrame]:
    wb = openpyxl.load_workbook(filename)
    tables = {sheet_name:read_yc_reg(wb, sheet_name) for sheet_name in wb.sheetnames if sheet_name != 'lpm'}
    return tables

def keep_only_rows(table:pd.DataFrame, keep_list:list, col:str = addr_name) -> pd.DataFrame:
    return table.loc[table[col].isin(keep_list)]

def table2tree(table:pd.DataFrame, key:str) -> dict:
    """convert pandas Dataframe to tree like dict, use either `addr_name` or `reg_name` as `key`"""
    tree = {}
    old_key = ""
    for i in table.to_dict("records"):
        if tree.get(i[key],False):
            if i[key] != old_key:
                raise ValueError(f"multiple '{i[key]}' in {i}")
            tree[i[key]].append(i)
        else:
            tree[i[key]] = [i]
        old_key = i[key]
    return tree


"""manipulate data
mem_map = {0x8b00 : 0x20, ...}
reg_map = {CODEC_LDO_EN0RegDef : 0x20, ...}
addr_map = {0x8b00: CODEC_LDO_EN0RegDef, ...}
"""

def efile_to_mem_map(filename:str) -> dict:
    """convert an `e [addr]l[size]` output file to dict where key is addr and value is data"""
    return {addr:data for data,addr in zip(*e2int(filename,"u1"))}

def parse_width(width:Union[str,int]) -> tuple[int,int]:
    """parse_width('[x]/x') = (x,x);  parse_width('[x:y]/x:y') = (x,y)"""
    if isinstance(width, (np.integer, int)):
        return width, width
    if (not width) or (width == "nan") or not isinstance(width, str):
        raise ValueError(f"parse_width() failed: {type(width)}:{width}")
    width = width.replace("[","").replace("]","").replace(" ","").split(":")
    return (int(width[1]), int(width[0])) if len(width)==2 else (int(width[0]), int(width[0]))

def parse_reg(addr:int, mem_map:dict, start:int, stop:int) -> str:
    """Get bits between `start` and `stop` from start address `addr` in `mem_map`.
    if total bits > 64, return `too large`, if cannot find `addr` in `mem_map` return `nan`, otherwise return string of data in hex"""
    bits = stop-start+1
    if bits > 64:
        return "too large"    
    if mem_map.get(addr,-1) >= 0:
        num = 0
        for i in range(stop//8+1):
            num |= mem_map[addr+i]<<(i*8)
        num = (num >> start) & ((1<<bits)-1)
        return f"{num:0{((bits-1)//8+1)*2}x}"
    else:
        return "nan"
    
def parse_table(table:pd.DataFrame, mem_map:dict, new_column:str) -> None:        
    """add new column named `new_column` to `table`, apply `parse_reg` to each row"""
    table.loc[:,new_column] = np.zeros(len(table),str)
    for i in table.index:    
        try:
            start, stop = parse_width(table.loc[i,width_name])
            if start >= 0 and not pd.isna(table.loc[i,addr_name]):            
                addr = re.search(r"[\da-f]{4,}",table.loc[i,addr_name])
                if addr is not None:     
                    table.loc[i,new_column] = parse_reg(int(addr.group(),16), mem_map, start, stop)
        except Exception as e:
            print(f"Unable to parse table line {i}: \n{table.loc[i]}\n")
            raise e

def load_reg_1121M(MODULE_PATH = "E:\\Work\\Yichip\\1121M\\Soft_Doc\\xlsxtoStructTool\\reg_1121M"):    
    sys.path.append(MODULE_PATH)