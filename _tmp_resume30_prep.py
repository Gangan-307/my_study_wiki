import sys, os, json
from pypdf import PdfReader
from PIL import Image

pdf, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
r = PdfReader(pdf)
pg = r.pages[0]
xo = pg["/Resources"]["/XObject"]
name = list(xo.keys())[0]
obj = xo[name].get_object()
w, h = int(obj["/Width"]), int(obj["/Height"])
im = Image.frombytes("RGB", (w, h), obj.get_data())
im.save(os.path.join(outdir, "page.png"))

SCALE = 3
big = im.resize((w * SCALE, h * SCALE), Image.LANCZOS).convert("L")
W, H = big.size
data = big.tobytes()
tbl = bytes(1 if v < 150 else 0 for v in range(256))
bw = data.translate(tbl)
ink = [bw[y * W:(y + 1) * W].count(1) for y in range(H)]

bands, y = [], 0
min_ink, gap = 4, 5
while y < H:
    if ink[y] >= min_ink:
        s = y; low = 0
        while y < H and low < gap:
            if ink[y] < min_ink:
                low += 1
            else:
                low = 0
            y += 1
        e = y - low
        if e - s > 10:
            bands.append((s, e))
    else:
        y += 1

rot = big.transpose(Image.ROTATE_90)
rdata = rot.tobytes().translate(tbl)
RW = H
rcols = [rdata[x * RW:(x + 1) * RW].count(1) for x in range(W)]
xs = [x for x, c in enumerate(rcols) if c > 0]
x0, x1 = (min(xs), max(xs)) if xs else (0, W)

meta = []
for i, (s, e) in enumerate(bands):
    c = big.crop((max(0, x0 - 8), max(0, s - 8), min(W, x1 + 8), min(H, e + 8)))
    c = c.resize((c.width, int(c.height * 1.5)), Image.BILINEAR)
    fp = os.path.join(outdir, "b_%03d.png" % i)
    c.save(fp)
    meta.append({"i": i, "y0": s, "y1": e, "file": fp})

json.dump({"image": [w, h], "dpi": round(w / (595.28 / 72), 1), "bands": meta},
          open(os.path.join(outdir, "bands.json"), "w"), ensure_ascii=False)
print("page image %dx%d px, %.1f DPI, ink cols %d-%d, bands: %d" % (w, h, w / (595.28 / 72), x0, x1, len(bands)))
