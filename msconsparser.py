"""
Created on Mon Sep 26 14:12:58 2016

@author: ChristnachJeanClaude
"""

from statemachine import StateMachine
from segmentgenerator import SegmentGenerator
import datetime
import re
import logging, sys
from autologging import traced, TRACE


@traced
class MSCONSparser:
    # information from the envelope header (UNB segment)
    # most important is 'application_reference' which influences program flow
    # dependant if application is 'LG' (whole load profile) or TL (parts of loadprofiles)
    interchange_header = {}
    # information from the message header    
    message_header = {}
    # list of tuples (location, obis-code). The loadprofiles stored
    lpList = []
    # a list of lists that are the actual loadprofiles
    loadProfiles = []
    # load profile interval in minutes (assume 15 minutes just in case)
    LGinterval = '15'
    ##### private variables #####
    _chunkLocations = []
    _locationStartTimes = []
    _locationEndTimes = []
    _chunkObis = []
    _currentLpChunk = []
    _LpChunks = []
    _currentLocation = ''

    def starttransition(self, segment):
        match = re.search('UNB\+(.*?)\+(.*?):.*?\+(.*?):.*?\+(.*?):(.*?)\+(.*?)\+.*?\+(.*?)($|\+.*)', segment)
        # https://regex101.com/r/gU3vZ9/1
        if match:
            self.interchange_header['syntax_identifier'] = match.group(1)
            self.interchange_header['sender'] = match.group(2)
            self.interchange_header['recipient'] = match.group(3)
            self.interchange_header['preparation_date'] = match.group(4)
            self.interchange_header['preparation_time'] = match.group(5)
            self.interchange_header['control_reference'] = match.group(6)
            self.interchange_header['application_reference'] = match.group(7)
            newstate = 'UNB'
            return newstate, self.sg.next()
        else:
            match = re.search('UNA:\+\.\?', segment)
            # escape character is assumed to always be '?'
            if match:
                return 'Start', self.sg.next()
        return 'Error', segment + "\nUNA or UNB segment didn't match"

    def UNBtransition(self, segment):
        match = re.search('UNH\+(.*?)\+(.*?):(.*?):(.*?):(.*?):(.*?)($|\+|:).*', segment)
        if match:
            self.message_header['message_identifier'] = match.group(1)
            self.message_header['message_type'] = match.group(2)
            self.message_header['message_version'] = match.group(3)
            self.message_header['message_release'] = match.group(4)
            self.message_header['controlling_agency'] = match.group(5)
            self.message_header['association_assigned_code'] = match.group(6)
            if self.message_header['message_type'] != 'MSCONS':
                return 'Error', 'Not an MSCONS message'
            newstate = 'UNH'
            return newstate, self.sg.next()
        else:
            return 'Error', 'Error', segment + "\nUNH segment didn't match"

    def UNHtransition(self, segment):
        match = re.search('BGM\+(.*?)\+(.*?)\+(.*?)($|\+.*$)', segment)
        if match:
            self.message_header['message_name'] = match.group(1)
            self.message_header['message_identification'] = match.group(2)
            self.message_header['message_function'] = match.group(3)
            return 'BGM', self.sg.next()
        else:
            return 'Error', segment + "\nBGM segment didn't match"

    def BGMtransition(self, segment):
        match = re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            self.message_header['message_dtm_qualifier'] = match.group(1)
            self.message_header['message_dtm'] = match.group(2)
            self.message_header['message_dtm_format'] = match.group(3)
            return 'DTMmsg', self.sg.next()
        else:
            return 'Error', segment + "\nDTM segment didn't match"

    def DTMmsgtransition(self, segment):
        match = re.search('NAD\+(.*?)\+(.*?):(.*?):(.*?)$', segment)
        if match:
            if match.group(1) == 'MS':
                self.message_header['sender'] = match.group(2)
            if match.group(1) == 'MR':
                self.message_header['receiver'] = match.group(2)
            return 'NAD', self.sg.next()
        match = re.search('RFF\+(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            # meter unit number is currently not used
            return 'RFF', self.sg.next()
        else:
            return 'Error', segment + "\nNAD segment didn't match, also no RFF segment"

    def NADtransition(self, segment):
        if segment is None:
            return 'NAD', self.sg.next()
        match = re.search('NAD\+(.*?)\+(.*?):(.*?):(.*?)$', segment)
        if match:
            if match.group(1) == 'MS':
                self.message_header['sender'] = match.group(2)
            if match.group(1) == 'MR':
                self.message_header['receiver'] = match.group(2)
            if match.group(2) == 'DP':
                self.message_header['delivery_party'] = match.group(2)
            return 'NAD', self.sg.next()
        else:
            match = re.search('UNS\+D', segment)
            if match:
                return 'UNS', self.sg.next()
            match = re.search('LOC\+(.*?)\+(.*?):(.*?):(.*?)$|\+', segment)
            if match:
                location = match.group(2)
                self._currentLocation = location
                return 'LOC', self.sg.next()
            else:
                return 'Error', segment + '\nExpected NAD,UNS or LOC segment'

    def UNStransition(self, segment):
        match = re.search('NAD\+.*', segment)
        if match:
            return 'NAD', self.sg.next()
        else:
            return 'Error', segment + '\nExpected NAD segment'

    def LOCtransition(self, segment):
        match = re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            if match.group(1) == '163':
                self._locationStartTimes.append(self.dateConvert(match.group(2)))
                if self.interchange_header['application_reference'] == 'LG':
                    self._locationEndTimes.append(self._locationStartTimes[-1] +
                                                  datetime.timedelta(hours=int(self.LGinterval)))
                return 'DTMLOC', self.sg.next()
        else:
            return 'Error', segment + "\nDTM segment didn't match"

    def DTMLOCtransition(self, segment):
        match = re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            if match.group(1) == '164':
                self._locationEndTimes.append(self.dateConvert(match.group(2)))
                return 'DTMLOC', self.sg.next()
            if self.interchange_header['application_reference'] == 'LG':
                if match.group(1) == '672':
                    self.LGinterval = match.group(2)
                    return 'RFF', self.sg.next()
        else:
            if self.interchange_header['application_reference'] == 'TL':
                match = re.search('LIN\+.*', segment)
                if match:
                    return 'LIN', self.sg.next()

        return 'Error', segment + '\nExpected DTM or LIN segment'

    def LINtransition(self, segment):
        match = re.search('PIA\+(.*?)\+(.*?):(.*?):(.*?)$', segment)
        if match:
            self._chunkObis.append(match.group(3))
            self._chunkLocations.append(self._currentLocation)
            if len(self._currentLpChunk) > 0:  # not the first PIA time
                self._LpChunks.append(self._currentLpChunk)
                self._currentLpChunk = []
            return 'PIA', self.sg.next()
        return 'Error', segment + '\nExpected PIA segment did not match'

    def PIAtransition(self, segment):
        match = re.search('QTY\+(.*?):(.*?)(:(.*?)$|$)', segment)
        if match:
            self.currentquantity = match.group(2)
            self.currentUnit = match.group(4)
            self.currentCode = match.group(1)
            return 'QTY', None
        return 'Error', segment + '\nExpected QTY segment'

    def RFFtransition(self, segment):
        match = re.search('RFF\+(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            # meter unit number is currently not used
            return ('RFF', self.sg.next())
        match = re.search('LIN\+.*', segment)
        if match:
            return ('LIN', self.sg.next())
        match = re.search('NAD\+(.*?)\+(.*?):(.*?):(.*?)$', segment)
        if match:
            return 'NAD', segment
        return 'Error', segment + '\nExpected LIN or NAD'

    def QTYtransition(self, segment):
        if self.interchange_header['application_reference'] == 'LG':
            if segment is None:
                self.currentstarttime = self._locationStartTimes[-1]
                self.currentendtime = self._locationEndTimes[-1]
                return 'QTY', self.sg.next()
            match = re.search('QTY\+(.*?):(.*?)(:(.*?)$|$)', segment)
            if match:
                self.currentquantity = match.group(2)
                self.currentUnit = match.group(4)
                self.currentCode = match.group(1)
                # save this quantity
                self._currentLpChunk.append((self.currentstarttime, self.currentendtime, self.currentCode,
                                             self.currentquantity, self.currentUnit))
                # next QTY's times
                self.currentendtime += datetime.timedelta(minutes=int(self.LGinterval))
                self.currentstarttime += datetime.timedelta(minutes=int(self.LGinterval))
                return 'QTY', self.sg.next()
            match = re.search('LOC\+(.*?)\+(.*?):(.*?):(.*?)', segment)
            if match:
                location = match.group(2)
                self._currentLocation = location
                return 'LOC', self.sg.next()
            match = re.search('UNT\+.*', segment)
            if match:
                self._LpChunks.append(self._currentLpChunk)
                self.currentLpChunk = []
                return 'UNT', segment
            match = re.search('LIN\+.*', segment)
            if match:
                return 'LIN', self.sg.next()
        else:  # application = TL
            if segment == None:
                return 'QTY', self.sg.next()
        match = re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            if match.group(1) == '163':
                self.currentstarttime = self.dateConvert(match.group(2), match.group(3))
                return 'DTMstart', self.sg.next()
        return 'Error', segment + "\nExpected DTM segment didn't match"

    def DTMstarttransition(self, segment):
        match = re.search('DTM\+(.*?):(.*?):(.*?)($|\+.*|:.*)', segment)
        if match:
            if match.group(1) == '164':
                self.currentendtime = self.dateConvert(match.group(2), match.group(3))
                return 'DTMend', self.sg.next()
        return 'Error', segment + "\nExpected DTM segment didn't match"

    def DTMendtransition(self, segment):
        match = re.search('QTY\+(.*?):(.*?)(:(.*?)$|$)', segment)
        if match:
            # save the previous measurement data
            self._currentLpChunk.append(
                (self.currentstarttime, self.currentendtime, self.currentCode, self.currentquantity, self.currentUnit))
            # belongs to the now current data            
            self.currentquantity = match.group(2)
            self.currentUnit = match.group(4)
            self.currentCode = match.group(1)
            return 'QTY', None
        match = re.search('NAD\+.*', segment)
        if match:
            return 'NAD', None
        match = re.search('UNT\+(.*?)\+(.*?)$', segment)
        if match:
            self._currentLpChunk.append(
                (self.currentstarttime, self.currentendtime, self.currentCode, self.currentquantity, self.currentUnit))
            self._LpChunks.append(self._currentLpChunk)
            self._currentLpChunk = []
            return 'UNT', segment
        match = re.search('LIN\+.*', segment)
        if match:
            self._currentLpChunk.append(
                (self.currentstarttime, self.currentendtime, self.currentCode, self.currentquantity, self.currentUnit))
            return 'LIN', self.sg.next()
        return 'Error', segment + '\nExpected QTY, NAD, LIN or UNT segment'

    def UNTtransition(self, segment):
        match = re.search('UNT\+(.*?)\+(.*?)$', segment)
        # ***** disabled checking of segment count for now, because we get messages with wrong count *******
        #        if self.interchange_header['application_reference']=='TL':
        #            offset=3
        #        else:
        #            offset=4
        #        if match:
        #            if len(self.sg.segments)-offset != int(match.group(1)):
        #                return('Error',segment + '\nincorrect number of segments.')
        #            else:
        #                return('UNZ',self.sg.next())
        if match:
            return 'UNT', self.sg.next()
        # if UNH then a new message begins
        match = re.search('UNH\+(.*?)\+(.*?):(.*?):(.*?):(.*?):(.*?)($|\+|:).*', segment)
        if match:
            # TODO: the headers of the old message get overwritten. Need headers per message
            self.message_header['message_identifier'] = match.group(1)
            self.message_header['message_type'] = match.group(2)
            self.message_header['message_version'] = match.group(3)
            self.message_header['message_release'] = match.group(4)
            self.message_header['controlling_agency'] = match.group(5)
            self.message_header['association_assigned_code'] = match.group(6)
            if self.message_header['message_type'] != 'MSCONS':
                return 'Error', 'Not an MSCONS message'
            return 'UNH', self.sg.next()
        match = re.search('UNZ\+.*', segment)
        if match:
            return 'UNZ', segment
        return 'Error', segment + '\nUNH Expected and UNZ segment or a new message with UNH'

    def UNZstate(self, segment):
        match = re.search('UNZ\+.*', segment)
        if match:
            return 'concatenate', None
        return 'Error', segment + '\nExpected UNZ segment'

    def Errorstate(self, message):
        print(message)
        return

    def concatenateState(self, msg):
        for i, location in enumerate(self._chunkLocations):
            obis = self._chunkObis[i]
            if (location, obis) not in self.lpList:
                self.lpList.append((location, obis))
        for listnum in range(len(self.lpList)):
            self.loadProfiles.append([])
        for lpIndex, locobis in enumerate(self.lpList):
            for chunkIndex, chunk in enumerate(self._LpChunks):
                if self._chunkLocations[chunkIndex] == locobis[0] and self._chunkObis[chunkIndex] == locobis[1]:
                    self.loadProfiles[lpIndex].extend(chunk)
        return 'End', None

    def dateConvert(self, dtmstring, dtmformat='303'):
        if dtmformat == '303':
            match = re.search('(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\?\+|-)(\d{2})', dtmstring)
            if match:
                y = int(match.group(1))
                m = int(match.group(2))
                d = int(match.group(3))
                h = int(match.group(4))
                mi = int(match.group(5))
                dtm = datetime.datetime(y, m, d, h, mi)
            else:
                return None
        else:
            return None
        return dtm

    def __init__(self, filename):
        self.sg = SegmentGenerator(filename)
        self.sm = StateMachine()
        self.sm.add_state('Start', self.starttransition)
        self.sm.add_state('Error', self.Errorstate, end_state=1)
        self.sm.add_state('UNB', self.UNBtransition)
        self.sm.add_state('UNH', self.UNHtransition)
        self.sm.add_state('BGM', self.BGMtransition)
        self.sm.add_state('DTMmsg', self.DTMmsgtransition)
        self.sm.add_state('NAD', self.NADtransition)
        self.sm.add_state('UNS', self.UNStransition)
        self.sm.add_state('LOC', self.LOCtransition)
        self.sm.add_state('DTMLOC', self.DTMLOCtransition)
        self.sm.add_state('RFF', self.RFFtransition)
        self.sm.add_state('LIN', self.LINtransition)
        self.sm.add_state('PIA', self.PIAtransition)
        self.sm.add_state('QTY', self.QTYtransition)
        self.sm.add_state('DTMstart', self.DTMstarttransition)
        self.sm.add_state('DTMend', self.DTMendtransition)
        self.sm.add_state('UNT', self.UNTtransition)
        self.sm.add_state('UNZ', self.UNZstate)
        self.sm.add_state('Concatenate', self.concatenateState)
        self.sm.add_state('End', None, end_state=1)
        self.sm.set_start('Start')
        self.sm.run(self.sg.next())


if __name__ == '__main__':
    logging.basicConfig(level=TRACE, stream=sys.stdout, format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")
    mscons = MSCONSparser('current_example.txt')
