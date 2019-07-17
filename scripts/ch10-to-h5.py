#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path
from hashlib import sha256
from datetime import datetime
import re
import numpy as np
import h5py
import Py106
import Py106.MsgDecodeTMATS
import Py106.Time
import Py106.MsgDecode1553
import Py106.MsgDecodeVideo


################################################################################
def store_tmats_attrs(h5grp, tmats_buff):
    """Parse TMATS buffer to store as TMATS attributes and their values."""
    # Skip first four bytes in the buffer as per
    # https://github.com/bbaggerman/irig106utils/blob/4c286cf86b93b885387ee1a264b70e4a38e6e410/src/idmptmat.c#L298
    clean_tmats = tmats_buff[4:tmats_buff.rindex(b';')].decode('ascii')
    if clean_tmats:
        tmats = re.split('\r?\n', clean_tmats)
        for tma in tmats:
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

        if smmry['type'] == 'MIL1553_FMT_1':
            lggr.debug(f'Create HDF5 dataset data[{nelems}] in {grp_path}')
            dset = grp.create_dataset(
                'data', shape=(nelems,), chunks=True,
                dtype=h5py.special_dtype(vlen=np.dtype('<u2')))
            dset.attrs['long_name'] = np.string_('1553 packet message data')
            dsets['data'] = dset

            lggr.debug(f'Create HDF5 dataset timestamp[{nelems}] in {grp_path}')
            dset = grp.create_dataset('timestamp', shape=(nelems,),
                                      chunks=True, dtype='S30')
            dset.attrs['long_name'] = np.string_('1553 intra-packet time stamp')
            dsets['timestamp'] = dset

            lggr.debug(f'Create HDF5 dataset time[{nelems}] in {grp_path}')
            dset = grp.create_dataset('time', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('double'))
            dset.attrs['long_name'] = np.string_('1553 intra-packet time')
            dset.attrs['units'] = np.string_('seconds')
            dset.attrs['epoch'] = '1970-01-01T00:00:00Z'
            dsets['time'] = dset

            lggr.debug(f'Create HDF5 dataset msg_error[{nelems}] in {grp_path}')
            dset = grp.create_dataset('msg_error', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('1553 message error flag')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no message error',
                                                      'message error'])
            dsets['msg_error'] = dset

            lggr.debug(f'Create HDF5 dataset ttb[{nelems}] in {grp_path}')
            dset = grp.create_dataset('ttb', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('time tag bits')
            dset.attrs['flag_values'] = np.array([0, 1, 2, 3], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_([
                'Last bit of the last word of the message',
                'First bit of the first word of the message',
                'Last bit of the first (command) word of the message',
                'Reserved'])
            dsets['ttb'] = dset

            lggr.debug(
                f'Create HDF5 dataset word_error[{nelems}] in {grp_path}')
            dset = grp.create_dataset('word_error', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('invalid word error')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no invalid word error',
                                                      'invalid word error'])
            dsets['word_error'] = dset

            lggr.debug(
                f'Create HDF5 dataset sync_error[{nelems}] in {grp_path}')
            dset = grp.create_dataset('sync_error', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('sync type error')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no sync type error',
                                                      'sync type error'])
            dsets['sync_error'] = dset

            lggr.debug(
                f'Create HDF5 dataset word_count_error[{nelems}] in {grp_path}')
            dset = grp.create_dataset('word_count_error', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('word count error')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no word count error',
                                                      'word count error'])
            dsets['word_count_error'] = dset

            lggr.debug(f'Create HDF5 dataset rsp_tout[{nelems}] in {grp_path}')
            dset = grp.create_dataset('rsp_tout', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('response time out')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no response time out',
                                                      'response time out'])
            dsets['rsp_tout'] = dset

            lggr.debug(
                f'Create HDF5 dataset format_error[{nelems}] in {grp_path}')
            dset = grp.create_dataset('format_error', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('format error')
            dset.attrs['flag_values'] = np.array([0, 1], dtype=dset.dtype)
            dset.attrs['flag_meanings'] = np.string_(['no format error',
                                                      'format error'])
            dsets['format_error'] = dset

            lggr.debug(f'Create HDF5 dataset bus_id[{nelems}] in {grp_path}')
            dset = grp.create_dataset('bus_id', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('|S1'))
            dset.attrs['long_name'] = np.string_('Bus ID')
            dsets['bus_id'] = dset

            lggr.debug(
                f'Create HDF5 dataset packet_version[{nelems}] in {grp_path}')
            dset = grp.create_dataset('packet_version', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('uint8'))
            dset.attrs['long_name'] = np.string_('1553 packet version')
            dsets['packet_version'] = dset

            # Create alias HDF5 paths for created datasets...
            if 'alias' in smmry:
                for where in smmry['alias']:
                    grp = top_grp.create_group(where)
                    for name, dset in dsets.items():
                        lggr.debug(f'Hard link {dset.name} from {grp.name}')
                        grp[name] = dset

        elif smmry['type'] == 'VIDEO_FMT_0':
            lggr.debug(f'Create HDF5 dataset ts[{nelems}] in {grp_path}')
            dset = grp.create_dataset('ts', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('|V188'))
            dset.attrs['long_name'] = np.string_('video transfer stream')
            dsets['ts'] = dset


def append_dset(h5dset, pos_cursor, arr):
    """Add given NumPy array data (``arr``) to specified HDF5 dataset at the
    next position.
    """
    next_pos = h5dset.shape[0] - pos_cursor
    lggr.debug(f'Insert data to {h5dset.name} at position {next_pos}')
    h5dset[next_pos] = arr


def compute_sha256(fpath):
    """Compute SHA-256 checksum of the input file."""
    cksum = sha256()
    with fpath.open('rb') as f:
        for chunk in iter(lambda: f.read(100_000_000), b''):
            cksum.update(chunk)
    return cksum.hexdigest()


def ch10_time_coverage(ch10, ch10_time):
    """Get Ch10 data start and end times as datetime objects."""
    ch10.first()
    ch10.read_next_header()
    ch10.read_next_header()
    tstart = ch10_time.Rel2IrigTime(ch10.Header.RefTime)

    ch10.last()
    ch10.read_next_header()
    while ch10.Header.DataType == Py106.Packet.DataType.RECORDING_INDEX:
        ch10.read_prev_header()
    tend = ch10_time.Rel2IrigTime(ch10.Header.RefTime)

    # Convert to Python's datetime object...
    dtfmt = '%Y/%m/%d %H:%M:%S.%f'
    tstart = datetime.strptime(str(tstart), dtfmt)
    tend = datetime.strptime(str(tend), dtfmt)
    lggr.debug(f'Ch10 data time start: {tstart}')
    lggr.debug(f'Ch10 data time stop: {tend}')

    return (tstart, tend)


def epoch_time(tstamp):
    """Convert IRIG timestamp into UNIX (POSIX) epoch seconds"""
    return datetime.strptime(tstamp, '%Y/%m/%d %H:%M:%S.%f').timestamp()
################################################################################


parser = argparse.ArgumentParser(
    description='Convert Ch10 data into an HDF5-based format',
    epilog='Copyright (c) 2019 Akadio Inc.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ch10', metavar='FILE', help='Ch10 input file', type=Path)
parser.add_argument('--outfile', '-o', metavar='H5FILE', type=Path,
                    help='Output HDF5 file. Use Ch10 file name if not given.')
parser.add_argument('--loglevel', default='info',
                    choices=['debug', 'info', 'warning', 'error', 'critical'],
                    help='Logging level. Log output goes to stderr.')
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

lggr.info(f'Converting Ch10 file {str(arg.ch10)} to HDF5 file {str(outh5)}')

ch10 = Py106.Packet.IO()
ch10_tmats = Py106.MsgDecodeTMATS.DecodeTMATS(ch10)
ch10_1553 = Py106.MsgDecode1553.Decode1553F1(ch10)
ch10_vidf0 = Py106.MsgDecodeVideo.DecodeVideoF0(ch10)

lggr.info(f'Open {str(arg.ch10)} for collecting info about stored packets')
status = ch10.open(str(arg.ch10), Py106.Packet.FileMode.READ)
if status != Py106.Status.OK:
    raise IOError(f'{str(arg.ch10)}: Error opening file')

pckt_summary = dict()
pcntr = 0
lggr.info(f'Iterate over {str(arg.ch10)} packet data')
for packet in ch10.packet_headers():
    pcntr += 1
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
                pckt_summary[tx_grp1553] = pckt_summary.get(
                    tx_grp1553,
                    {'count': 0, 'alias': set(), 'type': 'MIL1553_FMT_1'})
                pckt_summary[tx_grp1553]['count'] += 1
                pckt_summary[tx_grp1553]['alias'].update([rx_grp1553])
            else:
                # RT-to-BC or BC-to-RT message
                rt = msg.pCmdWord1.contents.Field.RTAddr
                sa = msg.pCmdWord1.contents.Field.SubAddr
                tr = ('R', 'T')[msg.pCmdWord1.contents.Field.TR]
                grp1553 = f'1553/Ch_{ch}/RT_{rt}/SA_{sa}/{tr}/BC'
                pckt_summary[grp1553] = pckt_summary.get(
                    grp1553, {'count': 0, 'type': 'MIL1553_FMT_1'})
                pckt_summary[grp1553]['count'] += 1
                lggr.debug(
                    f'1553 packet #{pcntr}, message #{msg_cntr}: {grp1553}')

    elif packet.DataType == Py106.Packet.DataType.VIDEO_FMT_0:
        lggr.debug(f'Collecting info on packet #{pcntr} with VIDEO_FMT_0 data')
        ch10.read_data()
        ch = ch10.Header.ChID
        loc = f'Video Format 0/Ch_{ch}'
        pckt_summary[loc] = pckt_summary.get(loc, {'count': 0,
                                                   'type': 'VIDEO_FMT_0'})
        msg_cntr = 0
        for msg in ch10_vidf0.msgs():
            msg_cntr += 1
        pckt_summary[loc]['count'] += msg_cntr
        lggr.debug(f'Video Format 0 packet #{pcntr}: {msg_cntr} streams')

lggr.info(f'Finished collecting info on packets in {str(arg.ch10)}')
ch10.close()
lggr.debug(f'pckt_summary = {pckt_summary}')

lggr.info(f'Open {str(arg.ch10)} for reading data')
ch10 = Py106.Packet.IO()
ch10_tmats = Py106.MsgDecodeTMATS.DecodeTMATS(ch10)
ch10_time = Py106.Time.Time(ch10)
ch10_1553 = Py106.MsgDecode1553.Decode1553F1(ch10)
ch10_vidf0 = Py106.MsgDecodeVideo.DecodeVideoF0(ch10)
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
    lggr.info(f'Packet #{pcntr} type: '
              f'{Py106.Packet.DataType.TypeName(packet.DataType)}')
    if packet.DataType == Py106.Packet.DataType.TMATS:
        lggr.debug(f'Require {rawgrp.name}/TMATS HDF5 group and store TMATS '
                   f'attributes')
        tmats_grp = rawgrp.create_group('TMATS')
        ch10.read_data()
        store_tmats_attrs(tmats_grp, ch10.Buffer.raw)
        tmats_grp.attrs['rcc_version'] = np.string_(ch10_tmats.ch10ver)
        lggr.info('Finished with TMATS information')

    elif packet.DataType == Py106.Packet.DataType.MIL1553_FMT_1:
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
            tstamp = str(ch10_time.RelInt2IrigTime(
                msg.p1553Hdr.contents.Field.PktTime))
            append_dset(timestamp, cursor, np.string_(tstamp))

            append_dset(data_grp['time'], cursor, epoch_time(tstamp))

            append_dset(data_grp['ttb'], cursor, msg.pChanSpec.contents.TTB)

            append_dset(data_grp['word_error'], cursor,
                        msg.p1553Hdr.contents.Field.BlockStatus.WordError)

            append_dset(data_grp['sync_error'], cursor,
                        msg.p1553Hdr.contents.Field.BlockStatus.SyncError)

            append_dset(data_grp['word_count_error'], cursor,
                        msg.p1553Hdr.contents.Field.BlockStatus.WordCntError)

            append_dset(data_grp['rsp_tout'], cursor,
                        msg.p1553Hdr.contents.Field.BlockStatus.RespTimeout)

            append_dset(data_grp['format_error'], cursor,
                        msg.p1553Hdr.contents.Field.BlockStatus.FormatError)

            append_dset(
                data_grp['bus_id'], cursor,
                (b'A', b'B')[msg.p1553Hdr.contents.Field.BlockStatus.BusID])

            append_dset(data_grp['packet_version'], cursor, packet.DataType)

            pckt_summary[grp1553]['count'] -= 1

    elif packet.DataType == Py106.Packet.DataType.VIDEO_FMT_0:
        ch10.read_data()
        ch = ch10.Header.ChID
        where = f'Video Format 0/Ch_{ch}'
        data_grp = rawgrp[where]
        lggr.debug(f'Add packet data in {data_grp.name} HDF5 group')
        for msg in ch10_vidf0.msgs():
            cursor = pckt_summary[where]['count']
            append_dset(data_grp['ts'], cursor, msg.TSData(as_bytes=True))
            pckt_summary[where]['count'] -= 1

    lggr.info(f'Packet #{pcntr} finished processing')

# Store some useful metadata...
h5f.attrs['ch10_file'] = np.string_(arg.ch10.name)
h5f.attrs['ch10_file_checksum'] = np.string_(
    f'SHA-256:{compute_sha256(arg.ch10)}')
tstart, tend = ch10_time_coverage(ch10, ch10_time)
h5f.attrs['time_coverage_start'] = np.string_(tstart.isoformat() + 'Z')
h5f.attrs['time_coverage_end'] = np.string_(tend.isoformat() + 'Z')
dt = datetime.utcnow().isoformat() + 'Z'
h5f.attrs['date_created'] = np.string_(dt)
h5f.attrs['date_modified'] = np.string_(dt)
h5f.attrs['date_metadata_modified'] = np.string_(dt)

lggr.debug(f'Close {h5f.filename} file')
h5f.close()
lggr.debug(f'Close {str(arg.ch10)} file')
ch10.close()
lggr.info('Done')
