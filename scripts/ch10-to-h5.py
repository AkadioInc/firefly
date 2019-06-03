#!/usr/bin/env python3
import argparse
import logging
import numpy as np
from pathlib import Path
import h5py
import Py106
import Py106.MsgDecodeTMATS
import Py106.Time
import Py106.MsgDecode1553


################################################################################
def store_tmats_attrs(h5grp, tmats_buff):
    """Parse TMATS buffer to store as TMATS attributes and their values."""
    # Skip first four bytes in the buffer as per
    # https://github.com/bbaggerman/irig106utils/blob/4c286cf86b93b885387ee1a264b70e4a38e6e410/src/idmptmat.c#L298
    tmats_list = tmats_buff[4:].strip(b'\x00').decode('ascii').split('\r\n')
    for tma in tmats_list:
        if tma:
            if tma[-1] != ';':
                lggr.warning(
                    f'{tma!r}: TMATS attribute without ending semicolon')
            tmats_attr, val = tma.rstrip(';').split(':')
            if val:
                lggr.debug(f'TMATS attribute {tmats_attr!r} = {val!r}')
                h5grp.attrs[tmats_attr] = np.string_(val)
            else:
                lggr.debug(f'TMATS {tmats_attr} attribute value not given')

    # Store the TMATS buffer as well...
    h5grp.attrs['buffer'] = np.void(tmats_buff)


def setup_output_content(top_grp, pckt_summary):
    """Create HDF5 groups and datasets based on the Ch10 file packet summary"""
    for where, smmry in pckt_summary.items():
        grp = top_grp.create_group(where)
        grp_path = grp.name
        nelems = smmry['count']
        dsets = dict()

        lggr.debug(f'Create HDF5 dataset data[{nelems}] in {grp_path}')
        dset = grp.create_dataset(
            'data', shape=(nelems,), chunks=True,
            dtype=h5py.special_dtype(vlen=np.dtype('<u2')))
        dset.attrs['description'] = np.string_('1553 packet message data')
        dsets['data'] = dset

        lggr.debug(f'Create HDF5 dataset timestamp[{nelems}] in {grp_path}')
        dset = grp.create_dataset('timestamp', shape=(nelems,),
                                  chunks=True, dtype='S30')
        dset.attrs['description'] = np.string_('1553 intra-packet time stamp')
        dsets['timestamp'] = dset

        lggr.debug(f'Create HDF5 dataset msg_error[{nelems}] in {grp_path}')
        dset = grp.create_dataset('msg_error', shape=(nelems,),
                                  chunks=True, dtype=np.dtype('uint8'))
        dset.attrs['description'] = np.string_('1553 message error flag')
        dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
        dset.attrs['flag_meanings'] = np.string_(['no message error',
                                                  'message error'])
        dsets['msg_error'] = dset

        # Create alias HDF5 paths for created datasets...
        if 'alias' in smmry:
            for where in smmry['alias']:
                grp = top_grp.create_group(where)
                for name, dset in dsets.items():
                    lggr.debug(f'Hard link {dset.name} from {grp.name}')
                    grp[name] = dset


def append_dset(h5dset, pos_cursor, arr):
    """Add given NumPy array data (``arr``) to specified HDF5 dataset at the
    next position.
    """
    next_pos = h5dset.shape[0] - pos_cursor
    lggr.debug(f'Insert data to {h5dset.name} at position {next_pos}')
    h5dset[next_pos] = arr
################################################################################


parser = argparse.ArgumentParser(
    description='Convert Ch10 data into an HDF5-based format',
    epilog='Copyright (c) 2019 Akadio Inc.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ch10', metavar='FILE', help='Ch10 input file', type=Path)
parser.add_argument('--outfile', '-o', metavar='H5FILE', type=Path,
                    help=('Output HDF5 file. Use Ch10 file name if not given.'))
parser.add_argument('--loglevel', default='info',
                    choices=['debug', 'info', 'warning', 'error', 'critical'],
                    help='Logging level')
arg = parser.parse_args()

# Log to stderr
logging.basicConfig(
    format='%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s',
    level=arg.loglevel.upper(),
    datefmt='%Y%m%dT%H%M%S')

lggr = logging.getLogger('ch10-to-h5')

# Show command-line options...
lggr.debug(f'Input Ch10 file = {arg.ch10}')
lggr.debug(f'Output HDF5 file = {arg.outfile}')
lggr.debug(f'Logging level = {arg.loglevel}')

if arg.ch10.is_file():
    outh5 = arg.outfile if arg.outfile else arg.ch10.with_suffix('.h5')
else:
    raise OSError(f'{str(arg.ch10)}: Does not exist or not a file')

lggr.info(
    f'Converting Ch10 file {str(arg.ch10)} to HDF5 file {str(outh5)}')

ch10 = Py106.Packet.IO()
ch10_tmats = Py106.MsgDecodeTMATS.DecodeTMATS(ch10)
ch10_1553 = Py106.MsgDecode1553.Decode1553F1(ch10)

lggr.info(f'Open {str(arg.ch10)} for collecting info about stored packets')
status = ch10.open(str(arg.ch10), Py106.Packet.FileMode.READ)
if status != Py106.Status.OK:
    raise IOError(f'{str(arg.ch10)}: Error opening file')

pckt_summary = dict()
pcntr = 0
lggr.info(f'Iterate over {str(arg.ch10)} packet data')
for packet in ch10.packet_headers():
    pcntr += 1
    # Only interested in 1553 packet data for now...
    if packet.DataType == Py106.Packet.DataType.MIL1553_FMT_1:
        lggr.debug(
            f'Collecting info on packet #{pcntr} with MIL1553_FMT_1 data')
        ch10.read_data()
        msg_cntr = 0
        for msg in ch10_1553.msgs():
            ch = ch10.Header.ChID
            msg_cntr += 1
            if msg.p1553Hdr.contents.Field.BlockStatus.RT2RT:
                # RT-to-RT message
                rx_cmd = msg.pCmdWord1.contents.Field
                tx_cmd = msg.pCmdWord2.contents.Field
                if rx_cmd.TR != 0:
                    lggr.warning(f'1553 packet #{pcntr}, message #{msg_cntr}: '
                                 f'First command word not "Receive"')
                if tx_cmd.TR != 1:
                    lggr.warning(f'1553 packet #{pcntr}, message #{msg_cntr}: '
                                 f'Second command word not "Transmit"')
                rx_grp1553 = (
                    f'1553/Ch_{ch}/RT_{rx_cmd.RTAddr}/SA_{rx_cmd.SubAddr}/R/'
                    f'RT_{tx_cmd.RTAddr}/SA_{tx_cmd.SubAddr}')
                tx_grp1553 = (
                    f'1553/Ch_{ch}/RT_{tx_cmd.RTAddr}/SA_{tx_cmd.SubAddr}/T/'
                    f'RT_{rx_cmd.RTAddr}/SA_{rx_cmd.SubAddr}')
                lggr.debug(f'1553 packet #{pcntr}, message #{msg_cntr}: '
                           f'{rx_grp1553} and {tx_grp1553}')
                pckt_summary[tx_grp1553] = pckt_summary.get(tx_grp1553,
                                                            {'count': 0,
                                                             'alias': set()})
                pckt_summary[tx_grp1553]['count'] += 1
                pckt_summary[tx_grp1553]['alias'].update([rx_grp1553])
            else:
                # RT-to-BC or BC-to-RT message
                rt = msg.pCmdWord1.contents.Field.RTAddr
                sa = msg.pCmdWord1.contents.Field.SubAddr
                tr = ('R', 'T')[msg.pCmdWord1.contents.Field.TR]
                grp1553 = f'1553/Ch_{ch}/RT_{rt}/SA_{sa}/{tr}/BC'
                pckt_summary[grp1553] = pckt_summary.get(grp1553, {'count': 0})
                pckt_summary[grp1553]['count'] += 1
                lggr.debug(
                    f'1553 packet #{pcntr}, message #{msg_cntr}: {grp1553}')
lggr.info(f'Finished collecting info on packets in {str(arg.ch10)}')
ch10.close()
lggr.debug(f'pckt_summary = {pckt_summary}')

lggr.info(f'Open {str(arg.ch10)} for reading data')
ch10 = Py106.Packet.IO()
ch10_tmats = Py106.MsgDecodeTMATS.DecodeTMATS(ch10)
ch10_time = Py106.Time.Time(ch10)
ch10_1553 = Py106.MsgDecode1553.Decode1553F1(ch10)
status = ch10.open(str(arg.ch10), Py106.Packet.FileMode.READ)
if status != Py106.Status.OK:
    raise IOError(f'{str(arg.ch10)}: Error opening file')
ch10_time.SyncTime(False, 0)

lggr.info(f'Create output HDF5 file {str(outh5)} (will overwrite)')
h5f = h5py.File(str(outh5), 'w')
lggr.debug('Create /raw group')
rawgrp = h5f.create_group('raw')
lggr.debug('Set up content in the HDF5 file')
setup_output_content(rawgrp, pckt_summary)

lggr.info(f'Iterate over {str(arg.ch10)} packet data')
pcntr = 0
for packet in ch10.packet_headers():
    pcntr += 1
    if packet.DataType == Py106.Packet.DataType.TMATS:
        lggr.info(f'Packet #{pcntr} type: TMATS')
        lggr.debug(f'Require {rawgrp.name}/TMATS HDF5 group and store TMATS '
                   f'attributes')
        tmats_grp = rawgrp.create_group('TMATS')
        ch10.read_data()
        store_tmats_attrs(tmats_grp, ch10.Buffer.raw)
        lggr.info('Finished with TMATS information')

    elif packet.DataType == Py106.Packet.DataType.MIL1553_FMT_1:
        lggr.info(f'Packet #{pcntr} type: MIL1553_FMT_1')
        ch10.read_data()

        # Loop over each message in the 1553 packet...
        for msg in ch10_1553.msgs():
            ch = ch10.Header.ChID
            if msg.p1553Hdr.contents.Field.BlockStatus.RT2RT:
                # RT-to-RT message
                rx_cmd = msg.pCmdWord1.contents.Field
                tx_cmd = msg.pCmdWord2.contents.Field
                grp1553 = (
                    f'1553/Ch_{ch}/RT_{tx_cmd.RTAddr}/SA_{tx_cmd.SubAddr}/T/'
                    f'RT_{rx_cmd.RTAddr}/SA_{rx_cmd.SubAddr}')
            else:
                # RT-to-BC or BC-to-RT message
                rt = msg.pCmdWord1.contents.Field.RTAddr
                sa = msg.pCmdWord1.contents.Field.SubAddr
                tr = ('R', 'T')[msg.pCmdWord1.contents.Field.TR]
                grp1553 = f'1553/Ch_{ch}/RT_{rt}/SA_{sa}/{tr}/BC'
            data_grp = rawgrp[grp1553]
            lggr.debug(f'Add packet data in {data_grp.name} HDF5 group')
            cursor = pckt_summary[grp1553]['count']

            msg_err = msg.p1553Hdr.contents.Field.BlockStatus.MsgError
            data = data_grp['data']
            if msg_err == 0:
                word_cnt = ch10_1553.word_cnt(msg.pCmdWord1.contents.Value)
                arr = np.array([msg.pData.contents[i] for i in range(word_cnt)],
                               dtype=data.dtype)
            else:
                arr = np.array([], dtype=data.dtype)
            append_dset(data, cursor, arr)

            append_dset(data_grp['msg_error'], cursor, msg_err)

            timestamp = data_grp['timestamp']
            tstamp = np.array(
                str(ch10_time.RelInt2IrigTime(
                    msg.p1553Hdr.contents.Field.PktTime)),
                dtype=timestamp.dtype)
            append_dset(timestamp, cursor, tstamp)

            pckt_summary[grp1553]['count'] -= 1

        lggr.info(f'Packet #{pcntr} finished processing')


lggr.debug(f'Close {h5f.filename} file')
h5f.close()
lggr.debug(f'Close {str(arg.ch10)} file')
ch10.close()
lggr.info('Done')
