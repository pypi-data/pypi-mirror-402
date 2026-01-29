# tests/test_cstr.py

import sys
sys.path.append("/data/tianzhen/my_packages/cobra-color/src")

from cobra_color import cstr
from cobra_color.string import (ColorStr, to_ansi)


def test_ColorStr():
    text = """正常文本 \x1b[1m加粗\x1b[0m 继续普通文本 \
    \x1b[4m下划线\x1b[0m \
    \x1b[31m红色前景\x1b[0m \
    \x1b[42m绿色背景\x1b[0m \
    \x1b[1;2;33;44m加粗+黄字+蓝底\x1b[0m \
    \x1b[1;38;5;200m256色前景 \
    \x1b[;38;2;255;mTrueColor红色背景\x1b[0m \
    结束文本"""

    a = ColorStr.from_str("abcd", bg="lm", styles={"bold", "udl"})
    b = cstr("abcc", bg="g", styles={"dim", "udl"})
    c = cstr(text)
    print(c)
    b.copy()
    print(a)
    print(b)
    print(to_ansi("abcc", bg="g", styles={"dim", "udl"}))
    print(a._SEGMENTS)

    print(3*a)
    print(a[1: 40])
    print(a == "abcd", a != b, a > b, a < b, a <= b, a >= b)
    b = cstr("123b4ff", fg="r", styles={"italic", "delete"})
    a += b
    a *= 2

    print(a)
    print(a._SEGMENTS)
    print(a[3:10])

    print("true", cstr("2") == "2")
    print("false", cstr("2", bg="b") == cstr("2"))
    print("false", cstr("2", bg="b") == "2")
    print("true", cstr("2", bg="b") == cstr("2", bg="b"))
    print("false", "2" == cstr("2", bg="r"))
    print("false", "2" == 1)
    print("====")
    print("true", cstr("2", bg="b") != "2")
    print("false", cstr("2") != cstr("2"))
    print("false", "2" != cstr("2"))
    print("====")
    t = a + "1b5" + a
    print(t)
    t1 = t[3: 6]
    print(t1)
    print("true", t.equal(t1, slice(3, 6)))
    print("false", t.equal(t1.plain, slice(3, 6)))
    print("false", cstr().equal(t1, slice(1, 1)))
    print("true", cstr().equal(t1[1:1], slice(1, 1)))
    print("====")
    t2 = t[22: 25]
    print(t2)
    print("true", t.equal("1b5", slice(22, 25)))
    t3 = t[3:25]
    print(t3)
    t4 = t[3:4]
    print(t4)
    print("false", t.equal(t4, slice(3, 25)))
    print("==== startswith")
    print("true", t.startswith(t1, 3))
    print("false", t.startswith(t1.plain, 3))
    print("false", cstr().startswith(t1, 1))
    print("true", cstr().startswith(t1[1:1], 1))
    print("====")
    t2 = t[22: 25]
    print(t2)
    print("false", t.startswith("1b5", 22, 24))
    t3 = t[3:25]
    print(t3)
    t4 = t[14:15]
    print(t4)
    print("true", t.startswith((t4, "123"), 14))
    print("====endswith")
    print("true", t.endswith(t1, 0, 6))
    print("false", t.endswith(t1.plain, 3))
    print("false", cstr().endswith(t1, 1))
    print("true", cstr().endswith(t1[1:1], 1))
    print("true", t.endswith((t4, "1b5"), 14, 25))

    print(a.apply("modified"*3, start_idx=3, extend="left"))
    print(a.rapply("modified"*3, start_idx=3, extend=None))
    print(a.plain)
    print(a.iscombined, a.isfgcolored, a.isbgcolored, a.isstyled, a.isplain)
    print(a.pieces())
    print(a.capitalize())
    print(a.casefold())
    print(a.lower())
    print(a.swapcase())
    print(a.title())
    print(a.upper())
    print(a.center(30, cstr("-2", bg="g")))
    print(a.ljust(30, "*", extend="right"))
    print(a.rjust(30, "+", extend="left"))
    print(a.zfill(30))
    print(a.find(cstr("b", bg="lm", styles=["bold", "udl"])))
    print(a.rfind(cstr("a", fg="y").plain))

    seg = a.pieces()[2]
    print(seg)
    seg2 = a.pieces()[3]
    print(seg2)
    f = seg2.join([seg, seg, seg])
    print("JOIN: ", f)
    print(f._SEGMENTS)

    print(a[:5].pieces()[-1])
    print(a)
    print(a._SEGMENTS)
    print("=================== SPLIT")
    print(a)

    for seg in a.split(cstr("b", fg="r", styles=["italic", "delete"])):
        print(seg, end="     ")
    print()
    print(a.plain.split("b"))
    print(a.split(cstr("b", fg="y")))
    print(a.rsplit(cstr("b", fg="y"), maxsplit=1))
    print(a.split("b"))
    print(a.splitlines(keepends=True))
    
    
    aa = ColorStr.from_str("abcd", bg="lm", styles={"bold", "udl"})
    aa += cstr("123b4ff\n", fg="r", styles={"italic", "delete"})
    aa *= 2
    ga = cstr("a", aa, 1243, sep=cstr("sep", fg="y"))
  
    for i in ga.split(cstr(1)):
        print(i, end="  ")
    print()
    print("-------------------")
    for i in ga.split("1", 2):
        print(i, end="  ")
    print()
    print("-------------------")
    
    for i in ga.rsplit("1", 2):
        print(i, end="  ")
    print()
    print("------------------- rsplit")
    for i in ga.splitlines(keepends=True):
        print(i, end="  ")
    print()
    print("------------------- splitlines")

    print(a.replace(cstr("b", bg="lm", styles=["bold", "udl"]), cstr("BB", fg="y"), count=1))

    print(a.strip("a"))
    print(a.rstrip("f"))
    print(a.removesuffix("4ff"))
    print(a.removeprefix("abcd1"))

    print("------------------- partition")
    print(a.partition(cstr("fab")))
    print(a.partition("fab"))
    print(a.rpartition("fab1"))

    print(a.splitlines())

    print(a.insert(-1, cstr("123456", fg="g"), overwrite=True))
    print(a.insert(-1, cstr("123456", fg="g")))
    print(a.insert(-1, cstr("123456", fg="g"), overwrite=True, keep_pattern=False))
    print(a.insert(-1, cstr("123456", fg="g"), keep_pattern=False))

    print(cstr("2", fg="d") in a)

    for i in a:
        print(i, end="|")
    print()
    print("fs" in a)
    

    print("====")
    a += "999"
    print("static", a)
    print(a._SEGMENTS)
    b = a.rebuild(fg=[("r", "lg"), (None, (255, 1, 92))], bg="", styles=[("del", None), (None, ["bold", "udl"])])
    print(b)
    print(b._SEGMENTS)
    print("static", a)
    c = a.rebuild(slice(4, 7), fg="y", bg="m")
    print(c)
    print(c._SEGMENTS)
    print("static", a)

    print(cstr("\u2580", fg=(42, 42, 42), bg=(31, 31, 31)))
    print(a("123"))

    print(str(121))
    f = cstr(f"()12{a}dada", fg=[("", "b")])
    print(type(f))
    print(repr(f))
    print(len(f))
    print(f)
    print(f.pieces())
    # print("\x1b[4m下划线")
    f = cstr(f, a, "<\x1b[4m下划线", 434, fg=[("", "g")])
    print(f)
    print(f._SEGMENTS)

    f._update(fg=[("b", "y")], styles={"dim"})

    print(f)
    print(f._SEGMENTS)
    f._update(bg="clear")

    print(f)
    print(f._SEGMENTS)

    g = cstr("a", a, 1243, sep=cstr("sep", fg="y"))
    print(g)
    print(g.replace(1, cstr("ONE", fg="g")))
    print(g.replace(cstr(1), cstr("ONE", fg="g")))


if __name__ == "__main__":
    test_ColorStr()
