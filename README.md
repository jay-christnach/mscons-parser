#mscons-parser
Class to parse EDIFACT MSCONS messages and converter to get a csv file from an MSCONS file.

Only the variant of MSCONS that is used by the utilies in Luxembourg will be tested. This is version 2.1a of the German MSCONS formats. The data will be accepted as liberally as possible so that possibly other dialects will also get read correctly.

##msconsparser.py##
Stores the loadprofiles and the metadata extracted from an MSCONS file in its data structures.

##mscons2csv##
Writes a semicolon delimited file with load profile data

##statemachine.py##
a simple state machine that is used by msconsparser

##segmentgenerator.py
provides a next() function to return the next segment to be analysed. Segments are delinited by "'" in EDIFACT

##TODO##
* docstrings and more comments and info
* changing state machine to accept the LG application (currently only supports TL)
* adding command line options to mscons2csv
