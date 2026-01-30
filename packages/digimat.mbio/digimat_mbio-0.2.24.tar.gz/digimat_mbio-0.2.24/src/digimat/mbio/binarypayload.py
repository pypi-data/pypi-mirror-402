import struct

class Endian:
    LITTLE = '<'
    BIG = '>'

class MyBinaryPayloadBuilder:
    def __init__(self, payload=None, byteorder=Endian.BIG, wordorder=Endian.BIG):
        self._payload = payload if payload is not None else []
        self._byteorder = byteorder
        self._wordorder = wordorder

    def to_registers(self):
        return self._payload

    def reset(self):
        self._payload = []

    def _add(self, value, fmt, num_regs):
        # Pack as BIG Endian (Standard Network Order)
        try:
            b_data = struct.pack('>' + fmt, value)
        except struct.error:
            raise

        registers = []
        # Chunk into 16-bit words (BIG Endian by default for Modbus)
        for i in range(0, len(b_data), 2):
            w = (b_data[i] << 8) | b_data[i+1]
            registers.append(w)

        # Handle Word Order (swapping registers)
        if self._wordorder == Endian.LITTLE:
            registers.reverse()

        # Handle Byte Order (swapping bytes within each register)
        if self._byteorder == Endian.LITTLE:
            registers = [((w & 0xFF) << 8) | ((w >> 8) & 0xFF) for w in registers]

        self._payload.extend(registers)

    def add_16bit_uint(self, value):
        self._add(value, 'H', 1)

    def add_16bit_int(self, value):
        self._add(value, 'h', 1)

    def add_32bit_uint(self, value):
        self._add(value, 'I', 2)

    def add_32bit_int(self, value):
        self._add(value, 'i', 2)

    def add_32bit_float(self, value):
        self._add(value, 'f', 2)

    def add_64bit_uint(self, value):
        self._add(value, 'Q', 4)

    def add_64bit_int(self, value):
        self._add(value, 'q', 4)

    def add_64bit_float(self, value):
        self._add(value, 'd', 4)

    def add_16bit_float(self, value):
        self._add(value, 'e', 1)

    def add_string(self, value):
        s = value.encode() if hasattr(value, 'encode') else value
        if len(s) % 2:
            s += b'\x00'

        registers = []
        for i in range(0, len(s), 2):
            w = (s[i] << 8) | s[i+1]
            registers.append(w)

        if self._byteorder == Endian.LITTLE:
             registers = [((w & 0xFF) << 8) | ((w >> 8) & 0xFF) for w in registers]

        self._payload.extend(registers)


class MyBinaryPayloadDecoder:
    def __init__(self, registers, byteorder=Endian.BIG, wordorder=Endian.BIG):
        self._registers = registers
        self._byteorder = byteorder
        self._wordorder = wordorder
        self._pointer = 0

    @classmethod
    def fromRegisters(cls, registers, byteorder=Endian.BIG, wordorder=Endian.BIG):
        return cls(registers, byteorder, wordorder)

    def _decode(self, fmt, num_regs):
        if self._pointer + num_regs > len(self._registers):
            return 0 # Or raise exception? Pymodbus behavior varies but often returns 0/default on underrun

        # Extract registers
        regs = self._registers[self._pointer : self._pointer + num_regs]
        self._pointer += num_regs

        # Handle Word Order
        if self._wordorder == Endian.LITTLE:
            regs = list(reversed(regs))

        # Handle Byte Order
        if self._byteorder == Endian.LITTLE:
            regs = [((w & 0xFF) << 8) | ((w >> 8) & 0xFF) for w in regs]

        # Reconstruct bytes (BIG Endian stream)
        b_data = bytearray()
        for w in regs:
            b_data.append((w >> 8) & 0xFF)
            b_data.append(w & 0xFF)

        try:
            return struct.unpack('>' + fmt, b_data)[0]
        except struct.error:
            return 0

    def decode_16bit_uint(self):
        return self._decode('H', 1)

    def decode_16bit_int(self):
        return self._decode('h', 1)

    def decode_32bit_uint(self):
        return self._decode('I', 2)

    def decode_32bit_int(self):
        return self._decode('i', 2)

    def decode_32bit_float(self):
        return self._decode('f', 2)

    def decode_64bit_uint(self):
        return self._decode('Q', 4)

    def decode_64bit_int(self):
        return self._decode('q', 4)

    def decode_64bit_float(self):
        return self._decode('d', 4)

    def decode_16bit_float(self):
        return self._decode('e', 1)

    def decode_string(self, size):
        num_regs = (size + 1) // 2

        if self._pointer + num_regs > len(self._registers):
             return b''

        regs = self._registers[self._pointer : self._pointer + num_regs]
        self._pointer += num_regs

        if self._byteorder == Endian.LITTLE:
            regs = [((w & 0xFF) << 8) | ((w >> 8) & 0xFF) for w in regs]

        b_data = bytearray()
        for w in regs:
            b_data.append((w >> 8) & 0xFF)
            b_data.append(w & 0xFF)

        return b_data[:size]

    def skip_bytes(self, nbytes):
        num_regs = (nbytes + 1) // 2
        self._pointer += num_regs
