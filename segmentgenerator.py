# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 11:41:37 2016

@author: ChristnachJeanClaude
"""

import sys


# import logging
# from autologging import traced, TRACE

# @traced
class SegmentGenerator:
    def __init__(self, filename):
        try:
            fh = open(filename)
        except IOError:
            print("Error: file " + filename + " not found!")
            sys.exit(2)
        lines = []
        for line in fh:
            line = line.rstrip()
            lines.append(line)
        if len(lines) == 1:
            msg = lines[0]
        else:
            msg = ''
            for line in lines:
                msg = msg + line.rstrip()
        self.segments = msg.split("'")
        self.iterator = iter(self.segments)
        self.counter = 0

    def next(self):
        try:
            self.counter += 1
            return next(self.iterator)
        except StopIteration:
            return None


if __name__ == '__main__':
    sg = SegmentGenerator('MSCONS_21X000000001333E_20X-SUD-STROUM-M_20180807_000026404801.txt')

    print("Num segments:", len(sg.segments))
    i = 0
    value = 'x'
    while value:
        value = sg.next()
        i += 1
        print(i, value)

    print("Num iterations:", i)
    print("Num segments:", len(sg.segments))
