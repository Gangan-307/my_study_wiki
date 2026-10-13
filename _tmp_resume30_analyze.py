import sys, zlib
from pypdf import PdfReader

p = sys.argv[1]
r = PdfReader(p)
print("== FILE:", p)
print("pages:", len(r.pages))
print("metadata:", dict(r.metadata or {}))

pg = r.pages[0]
print("mediabox:", pg.mediabox, " rotation:", pg.get("/Rotate"))

txt = pg.extract_text() or ""
print("\n== TEXT LAYER length:", len(txt), "chars, words ~", len(txt.split()))
print(txt)

res = pg.get("/Resources") or {}
xo = res.get("/XObject") or {}
print("\n== XObjects:", len(xo))
for name, ref in xo.items():
    o = ref.get_object()
    sub = o.get("/Subtype")
    if sub == "/Image":
        w, h = o.get("/Width"), o.get("/Height")
        print(f"  {name} IMAGE {w}x{h} filter={o.get('/Filter')} cs={o.get('/ColorSpace')} bpc={o.get('/BitsPerComponent')}")
    else:
        print(f"  {name} {sub}")

fonts = res.get("/Font") or {}
print("\n== Fonts:", list(fonts.keys()))
for name, ref in fonts.items():
    o = ref.get_object()
    print(f"  {name} {o.get('/Subtype')} base={o.get('/BaseFont')} enc={o.get('/Encoding')} tounicode={'yes' if o.get('/ToUnicode') else 'no'}")

try:
    cs = pg.get_contents()
    data = cs.get_data() if cs is not None else b""
except Exception as e:
    data = b""
    print("content err", e)
print("\n== content stream bytes:", len(data))
ops = [b"Tj", b"TJ", b"Tf", b"Do", b"BT", b"ET", b"re", b"f", b"S"]
for op in ops:
    print(f"  {op.decode():3}: {data.count(op)}")
print("first 800 bytes:", data[:800])
