import os

def float_range(start, stop, step):
    """ Range with float values.

    :param start: start value
    :param type: float

    :param stop: stop value
    :param type: float

    :param step: step value
    :param type: float

    :returns: generator of range values
    :rtype: generator
    """
    while start < stop:
        yield float(start)
        start += step


def reverse_readline(filename, buf_size=8192):
    """A generator that returns the lines of a file in reverse order.
    https://stackoverflow.com/questions/2301789/how-to-read-a-file-in-reverse-order
    
    :param filename: file name
    :param type: str
    
    :param buf_size: buffer size
    :param type: int
    
    :returns: generator of lines
    :rtype: generator
    """
    with open(filename, 'rb') as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size)).decode(encoding='utf-8')
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # The first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # If the previous chunk starts right from the beginning of line
                # do not concat the segment to the last line of new chunk.
                # Instead, yield the segment first 
                if buffer[-1] != '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if lines[index]:
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment