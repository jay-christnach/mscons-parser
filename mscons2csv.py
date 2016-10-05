# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 15:29:01 2016

@author: ChristnachJeanClaude
"""

import argparse
from msconsparser import MSCONSparser
import datetime


parser = argparse.ArgumentParser()
parser.add_argument("filename")
args = parser.parse_args()
filename=args.filename
mscons = MSCONSparser(filename)
lpHeader=('begin', 'end', 'value')
lpQuantity=len(mscons.lpList)
lpHeaders=lpHeader*lpQuantity
lpNameHeader=[]
for lpName, lpObis in mscons.lpList:
    lpNameHeader.append(lpName)
    lpNameHeader.append(lpObis)
    lpNameHeader.append('')
rowQuantity=max([len(item) for item in mscons.loadProfiles])
lpRows=[]
for i in range(rowQuantity):
    row=[]
    for j in range(lpQuantity):
        row.extend(mscons.loadProfiles[j][i])
    lpRows.append(row)

CR='\n'
with open(filename + '.csv','w') as file:
    file.write(';'.join(lpNameHeader)+CR)
    file.write(';'.join(lpHeaders)+CR)
    for row in lpRows:
        formatedRow=[]
        for field in row:
            if isinstance(field,datetime.datetime):
                formatedRow.append(field.strftime('%d.%m.%Y %H:%M'))
            else:
                formatedRow.append(field)
        file.write(';'.join(formatedRow)+CR)
    