# ---------------------------------------------------------------------------------
# Ch10Summary.py - A program to read Ch 10 data files and produce a summary
# report.
# ---------------------------------------------------------------------------------

import sys
import os

import Py106
import Py106.MsgDecodeTMATS
import Py106.Time


def RecorderVer2String(RecVersion):
    if (RecVersion == 0):
        return "106-05 or earlier"
    elif (RecVersion == 7):
        return "106-07"
    elif (RecVersion == 8):
        return "106-09"
    elif (RecVersion == 9):
        return "106-11"
    elif (RecVersion == 10):
        return "106-13"
    elif (RecVersion == 11):
        return "106-15"
    elif (RecVersion == 12):
        return "106-17"
    elif (RecVersion == 13):
        return "106-19"
    else:
        return "Unknown"


# Find the R index and R\DSI index for a given Channel ID number
def Find_R_DSI_Num(ChID):
    sNumIndexes = DecodeTmats.find("R-1\\N")
    if sNumIndexes == "":
        return None

    ReturnVal = None
    for Index in range(1, int(sNumIndexes) + 1):
        sTMATS = "R-1\\TK1-{0}".format(Index)
        sChID = DecodeTmats.find(sTMATS)
        if int(sChID) == ChID:
            ReturnVal = (1, Index)

    return ReturnVal


def Make_Ch10_Summary(Ch10Filename):
    print("")
    print("-----------------------------------")
    print("IRIG 106 Ch 10/11 Data File Summary")
    print("-----------------------------------")

    # Get some info about the file
    # ----------------------------

    FilePath, FileName = os.path.split(Ch10Filename)
    FileSize = os.path.getsize(Ch10Filename)

    # Read the file contents
    # ----------------------

    # Initialize counts variables
    Counts = {}

    RetStatus = PktIO.open(Ch10Filename, Py106.Packet.FileMode.READ)
    if RetStatus != Py106.Status.OK:
        print("Error opening data file '{0}'".format(Ch10Filename))
        return

    TimeUtils.SyncTime(False, 0)

    # Using Python iteration
    for PktHdr in PktIO.packet_headers():
        # Check for TMATS
        if PktHdr.DataType == Py106.Packet.DataType.TMATS:
            PktIO.read_data()
            status = DecodeTmats.decode_tmats()

        if (PktHdr.ChID, PktHdr.DataType) in Counts:
            Counts[(PktHdr.ChID, PktHdr.DataType)] += 1
        else:
            Counts[(PktHdr.ChID, PktHdr.DataType)] = 1

    # Gather some info
    # ----------------

    IrigVersion = DecodeTmats.TmatsInfo.Ch10Version
    TmatsVersion = DecodeTmats.find(r"G\106")
    RecorderManu = DecodeTmats.find(r"R-1\RI1")
    RecorderModel = DecodeTmats.find(r"R-1\RI2")
    RecDateTime = DecodeTmats.find(r"R-1\RI4")
    RecorderFirmware = DecodeTmats.find(r"R-1\RI10")

    if (DecodeTmats.find(r"R-1\IDX\\E") == "T"):
        IndexEnabled = "Enabled"
    else:
        IndexEnabled = "Disabled"

    if (DecodeTmats.find(r"R-1\EV\E") == "T"):
        EventsEnabled = "Enabled"
    else:
        EventsEnabled = "Disabled"

    # Get the data start and stop time
    PktIO.first()
    PktIO.read_next_header()
    PktIO.read_next_header()
    StartTime = TimeUtils.Rel2IrigTime(PktIO.Header.RefTime)

    PktIO.last()
    PktIO.read_next_header()
    while PktIO.Header.DataType == Py106.Packet.DataType.RECORDING_INDEX:
        PktIO.read_prev_header()
    StopTime = TimeUtils.Rel2IrigTime(PktIO.Header.RefTime)

    # Print out the results
    # ---------------------

    print("File Name                : {0}".format(FileName))
    print("File Size                : {0:#0,} bytes".format(FileSize))
    print("Recorder Manufacturer    : {0}".format(RecorderManu))
    print("Recorder Model           : {0}".format(RecorderModel))
    print("Recorder Firmware        : {0}".format(RecorderFirmware))
    print("IRIG 106 Version (Data)  : {0}".format(RecorderVer2String(IrigVersion)))
    print("IRIG 106 Version (TMATS) : 106-{0}".format(TmatsVersion))
    print("Indexing                 : {0}".format(IndexEnabled))
    print("Events                   : {0}".format(EventsEnabled))
    print("Recording Date / Time    : {0}".format(RecDateTime))
    print("Data Start Time          : {0}".format(StartTime))
    print("Data Stop Time           : {0}".format(StopTime))

    print("Data Types               : Channel  Data Type              (Type Num)  Packet Count")
    print("                           -------  ---------------------- ----------  ------------")
    for (ChID, DataTypeNum) in sorted(Counts.keys()):
        print("                            {0:>5}   {1:<24} (0x{2:02x})    {3:>10}  ".format(ChID, Py106.Packet.DataType.TypeName(DataTypeNum), DataTypeNum, Counts[(ChID, DataTypeNum)]), end='')
        # Print some more info for some selected channels
        if (DataTypeNum == Py106.Packet.DataType.PCM_FMT_0) or \
           (DataTypeNum == Py106.Packet.DataType.PCM_FMT_1):
            (R_Index, R_DSI_Index) = Find_R_DSI_Num(ChID)
            R_Search = "R-{0}\\PDP-{1}".format(R_Index, R_DSI_Index)
            Tmats_PDP = DecodeTmats.find(R_Search)
            if Tmats_PDP == "UN":
                PCM_Mode = "Unpacked"
            elif Tmats_PDP == "TM":
                PCM_Mode = "Throughput"
            elif Tmats_PDP == "PFS":
                PCM_Mode = "Packed with Frame Sync"
            else:
                PCM_Mode = "Unknown PCM Mode"
            print(" {0}".format(PCM_Mode))
        elif (DataTypeNum == Py106.Packet.DataType.ANALOG):
            R_Indexes = Find_R_DSI_Num(ChID)
            if R_Indexes is not None:
                (R_Index, R_DSI_Index) = R_Indexes
                R_Search = "R-{0}\\ADP-{1}".format(R_Index, R_DSI_Index)
                Tmats_ADP = DecodeTmats.find(R_Search)
                if Tmats_ADP == "YES":
                    Analog_Mode = "Packed"
                elif Tmats_ADP == "NO":
                    Analog_Mode = "Unpacked"
                else:
                    Analog_Mode = ""
                print(" {0}".format(Analog_Mode))
            else:
                print("")
        else:
            print("")

    # Free up the previously malloc'ed TMATS memory and close the data file
    DecodeTmats.free_tmatsinfo()
    PktIO.close()
# =============================================================================


PktIO = Py106.Packet.IO()
DecodeTmats = Py106.MsgDecodeTMATS.DecodeTMATS(PktIO)
TimeUtils = Py106.Time.Time(PktIO)

filename = sys.argv[1]
lower_fname = filename.lower()
if lower_fname.endswith(".ch10") or lower_fname.endswith(".c10"):
    print(filename)
    Make_Ch10_Summary(filename)
