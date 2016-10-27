# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 09:13:28 2016

@author: ChristnachJeanClaude
"""

class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.startState = None
        self.endStates = []

    def add_state(self, name, handler, end_state=0):
        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_start(self, name):
        self.startState = name.upper()

    def run(self, cargo):
        try:
            handler = self.handlers[self.startState]
        except:
            raise AssertionError("must call .set_start() before .run()")
        if not self.endStates:
            raise  AssertionError("at least one state must be an end_state")
    
        while True:
            (newState, cargo) = handler(cargo)
            if newState.upper() in self.endStates:
                handler = self.handlers[newState.upper()]
                if handler:
                    handler(cargo)
                print("reached ", newState)
                break 
            else:
                print(newState)
                handler = self.handlers[newState.upper()]  