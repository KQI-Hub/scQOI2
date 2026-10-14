import scqoi2, sys

fn = sys.argv[1]
fn_o = sys.argv[2]

do_diff = True
if "--no_diff" in sys.argv[3:]:
    do_diff = False

if fn.endswith(".scq2"):
    file = open(fn, "rb").read()
    open(fn_o, "wb").write(scqoi2.decompress(file))
else:
    file = open(fn, 'rb').read()
    open(fn_o, "wb").write(scqoi2.compress(file, do_diff=do_diff))