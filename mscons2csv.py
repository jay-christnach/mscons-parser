"""
Created on Thu Sep 29 15:29:01 2016

@author: ChristnachJeanClaude
"""

import argparse
from msconsparser import MSCONSparser
import datetime


def mscons2csv(filename):
    mscons = MSCONSparser(filename)
    lpHeader = ('begin', 'end', 'code', 'value', 'unit')
    lpQuantity = len(mscons.lpList)
    lpHeaders = lpHeader * lpQuantity
    lpNameHeader = []
    for lpName, lpObis in mscons.lpList:
        lpNameHeader.append(lpName)
        lpNameHeader.append(lpObis)
        lpNameHeader.append('')
        lpNameHeader.append('')
        lpNameHeader.append('')
    rowQuantity = max([len(item) for item in mscons.loadProfiles])
    lpRows = []
    for i in range(rowQuantity):
        row = []
        for j in range(lpQuantity):
            if len(mscons.loadProfiles[j]) > i:  # Lastprofile sind manchmal nicht gleich lang
                row.extend(mscons.loadProfiles[j][i])
            else:
                row.extend([None, None, None, None, None])
        lpRows.append(row)

    CR = '\n'
    with open(filename + '.csv', 'w') as file:
        file.write(';'.join(lpNameHeader) + CR)
        file.write(';'.join(lpHeaders) + CR)
        for row in lpRows:
            formatedRow = []
            for field in row:
                if isinstance(field, datetime.datetime):
                    formatedRow.append(field.strftime('%d.%m.%Y %H:%M'))
                if field is None:
                    formatedRow.append('')
                if field is not None and not isinstance(field, datetime.datetime):
                    formatedRow.append(str(field))
            file.write(';'.join(formatedRow) + CR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    filename = args.filename
    mscons2csv(filename)
