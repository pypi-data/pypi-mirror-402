# coding: utf-8

"""
"""


class PartialReader:
    """Wrapper for multipart signed-url upload"""

    def __init__(self, fd, size):
        self._offset = fd.tell()
        self.fd = fd
        self.remaining = size
        self.original = size

    def __getattr__(self, attr):
        return getattr(self.fd, attr)

    def tell(self):
        return self.original - self.remaining

    def seek(self, offset, whence=0):
        if offset != 0 or whence != 0:
            raise ValueError("Invalid seek!")
        self.fd.seek(self._offset)
        self.remaining = self.original

    def __len__(self):
        return self.remaining

    def read(self, n=-1):
        if self.remaining == 0:
            # signaling end
            return b""

        if self.remaining < n or n < 0:
            # last acutal chunk
            res = self.fd.read(self.remaining)
            self.remaining = 0
            return res

        self.remaining -= n
        return self.fd.read(n)
