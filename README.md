# scQOI2 compressor
scQOI2 is the successor to the previous scQOI compression algorithm, that applies a semi-sliding dictionary with Opcode RLE

```
SCQ2_OP_RUN (Code 00) - Declares a run of repeated symbols
SCQ2_OP_DIFF (Code 01) - Declares a difference between the last byte the byte succeeding it
SCQ2_OP_REF (Code 10) - Declares a repeat of a previous BYTES stream
SCQ2_OP_BYTES (Code 11) - Declares a stream of bytes (max: 64B)
```
