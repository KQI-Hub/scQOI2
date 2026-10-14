# scQOI2 - Simple compression algorithm
# scQOI2 uses simple, low complexity backreferences and differential RLE

def emit_buffer(data: bytes):
    r = bytes([192+len(data)-1])
    return r+data

"""
Sample encoder that makes a minimum viable scQOI2 file

def compress(data: bytes):
    bytes_table = [bytearray([32]), bytearray([0])]*32 # initialize to ascii space and null, which I think are useful
    compressed_data = bytearray()
    byte_buffer = bytearray()

    seek = 0
    while seek < len(data):
        b = data[seek]
        byte_buffer.append(b)

        if len(byte_buffer) == 64:
            bytes_table.append(byte_buffer)
            bytes_table = bytes_table[1:] # drop first entry
            compressed_data.extend(emit_buffer(byte_buffer))
            byte_buffer = bytearray()

        seek+=1

    if byte_buffer:
        compressed_data.extend(emit_buffer(byte_buffer)) # flush

    print(bytes_table)
    return compressed_data
"""

"""
Sample encoder that does sequence matching

def compress(data: bytes):
    bytes_table = [bytearray([32]), bytearray([0])]*32 # initialize to ascii space and null, which I think are useful
    table_item_lengths = [1]*64 # initialize to 1

    compressed_data = bytearray()
    byte_buffer = bytearray()

    seek = 0
    while seek < len(data):
        found_match = False
        b = data[seek]

        print(bytes_table)
        print(data[seek:seek+3])
        for length in reversed(sorted(set(table_item_lengths))):
            if data[seek:seek+length] in bytes_table[1:]: # ignore oldest entry, it gets killed :3
                found_match = True

                if byte_buffer: # generic flushing thing
                    byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

                compressed_data.append(128+63-bytes_table.index(data[seek:seek+length]))
                seek+=length-1 # advance pointer
                break

        if not found_match: # append byte to literal thing
            byte_buffer.append(b)
            if len(byte_buffer) == 64:
                byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

        seek+=1

    if byte_buffer:
        compressed_data.extend(emit_buffer(byte_buffer)) # flush

    print(bytes_table)
    return compressed_data
"""

def flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths):
    if not bytes(byte_buffer) in bytes_table: # avoid duplicating table entries
        bytes_table.append(bytes(byte_buffer))
        table_item_lengths.append(len(byte_buffer))
        del bytes_table[0] # drop first entry
        del table_item_lengths[0]
        table_item_lengths
    compressed_data.extend(emit_buffer(byte_buffer))
    return bytearray()

def compress(data: bytes, do_diff: bool = True): # diff usually reduces size but it makes encoding slower
    bytes_table = [bytearray([32]), bytearray([0])]*32 # initialize to ascii space and null, which I think are useful
    table_item_lengths = [1]*64 # initialize to 1

    compressed_data = bytearray()
    byte_buffer = bytearray()

    seek = 0
    prevbyte = None
    prev_output = None
    op_run = 0

    while seek < len(data):
        curr_output = None
        found_match = False
        b = data[seek]

        possible_search = sorted(set(table_item_lengths+[len(byte_buffer)]), reverse=True) if byte_buffer else reversed(sorted(set(table_item_lengths), reverse=True))

        for length in possible_search: # SCQ2_OP_REF
            if bytes(byte_buffer) == data[seek:seek+length]:
                byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

            search_window = bytes_table[1:] if byte_buffer else bytes_table # ignore oldest entry, if the buffer will be flushed

            if data[seek:seek+length] in search_window:
                found_match = True
                chunk = data[seek:seek+length]

                if byte_buffer: # generic flushing thing
                    byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

                curr_output = 128+63-bytes_table.index(chunk)
                compressed_data.append(curr_output)

                seek += len(chunk) - 1 # advance pointer
                break

        if do_diff and not found_match and prevbyte is not None: # SCQ2_OP_DIFF
            diff = (b - prevbyte) % 256 # pulling code from scQOI1
            if diff > 127:
                diff -= 256
            if (diff <= 31) and (diff >= -32):
                if byte_buffer: # generic flushing thing
                    byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

                if diff < 0:
                    diff+=64
                curr_output = 64+diff
                compressed_data.append(curr_output)
                found_match = True

        if not found_match: # SCQ2_OP_BYTES - append byte to literal thing
            byte_buffer.append(b)
            if len(byte_buffer) == 64:
                curr_output = None
                byte_buffer = flush_to_table(byte_buffer, bytes_table, compressed_data, table_item_lengths)

        if curr_output is not None and curr_output == prev_output and op_run < 64:
            del compressed_data[-1]            # repeat: never keep it
            op_run += 1
        elif op_run:
            if curr_output is not None:        # a new op was just written, put RUN before it
                compressed_data.insert(len(compressed_data)-1, op_run-1)
            else:                              # literal buffered, nothing written
                compressed_data.append(op_run-1)
            op_run = 0

        prev_output = curr_output


        seek+=1
        prevbyte = data[seek-1]

    if op_run:
        compressed_data.append(op_run-1)

    if byte_buffer:
        compressed_data.extend(emit_buffer(byte_buffer)) # flush

    return compressed_data

def decompress(data: bytes):
    bytes_table = [bytearray([32]), bytearray([0])]*32 # initialize to ascii space and null, which I think are useful

    decompressed_data = bytearray()
    byte_buffer = None
    prevbyte = None
    prev_op = None

    seek = 0
    while seek < len(data):
        b = data[seek]
        dtype = b>>6 # extract bittype
        pload = b%64 # extract payload value

        if dtype == 3: # SCQ2_OP_BYTES
            offset = seek+1
            assert len(data) >= offset+pload+1, "Truncated Byte End!"
            byte_buffer = data[offset:offset+pload+1]

            decompressed_data.extend(byte_buffer)

            if byte_buffer not in bytes_table:
                bytes_table.append(byte_buffer)
                bytes_table = bytes_table[1:] # drop first entry
            seek+=pload+1

        elif dtype == 2: # SCQ2_OP_REF
            e = bytes_table[63-pload]
            prev_op = [dtype, e]
            decompressed_data.extend(e)

        elif dtype == 1: # SCQ2_OP_DIFF
            assert seek != 0, "SCQ2_OP_DIFF before any decoded data!"
            if pload > 31:
                pload -= 64
            bt = (decompressed_data[-1]+pload) % 256

            prev_op = [dtype, pload]
            decompressed_data.append(bt)

        elif dtype == 0: # SCQ2_OP_RUN
            assert prev_op is not None, "SCQ2_OP_RUN before without an eligable previous OP!"
            for _ in range(pload+1):
                if prev_op[0] == 2:
                    decompressed_data.extend(prev_op[1])
                elif prev_op[0] == 1:
                    decompressed_data.append((decompressed_data[-1]+prev_op[1])%256)

        seek+=1

    return decompressed_data
