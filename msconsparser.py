# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 14:12:58 2016

@author: ChristnachJeanClaude
"""

from statemachine import StateMachine
from segmentgenerator import SegmentGenerator
import datetime
import re

class MSCONSparser:
    interchange_header={}
    message_header={}
    lpList=[]
    loadProfiles=[]
    __chunkLocations=[]
    __locationStartTimes=[]
    __locationEndTimes=[]
    __chunkObis=[]
    __currentLpChunk=[]
    __LpChunks=[]

    
    def starttransition(self, segment):    
        match=re.search('UNB\+(.*?)\+(.*?):.*?\+(.*?):.*?\+(.*?):(.*?)\+(.*?)\+.*?\+(.*?)($|\+.*)',segment)
        #https://regex101.com/r/gU3vZ9/1
        if match:
            self.interchange_header['syntax_identifier']=match.group(1)
            self.interchange_header['sender']=match.group(2)
            self.interchange_header['recipient']=match.group(3)
            self.interchange_header['preparation_date']=match.group(4)
            self.interchange_header['preparation_time']=match.group(5)
            self.interchange_header['control_reference']=match.group(6)
            self.interchange_header['application_reference']=match.group(7)
            newstate='UNB'
            return(newstate,self.sg.next())
        else:
            return('Error',segment + "\nUNB segment didn't match")
        
    def UNBtransition(self, segment):
        match=re.search('UNH\+(.*?)\+(.*?):(.*?):(.*?):(.*?):(.*?)($|\+|:).*',segment)
        if match:
            self.message_header['message_identifier']=match.group(1)
            self.message_header['message_type']=match.group(2)
            self.message_header['message_version']=match.group(3)
            self.message_header['message_release']=match.group(4)
            self.message_header['controlling_agency']=match.group(5)
            self.message_header['association_assigned_code']=match.group(6)
            if self.message_header['message_type']!='MSCONS':
                return('Error','Not an MSCONS message')
            newstate='UNH'
            return(newstate,self.sg.next())
        else:
            return('Error','Error',segment + "\nUNH segment didn't match")
            
    def UNHtransition(self, segment):
        match=re.search('BGM\+(.*?)\+(.*?)\+(.*?)$|\+.*$',segment)
        if match:
            self.message_header['message_name']=match.group(1)
            self.message_header['message_identification']=match.group(2)
            self.message_header['message_function']=match.group(3)
            return('BGM',self.sg.next())
        else:
            return('Error',segment + "\nBGM segment didn't match")   
            
    def BGMtransition(self, segment):
        match=re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)',segment)
        if match:
            self.message_header['message_dtm_qualifier']=match.group(1)
            self.message_header['message_dtm']=match.group(2)
            self.message_header['message_dtm_format']=match.group(3)
            return('DTMmsg',self.sg.next())
        else:
            return('Error',segment + "\nDTM segment didn't match")
    
    def DTMmsgtransition(self,segment):
        match=re.search('NAD\+(.*?)\+(.*?):(.*?):(.*?)$',segment)
        if match:
            if match.group(1) == 'MS':
                self.message_header['sender']=match.group(2)
            if match.group(1) == 'MR':
                self.message_header['receiver']=match.group(2)
            return('NAD',self.sg.next())
        else:
            return('Error',segment + "\nNAD segment didn't match")
            
    def NADtransition(self,segment):
        if segment==None:
            self.__LpChunks.append(self.__currentLpChunk)
            self.__currentLpChunk=[]
            return('NAD',self.sg.next())
        match=re.search('NAD\+(.*?)\+(.*?):(.*?):(.*?)$',segment)
        if match:
            if match.group(1) == 'MS':
                self.message_header['sender']=match.group(2)
            if match.group(1) == 'MR':
                self.message_header['receiver']=match.group(2)
            if match.group(2) == 'DP':
                self.message_header['delivery_party']=match.group(2)
            return('NAD',self.sg.next())
        else:
            match=re.search('UNS\+D',segment)
            if match:
                return('UNS',self.sg.next())
            match=re.search('LOC\+(.*?)\+(.*?):(.*?):(.*?)$|\+',segment)
            if match:
                self.__chunkLocations.append(match.group(2))
                return('LOC',self.sg.next())
            else:
                return('Error',segment + '\nExpected NAD,UNS or LOC segment')

    def UNStransition(self, segment):
        match=re.search('NAD\+.*',segment)
        if match:        
            return('NAD',segment)
        else:
            return('Error',segment + '\nExpected NAD segment')
    
    def LOCtransition(self,segment):
        match=re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)',segment)
        if match:
            if match.group(1)=='163':
                self.__locationStartTimes.append(match.group(2))
                return('DTMLOC',self.sg.next())
        else:
            return('Error',segment + "\nDTM segment didn't match")
    
    def DTMLOCtransition(self,segment):
        match=re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)',segment)
        if match:
            if match.group(1)=='164':
                self.__locationEndTimes.append(match.group(2))
                return('DTMLOC',self.sg.next())
        else:
            match=re.search('LIN\+.*',segment)
            if match:
                return('LIN',self.sg.next())
        return('Error',segment + '\nExpected DTM or LIN segment')
        
    def LINtransition(self,segment):
        match=re.search('PIA\+(.*?)\+(.*?):(.*?):(.*?)$',segment)
        if match:
            self.__chunkObis.append(match.group(3))
            return('PIA',self.sg.next())
        return('Error',segment + '\nExpected PIA segment did not match')
        
    def PIAtransition(self,segment):
        match=re.search('QTY\+(.*?):(.*?):(.*?)$',segment)
        if match:
            self.currentquantity=match.group(2)
            return('QTY',None)
        return('Error',segment + '\nExpected QTY segment')
        
    def QTYtransition(self,segment):
        if segment==None:
            return('QTY',self.sg.next())
        match=re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)',segment)
        if match:
            if match.group(1)=='163':
                self.currentstarttime=self.dateconvert(match.group(2),match.group(3))
                return('DTMstart',self.sg.next())
        return('Error',segment + "\nExpected DTM segment didn't match")
                
    def DTMstarttransition(self,segment):
        match=re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)',segment)
        if match:
            if match.group(1)=='164':
                self.currentendtime=self.dateconvert(match.group(2),match.group(3))
                return('DTMend',self.sg.next())
        return('Error',segment + "\nExpected DTM segment didn't match")
    
    def DTMendtransition(self,segment):
        match=re.search('QTY\+(.*?):(.*?):(.*?)$',segment)
        if match:
            self.__currentLpChunk.append((self.currentstarttime,self.currentendtime,self.currentquantity))
            self.currentquantity=match.group(2)
            return('QTY',None)
        match=re.search('NAD\+.*',segment)
        if match:
            return('NAD',None)
        match=re.search('UNT\+(.*?)\+(.*?)$',segment)
        if match:
            self.__LpChunks.append(self.__currentLpChunk)
            return('UNT',segment)
        return('Error',segment + '\nExpected QTY, NAD, or UNT segment')
        
    
    def UNTtransition(self,segment):
        match=re.search('UNT\+(.*?)\+(.*?)$',segment)
        if match:
            if len(self.sg.segments)-3 != int(match.group(1)):
                return('Error',segment + '\nincorrect number of segments.')
            else:
                return('UNZ',self.sg.next())
    
    def UNZstate(self,segment):
        match=re.search('UNZ\+.*',segment)
        if match:
            return('concatenate',None)
        return('Error',segment + '\nExpected UNZ segment')
        
    def Errorstate(self,message):
        print(message)
        return
        
    def concatenateState(self, msg):
        for i,location in enumerate(self.__chunkLocations):
            obis = self.__chunkObis[i]
            if (location,obis) not in self.lpList:
                self.lpList.append((location,obis))
        for listnum in range(len(self.lpList)):
            self.loadProfiles.append([])
        for lpIndex, locobis in enumerate (self.lpList):
            for chunkIndex, chunk in enumerate(self.__LpChunks):
                if self.__chunkLocations[chunkIndex]==locobis[0] and self.__chunkObis[chunkIndex]==locobis[1]:
                    self.loadProfiles[lpIndex].extend(chunk)                    
        return('End',None)
        
    def dateconvert(self,dtmstring,dtmformat):
        if dtmformat=='303':        
            match=re.search('(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\?\+|-)(\d{2})',dtmstring)
            if match:
                y=int(match.group(1))
                m=int(match.group(2))
                d=int(match.group(3))
                h=int(match.group(4))
                mi=int(match.group(5))
                dtm=datetime.datetime(y,m,d,h,mi)
            else:
                return None
        else:
            return None
        return  dtm

        
    def __init__(self, filename):   
        self.sg=SegmentGenerator(filename)
        self.sm=StateMachine()
        self.sm.add_state('Start',self.starttransition)
        self.sm.add_state('Error',self.Errorstate, end_state=1)
        self.sm.add_state('UNB',self.UNBtransition)
        self.sm.add_state('UNH',self.UNHtransition)
        self.sm.add_state('BGM',self.BGMtransition)
        self.sm.add_state('DTMmsg',self.DTMmsgtransition)
        self.sm.add_state('NAD',self.NADtransition)
        self.sm.add_state('UNS',self.UNStransition)
        self.sm.add_state('LOC',self.LOCtransition)
        self.sm.add_state('DTMLOC',self.DTMLOCtransition)
        self.sm.add_state('LIN',self.LINtransition)
        self.sm.add_state('PIA',self.PIAtransition)
        self.sm.add_state('QTY',self.QTYtransition)
        self.sm.add_state('DTMstart',self.DTMstarttransition)
        self.sm.add_state('DTMend',self.DTMendtransition)
        self.sm.add_state('UNT',self.UNTtransition)
        self.sm.add_state('UNZ',self.UNZstate)
        self.sm.add_state('Concatenate', self.concatenateState)
        self.sm.add_state('End',None,end_state=1)
        self.sm.set_start('Start')
        self.sm.run(self.sg.next())
        
if __name__ == '__main__':
    mscons=MSCONSparser('LG-example.mscons.txt')
    