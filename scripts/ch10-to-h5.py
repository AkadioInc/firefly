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
def derive_tmats_attrs(h5grp, tmats_buff):
    """Parse TMATS buffer to store TMATS attributes and their values."""
    tmats_str = tmats_buff.decode('ascii')
    if tmats_str:
        tmats_grp = h5grp.create_group('TMATS')
        tmats = re.split('\r?\n', tmats_str)
        for tma in tmats:
            if tma:
                if tma[-1] != ';':
                    lggr.warning(
                        f'{tma!r}: TMATS attribute without ending semicolon')
                tmats_attr, val = tma.rstrip(';').split(':')
                if val:
                    lggr.debug(f'TMATS attribute {tmats_attr!r} = {val!r}')
                    tmats_grp.attrs[tmats_attr] = val
                else:
                    lggr.debug(f'TMATS {tmats_attr} attribute value not given')


def setup_output_content(top_grp, pckt_summary):
    """Create HDF5 groups and datasets based on the Ch10 file packet summary"""
    for where, smmry in pckt_summary.items():
        grp = top_grp.create_group(where)
        grp_path = grp.name
        nelems = smmry['count']

        if smmry['type'] == 'MIL1553_FMT_1':
            lggr.debug(f'Create HDF5 dataset data[{nelems}] in {grp_path}')
            dtype_1553 = np.dtype(
                [('time', '<i8'),
                 ('timestamp', 'S30'),
                 ('msg_error', '|u1'),
                 ('ttb', '|u1'),
                 ('word_error', '|u1'),
                 ('sync_error', '|u1'),
                 ('word_count_error', '|u1'),
                 ('rsp_tout', '|u1'),
                 ('format_error', '|u1'),
                 ('bus_id', 'S1'),
                 ('packet_version', '|u1'),
                 ('messages', h5py.special_dtype(vlen=np.dtype('<u2')))])
            dset = grp.create_dataset(
                'data', shape=(nelems,), chunks=True, dtype=dtype_1553)

            name_dtype = np.dtype(
                [('time', 'S30'),
                 ('timestamp', 'S30'),
                 ('msg_error', 'S30'),
                 ('ttb', 'S30'),
                 ('word_error', 'S30'),
                 ('sync_error', 'S30'),
                 ('word_count_error', 'S30'),
                 ('rsp_tout', 'S30'),
                 ('format_error', 'S30'),
                 ('bus_id', 'S30'),
                 ('packet_version', 'S30'),
                 ('messages', 'S30')])
            names = ('1553 intra-packet time',
                     '1553 intra-packet time stamp',
                     '1553 message error flag',
                     'time tag bits',
                     'invalid word error',
                     'sync type error',
                     'word count error',
                     'response time out',
                     'format error',
                     'bus id',
                     '1553 packet version',
                     '1553 packet message data')
            dset.attrs.create('name', np.array(names, dtype=name_dtype))

            # Create alias HDF5 paths for created datasets...
            if 'alias' in smmry:
                for where in smmry['alias']:
                    grp = top_grp.create_group(where)
                    lggr.debug(f'Hard link {dset.name} from {grp.name}')
                    grp['data'] = dset

        elif smmry['type'] == 'VIDEO_FMT_0':
            lggr.debug(f'Create HDF5 dataset data[{nelems}] in {grp_path}')
            dset = grp.create_dataset('data', shape=(nelems,),
                                      chunks=True, dtype=np.dtype('|V188'))
            dset.attrs['name'] = 'video transfer stream'


def append_dset(h5dset, pos_cursor, arr, buffer=None):
    """Add given NumPy array data (``arr``) to specified HDF5 dataset at the
    next position.
    """
    MAX_BUFFER_SIZE = 10
    next_pos = h5dset.shape[0] - pos_cursor
    dset_name = h5dset.name
    lggr.debug(f'Insert data to {dset_name} at position {next_pos}')
    if buffer is not None:
        if dset_name not in buffer:
            lggr.debug(f"allocating buffer for {dset_name}")
            buffer[dset_name] = np.zeros((MAX_BUFFER_SIZE,), dtype=h5dset.dtype)
        des = buffer[dset_name]
        des[next_pos % MAX_BUFFER_SIZE] = arr
        if (next_pos + 1) % MAX_BUFFER_SIZE == 0:
            lggr.debug(f"writing buffer to dset {dset_name}")
            h5dset[(next_pos - MAX_BUFFER_SIZE):next_pos] = des

    else:
        # just write to the file
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
    """Convert IRIG timestamp into nanoseconds since 1970-01-01T00:00:00Z"""
    t = datetime.strptime(tstamp, '%Y/%m/%d %H:%M:%S.%f').timestamp()
    return int(t * 1_000_000_000)
################################################################################


parser = argparse.ArgumentParser(
    description='Convert Ch10 data into an HDF5-based format',
    epilog='Copyright (c) 2019 Akadio Inc.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ch10', metavar='FILE', help='Ch10 input file', type=Path)
parser.add_argument('--outfile', '-o', metavar='H5FILE', type=Path,
                    help='Output HDF5 file. Use Ch10 file name if not given.')
parser.add_argument('--aircraft-type', metavar='TYPE', type=str,
                    help='Aircraft type. Required.')
parser.add_argument('--aircraft-id', metavar='TAILID', type=str,
                    help='Aircraft tail/serial number. Required.')
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
lggr.debug(f'Aircraft type = {arg.aircraft_type}')
lggr.debug(f'Tail/serial number = {arg.aircraft_id}')
lggr.debug(f'Logging level = {arg.loglevel}')

if not arg.aircraft_id and not arg.aircraft_type:
    raise SystemExit('Aircraft type or tail/serial number not given')

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
lggr.debug('Create /chapter11_data group')
rawgrp = h5f.create_group('chapter11_data')
lggr.debug('Create /derived group')
paragrp = h5f.create_group('derived')
lggr.debug('Set up content in the HDF5 file')
setup_output_content(rawgrp, pckt_summary)

lggr.info(f'Iterate over {str(arg.ch10)} packet data')
pcntr = 0
buffer = dict()

for packet in ch10.packet_headers():
    pcntr += 1
    lggr.info(f'Packet #{pcntr} type: '
              f'{Py106.Packet.DataType.TypeName(packet.DataType)}')
    if packet.DataType == Py106.Packet.DataType.TMATS:
        lggr.debug(f'Require {paragrp.name}/TMATS HDF5 group and store TMATS '
                   f'attributes')
        ch10.read_data()
        rawgrp.attrs['rcc_version'] = ch10_tmats.ch10ver
        derive_tmats_attrs(paragrp, ch10.Buffer.raw[4:ch10.Header.DataLen])
        tmats_grp = rawgrp.create_group('TMATS')
        dset = tmats_grp.create_dataset(
            'data', shape=(),
            data=np.void(ch10.Buffer.raw[4:ch10.Header.DataLen]))
        dset.attrs['name'] = 'TMATS buffer'
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
            data = data_grp['data']

            msg_err = msg.p1553Hdr.contents.Field.BlockStatus.MsgError
            word_cnt = ch10_1553.word_cnt(msg.pCmdWord1.contents.Value)
            messages = np.array(
                [msg.pData.contents[i] for i in range(word_cnt)],
                dtype='<u2')
            tstamp = str(ch10_time.RelInt2IrigTime(
                msg.p1553Hdr.contents.Field.PktTime))
            time = epoch_time(tstamp)
            ttb = msg.pChanSpec.contents.TTB
            word_error = msg.p1553Hdr.contents.Field.BlockStatus.WordError
            sync_error = msg.p1553Hdr.contents.Field.BlockStatus.SyncError
            word_count_error = \
                msg.p1553Hdr.contents.Field.BlockStatus.WordCntError
            rsp_tout = msg.p1553Hdr.contents.Field.BlockStatus.RespTimeout
            format_error = msg.p1553Hdr.contents.Field.BlockStatus.FormatError
            bus_id = ('A', 'B')[msg.p1553Hdr.contents.Field.BlockStatus.BusID]
            packet_version = packet.DataType

            append_dset(data, cursor,
                        np.array((time, tstamp, msg_err, ttb, word_error,
                                  sync_error, word_count_error, rsp_tout,
                                  format_error, bus_id, packet_version,
                                  messages),
                                 dtype=data.dtype))

            pckt_summary[grp1553]['count'] -= 1

    elif packet.DataType == Py106.Packet.DataType.VIDEO_FMT_0:
        ch10.read_data()
        ch = ch10.Header.ChID
        where = f'Video Format 0/Ch_{ch}'
        data_grp = rawgrp[where]
        lggr.debug(f'Add packet data in {data_grp.name} HDF5 group')
        for msg in ch10_vidf0.msgs():
            cursor = pckt_summary[where]['count']
            append_dset(data_grp['data'], cursor, msg.TSData(as_bytes=True))
            pckt_summary[where]['count'] -= 1

    lggr.info(f'Packet #{pcntr} finished processing')

# Store some useful metadata...
h5f.attrs['ch10_file'] = arg.ch10.name
h5f.attrs['ch10_file_checksum'] = f'SHA-256:{compute_sha256(arg.ch10)}'
tstart, tend = ch10_time_coverage(ch10, ch10_time)
h5f.attrs['time_coverage_start'] = tstart.isoformat() + 'Z'
h5f.attrs['time_coverage_end'] = tend.isoformat() + 'Z'
dt = datetime.utcnow().isoformat() + 'Z'
h5f.attrs['date_created'] = dt
h5f.attrs['date_modified'] = dt
h5f.attrs['date_metadata_modified'] = dt
h5f.attrs['aircraft_type'] = arg.aircraft_type
h5f.attrs['aircraft_id'] = arg.aircraft_id

lggr.debug(f'Close {h5f.filename} file')
h5f.close()
lggr.debug(f'Close {str(arg.ch10)} file')
ch10.close()
lggr.info('Done')
