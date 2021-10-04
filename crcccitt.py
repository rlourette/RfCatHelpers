# // ****************************************************************************
# /// Calculates the 16bit CRC on the given byte stream using
# ///
# /// 	f(x) = x^16 + x^12 + x^5 + 1
# ///
# /// This function is designed to be called piecemeal, with the previously
# /// calculated CRC being injected as the preLoad value.  Because this algorithm
# /// XORs and bit reverses the output, we assume the preload value needs to be
# /// XORd and reversed.  This requires that the initial preload value for the
# /// algorithm (typically 0xFFFF) be pre-inverted to 0x00000000.
# ///
# /// @param data		Buffer to perform CRC on
# /// @param length   Length of data to CRC
# /// @param preLoad  Preload value for CRC
# /// @param end		Last CRC in stream or not
# /// @return			Calculated CRC value
# // ****************************************************************************
class CRCCCITT:

    @staticmethod
    def CalculateCrc16(data: bytes, crc):
        for i in range(len(data)):
            b = data[i]
            crc = ((0xff & (crc >> 8)) | (crc << 8)) & 0xffff
            crc ^= b
            crc ^= (crc & 0xff) >> 4
            crc ^= (crc << 12) & 0xffff
            crc ^= ((crc & 0xff) << 5) & 0xffff
        return crc

    @staticmethod
    def test():
        testData = bytes('123456789', 'UTF8')
        expected = 0x29B1
        crc = CRCCCITT.CalculateCrc16(testData, 0xffff)
        assert crc == expected


if __name__ == "__main__":
    CRCCCITT.test()
    print("Passed")
