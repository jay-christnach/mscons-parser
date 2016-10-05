# mscons-parser
Class to parse EDIFACT MSCONS messages and converter to get a csv file from an MSCONS file.

Only the variant of MSCONS that is used by the utilies in Luxembourg will be tested. This is version 2.1a of the German MSCONS formats. The data will be accepted as liberally as possible so that possibly other dialects will also get read correctly.

##TODO##
* docstrings and more comments and info
* adding value status and unit to load profiles
* changing state machine to accept the LG application