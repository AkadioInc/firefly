class PacketType(object):
    """ Packet Message Types """
    COMPUTER_0 = 0x00
    USER_DEFINED = 0x00
    COMPUTER_1 = 0x01
    TMATS = 0x01
    COMPUTER_2 = 0x02
    RECORDING_EVENT = 0x02
    COMPUTER_3 = 0x03
    RECORDING_INDEX = 0x03
    COMPUTER_4 = 0x04
    COMPUTER_5 = 0x05
    COMPUTER_6 = 0x06
    COMPUTER_7 = 0x07
    PCM_FMT_0 = 0x08
    PCM_FMT_1 = 0x09
    IRIG_TIME = 0x11
    MIL1553_FMT_1 = 0x19
    MIL1553_16PP194 = 0x1A
    ANALOG = 0x21
    DISCRETE = 0x29
    MESSAGE = 0x30
    ARINC_429_FMT_0 = 0x38
    VIDEO_FMT_0 = 0x40
    VIDEO_FMT_1 = 0x41
    VIDEO_FMT_2 = 0x42
    IMAGE_FMT_0 = 0x48
    IMAGE_FMT_1 = 0x49
    UART_FMT_0 = 0x50
    IEEE1394_FMT_0 = 0x58
    IEEE1394_FMT_1 = 0x59
    PARALLEL_FMT_0 = 0x60
    ETHERNET_FMT_0 = 0x68
    CAN_BUS = 0x78
    FIBRE_CHAN_FMT_0 = 0x79
    FIBRE_CHAN_FMT_1 = 0x7A

    @staticmethod
    def TypeName(TypeNum):
        name = {PacketType.USER_DEFINED: "User Defined",
                PacketType.TMATS: "TMATS",
                PacketType.RECORDING_EVENT: "Event",
                PacketType.RECORDING_INDEX: "Index",
                PacketType.COMPUTER_4: "Computer Generated 4",
                PacketType.COMPUTER_5: "Computer Generated 5",
                PacketType.COMPUTER_6: "Computer Generated 6",
                PacketType.COMPUTER_7: "Computer Generated 7",
                PacketType.PCM_FMT_0: "PCM Format 0",
                PacketType.PCM_FMT_1: "PCM Format 1",
                PacketType.IRIG_TIME: "Time",
                PacketType.MIL1553_FMT_1: "1553",
                PacketType.MIL1553_16PP194: "16PP194",
                PacketType.ANALOG: "Analog",
                PacketType.DISCRETE: "Discrete",
                PacketType.MESSAGE: "Message",
                PacketType.ARINC_429_FMT_0: "ARINC 429",
                PacketType.VIDEO_FMT_0: "Video Format 0",
                PacketType.VIDEO_FMT_1: "Video Format 1",
                PacketType.VIDEO_FMT_2: "Video Format 2",
                PacketType.IMAGE_FMT_0: "Image Format 0",
                PacketType.IMAGE_FMT_1: "Image Format 1",
                PacketType.UART_FMT_0: "UART",
                PacketType.IEEE1394_FMT_0: "IEEE 1394 Format 0",
                PacketType.IEEE1394_FMT_1: "IEEE 1394 Format 1",
                PacketType.PARALLEL_FMT_0: "Parallel",
                PacketType.ETHERNET_FMT_0: "Ethernet",
                PacketType.CAN_BUS: "CAN Bus",
                PacketType.FIBRE_CHAN_FMT_0: "Fibre Channel Format 0",
                PacketType.FIBRE_CHAN_FMT_1: "Fibre Channel Format 1"}
        return name[TypeNum]
