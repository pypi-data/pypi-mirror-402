# tests/test_cstr.py

import sys
sys.path.append("/data/tianzhen/my_packages/cobra-color/src")

import copy
from cobra_color.string import ColorSeg


def test_ColorSeg():
    a = ColorSeg.from_raw("123", fg="lb", bg="g", styles=["bold", "udl", "italic"])
    b = ColorSeg.from_raw("45", fg=(255, 0, 0), styles=["italic", "delete"])
    c = ColorSeg(a.plain, a.fg, a.bg, a.styles)
    d = ColorSeg.empty()
    e = a.copy()
    e = copy.deepcopy(a)
    f = ColorSeg.from_raw("1")
    g = a(1)
    h = a(1)

    print(len(a))
    print("true", a.equal(c))
    print("false", a.equal(c, slice(2, 5)))
    print("false", a != c)
    print("true", a == c)

    print("false", a.equal(f, slice(0, 1)))
    print("false", a.equal(g, slice(0, 2)))
    print("true", a.equal(g, slice(0, 1)))

    print(a.assemble("fg", "styles"))
    print("===")
    print(a.to_ansi())
    print(a("222222222222").to_ansi())
    print(a.istart, a.iend, a.isfgcolored, a.isbgcolored, a.isstyled, a.isplain)
    print(a.plain, a.fg, a.bg, a.styles)

    f = a % ("modified", "lr", "m", ["bold", "italic"], 100)

    print(repr(a))
    print(a.to_ansi())
    print(f)
    print(f.to_ansi())

    print("====")

    f = f % {"+plain": "123", "+fg": "ly", "@fg": ("lr", "m"), "@bg": "44", "-bg": "m", "-styles": ["bold"], "+styles": ["dim"], "@styles": ["dim", "blink"]}
    print(f)
    print(f.to_ansi())
    f._update_plain("modified again", mode="=")
    f._update(fg="y", bg="m", styles=[({"bold"}, {"udl"})])
    print(f)

    print(f.to_subseg(slice(105, 110), real_index=True))
    print(f.to_subseg(slice(111)))


if __name__ == "__main__":
    test_ColorSeg()
