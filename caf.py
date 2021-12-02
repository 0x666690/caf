import struct


class CAF:
    def __init__(self):
        pass
        self.data: bytearray = bytearray()
        self.input_data: bytearray = None
        self.mdat_content: bytearray = None
        self.magic_cookie: bytearray = bytearray()
        self.number_of_packets: int = 0
        self.number_of_valid_frames: int = 0
        self.sample_sizes: list[int] = []
        self.sample_rate: int = 0
        self.bit_depth: int = 0
        self.old_cookie: bool = False

    def load_input_data(self, b: bytearray) -> None:
        self.input_data = b

    def load_mdat_data(self, b: bytearray) -> None:
        self.mdat_content = b

    def write_old_cookie(self, magic_cookie: bytes) -> None:
        self.old_cookie = True
        self.magic_cookie = magic_cookie

    def encode_vlq(self, values: list[int]) -> list[int]:
        encoded = []
        for value in values:
            bl = int.bit_length(value)
            length = len(encoded)
            encoded.append(value & 127)
            while bl > 7:  # value keeps going
                value >>= 7
                bl -= 7
                encoded.insert(length, (value & 127) + 128)
        return encoded

    def decode_vlq(self, values: list[int]) -> list[int]:
        decoded = []
        summed = 0
        for value in values:
            summed += value & 127
            if value >= 128:
                summed <<= 7
            else:
                decoded.append(summed)
                summed = 0
        if summed > 0 or not decoded:
            raise ValueError
        return decoded

    def bytes_to_int(self, bytes: bytearray) -> int:
        result = 0
        for b in bytes:
            result = result * 256 + int(b)
        return result

    def read_data_ahead(self, b: bytearray, position: int, offset_ahead: int) -> int:
        return self.bytes_to_int(b[position - offset_ahead : position])

    def find_box(self, b: bytes, box_name: bytes) -> list[int]:
        results: list[int] = []
        ret: int = 0
        pos: int = 0
        while ret != -1:
            ret = (b[pos:]).find(box_name)
            if ret != -1:
                results.append(pos + ret)
                size_of_box = self.read_data_ahead(b, pos + ret, 4)
                pos = pos + ret + size_of_box
        return results

    def get_atoms_of_bytes(self, b: bytes) -> list[dict]:
        atoms: list[dict] = []
        offset: int = 0
        while offset < len(b):
            size: int = self.bytes_to_int(b[offset : offset + 4])
            name: bytes = b[offset + 4 : offset + 8]
            atoms.append({"offset": offset + 4, "name": name})
            offset += size
        return atoms

    def get_box_data_by_path(self, path: str) -> bytes:
        boxes: list[str] = path.split("/")
        b = bytearray(self.input_data)
        total_offset = 0
        for box in boxes:
            all_atoms = self.get_atoms_of_bytes(b)
            for atom in all_atoms:
                if box.encode("ascii") == atom["name"]:
                    total_offset += atom["offset"]
                    size = self.read_data_ahead(b, atom["offset"], 4)
                    b = b[atom["offset"] + 4 : atom["offset"] + size + 4]
                    total_offset += 4
                    break
        return b

    def load_magic_cookie(self):
        path_to_atom = "moov/trak/mdia/minf/stbl/stsd"
        stsd_data = self.get_box_data_by_path(path_to_atom)
        # starting bytes of the ALAC magic cookie
        offset = stsd_data.find(b"\x00\x00\x00\x24\x61\x6C\x61\x63")
        self.magic_cookie = stsd_data[offset : offset + 36]

    def write(self, path):
        with open(path, "wb") as f:
            f.write(self.data)

    def create_file(self):
        # write file header
        #    write 'caff' string
        self.data += "caff".encode("ascii")
        #    write file version
        self.data += int(1).to_bytes(2, "big")
        #    write file flags
        self.data += int(0).to_bytes(2, "big")

        # write desc
        #    write 'desc' string
        self.data += "desc".encode("ascii")
        #    write 8 bytes containing 0x20 chunk size
        self.data += int(32).to_bytes(8, "big")
        #    write sample rate
        self.data += bytearray(struct.pack(">d", self.sample_rate))
        #    write format id string
        self.data += "alac".encode("ascii")
        #    write format flags
        self.data += int(0).to_bytes(4, "big")
        #    write bytes per packet
        self.data += int(0).to_bytes(4, "big")
        #    write frames per packet
        self.data += int(4096).to_bytes(4, "big")
        #    write channels per frame
        self.data += int(2).to_bytes(4, "big")
        #    write bits per channel
        self.data += int(self.bit_depth).to_bytes(4, "big")

        # write chan
        #    write 'chan' string
        self.data += "chan".encode("ascii")
        #    write 8 bytes containing 0xC chunk size
        self.data += int(12).to_bytes(8, "big")
        #    write 4 bytes for mChannelLayoutTag
        #    in our case we just want regular stereo,
        #    which is defined as 101 << 16 | 2
        self.data += int(101 << 16 | 2).to_bytes(4, "big")
        #    write 4 bytes for mChannelBitmap
        #    leaving this at 0 seems fine
        self.data += int(0).to_bytes(4, "big")
        #    write 4 bytes for mNumberChannelDescriptions
        #    0 means we get to skip the CAFChannelDescription
        self.data += int(0).to_bytes(4, "big")

        if self.write_old_cookie:
            # write kuki
            #    write 'kuki' string
            self.data += "kuki".encode("ascii")
            #    write 8 bytes containing 0x30 chunk size
            self.data += int(48).to_bytes(8, "big")
            #    write 4 bytes containing 0xC format descriptor size
            self.data += int(12).to_bytes(4, "big")
            #    write 'frma' string
            self.data += "frma".encode("ascii")
            #    write 'alac' string
            self.data += "alac".encode("ascii")
            #    write alac magic cookie, 36 bytes long,
            #    starts with 00 00 00 24 61 6C 61 63
            self.data += self.magic_cookie
        else:
            self.data += "kuki".encode("ascii")
            # size
            self.data += int(24).to_bytes(8, "big")
            self.data += int(4096).to_bytes(4, "big")
            self.data += int(0).to_bytes(1, "big")
            self.data += int(24).to_bytes(1, "big")
            self.data += int(40).to_bytes(1, "big")
            self.data += int(10).to_bytes(1, "big")
            self.data += int(14).to_bytes(1, "big")
            # number of channels
            self.data += int(2).to_bytes(1, "big")
            self.data += int(255).to_bytes(2, "big")
            self.data += int(0).to_bytes(4, "big")
            self.data += int(0).to_bytes(4, "big")
            self.data += int(self.sample_rate).to_bytes(4, "big")

        # optional:
        # write info chunk
        # contains a whole bunch of info about encoder

        # write data
        #    write 'data' string
        self.data += "data".encode("ascii")
        #    write 8 bytes containing the size of mdat and edit count
        self.data += int(len(self.mdat_content) + 4).to_bytes(8, "big")
        #    write edit count
        self.data += int(0).to_bytes(4, "big")
        #    write mdat content
        self.data += self.mdat_content

        # write pakt
        #    write 'pakt' string
        self.data += "pakt".encode("ascii")
        #    write 8 bytes containing chunk size
        encoded_value_pairs = self.encode_vlq(self.sample_sizes)
        value_pair_bytes = bytearray()
        for v in encoded_value_pairs:
            value_pair_bytes += int(v).to_bytes(1, "big")
        #    size needs to be calulated beforehand
        pakt_size = len(value_pair_bytes) + 8 + 8 + 4 + 4
        self.data += int(pakt_size).to_bytes(8, "big")
        #    write mNumberPackets
        self.data += int(self.number_of_packets).to_bytes(8, "big")
        #    write mNumberValidFrames
        self.data += int(self.number_of_valid_frames).to_bytes(8, "big")
        #    write mPrimingFrames (set to zero in ALAC)
        self.data += int(0).to_bytes(4, "big")
        #    write mRemainderFrames (also set to zero in ALAC)
        self.data += int(0).to_bytes(4, "big")
        #    create the list of value pairs
        self.data += value_pair_bytes
