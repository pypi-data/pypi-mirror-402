from PIL import Image
import sys
in_fn = sys.argv[1]
out_fn = sys.argv[2]
img = Image.open(in_fn)
img.save(out_fn, format="PNG")



