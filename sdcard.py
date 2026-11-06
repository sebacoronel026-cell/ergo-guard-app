import machine
import time

_CMD_TIMEOUT = const(100)
_R1_IDLE_STATE = const(1 << 0)
_R1_ILLEGAL_COMMAND = const(1 << 2)
_TOKEN_CMD25 = const(0xFC)
_TOKEN_STOP_TRAN = const(0xFD)
_TOKEN_DATA = const(0xFE)

class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        self.tokenbuf = bytearray(1)
        for i in range(512):
            self.dummybuf[i] = 0xFF
        self.dummybuf_memoryview = memoryview(self.dummybuf)
        self.init_card()

    def init_spi(self, baudrate):
        try:
            master = self.spi.MASTER
        except AttributeError:
            self.spi.init(baudrate=baudrate, phase=0, polarity=0)
        else:
            self.spi.init(master, baudrate=baudrate, phase=0, polarity=0)

    def init_card(self):
        self.cs.init(self.cs.OUT, value=1)
        self.init_spi(100000)
        for i in range(16):
            self.spi.write(b"\xff")
        for _ in range(5):
            if self.cmd(0, 0, 0x95) == _R1_IDLE_STATE:
                break
        else:
            raise OSError("no SD card")
        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == _R1_IDLE_STATE:
            self.init_card_v2()
        elif r == (_R1_IDLE_STATE | _R1_ILLEGAL_COMMAND):
            self.init_card_v1()
        else:
            raise OSError("couldn't determine SD card version")
        if self.cmd(9, 0, 0, 0, False) != 0:
            raise OSError("no response from SD card")
        csd = bytearray(16)
        self.readinto(csd)
        if csd[0] & 0xC0 == 0x40:
            self.cdv = 1
        else:
            self.cdv = 512
        if self.cmd(16, 512, 0) != 0:
            raise OSError("can't set 512 block size")

    def init_card_v1(self):
        for i in range(_CMD_TIMEOUT):
            self.cmd(55, 0, 0)
            if self.cmd(41, 0, 0) == 0:
                self.init_spi(100000)
                return
        raise OSError("timeout waiting for v1 card")

    def init_card_v2(self):
        for i in range(_CMD_TIMEOUT):
            time.sleep_ms(50)
            self.cmd(58, 0, 0, 4)
            self.cmd(55, 0, 0)
            if self.cmd(41, 0x40000000, 0) == 0:
                self.cmd(58, 0, 0, 4)
                self.init_spi(100000)
                return
        raise OSError("timeout waiting for v2 card")

    def cmd(self, cmd, arg, crc, final=0, release=True, skip1=False):
        self.cs(0)
        self.cmdbuf[0] = 0x40 | cmd
        self.cmdbuf[1] = arg >> 24
        self.cmdbuf[2] = arg >> 16
        self.cmdbuf[3] = arg >> 8
        self.cmdbuf[4] = arg
        self.cmdbuf[5] = crc
        self.spi.write(self.cmdbuf)
        if skip1:
            self.spi.readinto(self.tokenbuf, 0xFF)
        for i in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            response = self.tokenbuf[0]
            if not (response & 0x80):
                if cmd == 58:
                    for _ in range(final):
                        self.spi.write(b"\xff")
                else:
                    for _ in range(final):
                        self.spi.readinto(self.tokenbuf, 0xFF)
                if release:
                    self.cs(1)
                    self.spi.write(b"\xff")
                return response
        self.cs(1)
        self.spi.write(b"\xff")
        return -1

    def readinto(self, buf):
        self.cs(0)
        for i in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] == _TOKEN_DATA:
                break
            time.sleep_ms(1)
        else:
            self.cs(1)
            raise OSError("timeout waiting for response")
        mv = self.dummybuf_memoryview
        if len(buf) != len(mv):
            mv = mv[: len(buf)]
        self.spi.write_readinto(mv, buf)
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")
        self.cs(1)
        self.spi.write(b"\xff")

    def write(self, token, buf):
        self.cs(0)
        self.spi.readinto(self.tokenbuf, 0xFF)
        self.spi.readinto(self.tokenbuf, 0xFF)
        self.tokenbuf[0] = token
        self.spi.write(self.tokenbuf)
        self.spi.write(buf)
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")
        if (self.spi.read(1)[0] & 0x1F) != 0x05:
            self.cs(1)
            self.spi.write(b"\xff")
            return False
        while self.spi.read(1)[0] == 0:
            pass
        self.cs(1)
        self.spi.write(b"\xff")
        return True

    def write_token(self, token):
        self.cs(0)
        self.spi.readinto(self.tokenbuf, 0xFF)
        self.spi.readinto(self.tokenbuf, 0xFF)
        self.tokenbuf[0] = token
        self.spi.write(self.tokenbuf)
        self.spi.readinto(self.tokenbuf, 0xFF)
        while self.tokenbuf[0] == 0:
            self.spi.readinto(self.tokenbuf, 0xFF)
        self.cs(1)
        self.spi.write(b"\xff")

    def readblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        if nblocks == 1:
            if self.cmd(17, block_num * self.cdv, 0, release=False) != 0:
                self.cs(1)
                raise OSError(5)
            self.readinto(buf)
        else:
            if self.cmd(18, block_num * self.cdv, 0, release=False) != 0:
                self.cs(1)
                raise OSError(5)
            offset = 0
            mv = memoryview(buf)
            while nblocks:
                self.readinto(mv[offset : offset + 512])
                offset += 512
                nblocks -= 1
            if self.cmd(12, 0, 0xFF, skip1=True):
                raise OSError(5)

    def writeblocks(self, block_num, buf):
        nblocks, err = len(buf) // 512, False
        if nblocks == 1:
            if self.cmd(24, block_num * self.cdv, 0) != 0:
                raise OSError(5)
            err = not self.write(_TOKEN_DATA, buf)
        else:
            if self.cmd(25, block_num * self.cdv, 0) != 0:
                raise OSError(5)
            offset = 0
            mv = memoryview(buf)
            while nblocks:
                if not self.write(_TOKEN_CMD25, mv[offset : offset + 512]):
                    err = True
                    break
                offset += 512
                nblocks -= 1
            self.write_token(_TOKEN_STOP_TRAN)
        if err:
            raise OSError(5)

    def ioctl(self, op, arg):
        if op == 4:
            return self.cmd(9, 0, 0, 0, False)
        if op == 5:
            return 512
        if op == 6:
            return 0