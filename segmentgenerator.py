# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 11:41:37 2016

@author: ChristnachJeanClaude
"""

import sys

class SegmentGenerator:
    def __init__(self, filename):
        try:
            fh = open(filename)
        except IOError:
            print ("Error: file " + filename + " not found!")
            sys.exit(2)
        lines=[]
        for line in fh:
            line = line.rstrip()
            lines.append(line)
        if len(lines) == 1:
            msg = lines[0]
        else:
            msg = ''
            for line in lines:
                msg = msg + line.rstrip()
        self.segments=msg.split("'")
        self.iter=iter(self.segments)
    
    def next(self):
        try:
            return next(self.iter)
        except StopIteration:
            return None
    

if __name__ == '__main__':
    sg = SegmentGenerator('MSCONS_10XLU-CEGEDEL-N3_20X-SUD-STROUM-M_01_20110318_114059_241.txt')
    for i in range(16500):
        print(sg.next())
        
    