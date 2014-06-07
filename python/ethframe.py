import struct


class EthFrame:
    bcast_mac = (0xff, 0xff, 0xff, 0xff, 0xff, 0xff)
    MAGIC_ONLINE = 0xffff
    MAGIC_OFFLINE = 0xfffe

    def __init__(self):
        self.raw_buf = None
        self.tgt_mac = None
        self.src_mac = None
        self.eth_type = None
        self.size = 0

    def decode(self, raw_buf):
        self.raw_buf = raw_buf
        self.tgt_mac = struct.unpack("BBBBBB", raw_buf[0:6])
        self.src_mac = struct.unpack("BBBBBB", raw_buf[6:12])
        self.eth_type = struct.unpack("!H", raw_buf[12:14])[0]
        self.size = len(raw_buf) - 14

    def _str_mac(self, mac):
        res = []
        for a in mac:
            res.append("%02x" % a)
        return ":".join(res)

    def __str__(self):
        t = self._str_mac(self.tgt_mac)
        s = self._str_mac(self.src_mac)
        return "[%04d:0x%04x,%s->%s]" % (self.size, self.eth_type, s, t)

    def is_bootp_bcast(self):
        eth_off = 14
          # check IP proto
        proto = ord(self.raw_buf[eth_off+9])
        if proto != 17:  # must be UDP
            return False
        # check tgt ip
        off = eth_off + 16  # eth hdr + ip: tgt
        tgt_ip = struct.unpack("BBBB", self.raw_buf[off:off+4])
        if tgt_ip != (255, 255, 255, 255):
            return False
        # check udp port
        udp_off = eth_off + (ord(self.raw_buf[eth_off]) & 0xf) * 4
        src_port = struct.unpack("!H", self.raw_buf[udp_off:udp_off+2])[0]
        tgt_port = struct.unpack("!H", self.raw_buf[udp_off+2:udp_off+4])[0]
        bootp = (67, 68)
        return src_port in bootp and tgt_port in bootp

    def is_for_me(self, my_mac):
        # check broadcast packets
        if self.tgt_mac == self.bcast_mac:
            if self.eth_type == 0x806:  # ARP
                return True
            elif self.eth_type == 0x800:  # IPv4
                return self.is_bootp_bcast()
            else:
                return False
        elif self.tgt_mac != my_mac:
            return False
        else:
            return True

    def is_magic_online(self):
        return self.eth_type == self.MAGIC_ONLINE

    def is_magic_offline(self):
        return self.eth_type == self.MAGIC_OFFLINE
