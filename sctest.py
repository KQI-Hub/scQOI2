import scqoi2

fn = "slinx92_and_dtpls_-_electrical_whisk.xm"
thisfile = open(fn, 'rb').read()

open(f'nodiff_{fn}.scq2', "wb").write(scqoi2.compress(thisfile, do_diff=False))

newfile = open(f'nodiff_{fn}.scq2', """rb""").read()

open(f'decompressed_nodiff_{fn}', "wb").write(scqoi2.decompress(newfile))
