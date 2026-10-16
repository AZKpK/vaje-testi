#!/usr/bin/env python3
# Splošen generator testov. Gen.py posamezne naloge opiše le vhode, ta modul pa
# izračuna pričakovane izhode s pravilno rešitvijo, jih (neobvezno) preveri z
# drugimi rešitvami ali checkerjem, ustvari testi/test01.in, test01.out, ... in
# vanjo skopira Makefile.testi (in checker), zato je mapa samostojna:
#     cd testi && make test name=<resitev>
#
# Primer gen.py naloge (poti so relativne na mapo, v kateri je gen.py):
#
#     import os, sys
#     sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "orodja"))
#     from gen import generiraj, iz_datoteke
#
#     def nakljucni(n):
#         # r je random.Random s fiksnim semenom za ta test
#         return lambda r: [(n,), [r.randint(1, 10**9) for _ in range(n)]]
#
#     testi = [iz_datoteke("primer.in"), "1\n5\n"]
#     testi += [nakljucni(10 * k) for k in range(1, 41)]
#
#     generiraj(testi, resitev="naloga_ai.cpp",
#               preveri=["naloga.cpp", ("naloga_brute.py", range(1, 21))])
#
# Test je lahko:
#   - niz: dobesedni vhod,
#   - funkcija f(r), ki vrne vhod; r je random.Random s semenom, ki je odvisno
#     le od številke testa, zato so testi vedno enaki (tudi pri vzporednem
#     generiranju in če vmes dodaš ali spremeniš kak drug test).
# Vhod je niz ali seznam vrstic; vrstica je seznam/terka (elementi se ločijo s
# presledki) ali posamezna vrednost. Enako velja za izhod rešitve-funkcije.
#
# Rešitev (resitev in elementi preveri) je .cpp (prevede se z g++ -O2), .py,
# drug izvedljiv program ali Pythonova funkcija f(vhod: str) -> izhod.
# Elementi preveri so rešitev ali (rešitev, številke testov), npr. počasna
# rešitev samo na majhnih testih. Brez checkerja morata biti izhoda enaka
# (presledki na koncu vrstic in prazne vrstice na koncu se ne upoštevajo).
#
# Uporaba gen.py naloge:  python3 gen.py [-j PROCESOV] [-t 3-7]
import argparse, concurrent.futures, glob, multiprocessing, os, random, shutil, \
    subprocess, sys, tempfile, time

ORODJA = os.path.dirname(os.path.abspath(__file__))
MAKEFILE = os.path.join(ORODJA, "Makefile.testi")

# ---------------------------------------------------------------- za gen.py nalog

def iz_datoteke(pot):
    """Test, katerega vhod je obstoječa datoteka (npr. primer iz naloge)."""
    pot = os.path.join(_mapa_naloge(), pot)
    return lambda r: open(pot).read()

def besedilo(vhod):
    """Vhod/izhod (niz ali seznam vrstic) kot besedilo z \\n na koncu."""
    if isinstance(vhod, str):
        return vhod if vhod.endswith("\n") or not vhod else vhod + "\n"
    vrstice = []
    for v in vhod:
        vrstice.append(" ".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v))
    return "".join(v + "\n" for v in vrstice)

# ---------------------------------------------------------------- notranje

def _mapa_naloge():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def _ime(r):
    return r.__name__ if callable(r) else os.path.basename(r)

def _prevedi(r, tmp):
    """Rešitev -> funkcija ali ukaz (seznam) za subprocess."""
    if callable(r):
        return r
    pot = os.path.join(_mapa_naloge(), r)
    if not os.path.exists(pot):
        sys.exit(f"Ni rešitve {pot}")
    if pot.endswith(".cpp"):
        exe = os.path.join(tmp, os.path.basename(pot)[:-4])
        print(f"Prevajam {r} ...")
        subprocess.run(["g++", "-O2", "-std=c++20", "-o", exe, pot, "-lm"], check=True)
        return [exe]
    if pot.endswith(".py"):
        return [sys.executable, pot]
    return [pot]

def _pozeni(prog, vhod, ime):
    if callable(prog):
        return besedilo(prog(vhod))
    p = subprocess.run(prog, input=vhod, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{ime} se je končal s kodo {p.returncode}:\n{p.stderr[-2000:]}")
    return p.stdout

def _normaliziraj(s):
    vrstice = [v.rstrip() for v in s.split("\n")]
    while vrstice and not vrstice[-1]:
        vrstice.pop()
    return vrstice

def _checker(checker, vhod, out, res, tmp, k):
    """Požene awk -f checker vhod out res; vrne None (OK) ali izpis checkerja."""
    datoteke = []
    for ime, vsebina in (("in", vhod), ("out", out), ("res", res)):
        datoteke.append(os.path.join(tmp, f"chk{k}.{ime}"))
        with open(datoteke[-1], "w") as f:
            f.write(vsebina)
    p = subprocess.run(["awk", "-f", checker] + datoteke, capture_output=True, text=True)
    for d in datoteke:
        os.remove(d)
    return None if p.returncode == 0 else (p.stdout + p.stderr).strip() or "napačno"

# Nastavi generiraj() pred zagonom procesov (ti jih podedujejo s fork, zato so
# testi lahko tudi lambde, ki jih pickle ne zna prenesti).
_N = {}

def _naredi_test(k):
    n = _N
    test = n["testi"][k - 1]
    vhod = besedilo(test(random.Random(n["seme"] * 1000 + k)) if callable(test) else test)
    if n["veljaven"]:
        try:
            n["veljaven"](vhod)
        except AssertionError as e:
            raise AssertionError(f"test{k:0{n['sirina']}d}: neveljaven vhod {e}") from None
    zacetek = time.perf_counter()
    izhod = _pozeni(n["resitev"], vhod, n["ime_resitve"])
    cas = time.perf_counter() - zacetek

    napake = []
    if n["checker"]:
        if (msg := _checker(n["checker"], vhod, izhod, izhod, n["tmp"], k)):
            napake.append(f"checker zavrne izhod {n['ime_resitve']}: {msg}")
    for prog, ime, kateri in n["preveri"]:
        if kateri is not None and k not in kateri:
            continue
        res = _pozeni(prog, vhod, ime)
        if n["checker"]:
            if (msg := _checker(n["checker"], vhod, izhod, res, n["tmp"], k)):
                napake.append(f"{ime}: {msg}")
        elif _normaliziraj(res) != _normaliziraj(izhod):
            napake.append(f"{ime} se ne ujema z {n['ime_resitve']}")

    ime = os.path.join(n["mapa"], f"test{k:0{n['sirina']}d}")
    with open(ime + ".in", "w") as f:
        f.write(vhod)
    with open(ime + ".out", "w") as f:
        f.write(izhod)
    return k, len(vhod), cas, napake

def _obseg(s, n):
    od, _, do = s.partition("-") if "-" in s else (s, "", s)
    return range(int(od or 1), int(do or n) + 1)

def generiraj(testi, resitev, preveri=(), checker=None, veljaven=None,
              mapa="testi", seme=2026):
    """Ustvari teste v mapi `mapa` (relativno na gen.py naloge).

    testi     seznam testov (niz ali funkcija f(r) -> vhod)
    resitev   pravilna rešitev, ki izračuna .out
    preveri   dodatne rešitve, ki se morajo ujemati: rešitev ali (rešitev, številke testov)
    checker   pot do checker.awk (naloge z več pravilnimi odgovori); skopira se v mapo
    veljaven  funkcija f(vhod: str), ki z assert preveri omejitve naloge
    """
    p = argparse.ArgumentParser(description="Generator testov.")
    p.add_argument("-j", type=int, default=os.cpu_count(), help="število procesov")
    p.add_argument("-t", default="-", help="samo ti testi, npr. 3-7 ali 12 (drugi ostanejo)")
    args = p.parse_args()

    naloga = _mapa_naloge()
    mapa = os.path.join(naloga, mapa)
    sirina = max(2, len(str(len(testi))))
    izbrani = [k for k in _obseg(args.t, len(testi)) if 1 <= k <= len(testi)]

    os.makedirs(mapa, exist_ok=True)
    if args.t == "-":
        for f in glob.glob(os.path.join(mapa, "test*.in")) + glob.glob(os.path.join(mapa, "test*.out")):
            os.remove(f)
    shutil.copy(MAKEFILE, os.path.join(mapa, "Makefile"))
    if checker:
        checker = os.path.join(naloga, checker)
        shutil.copy(checker, os.path.join(mapa, "checker.awk"))

    with tempfile.TemporaryDirectory() as tmp:
        prevedene = {}
        def prevedi(r):
            kljuc = r if callable(r) else os.path.normpath(r)
            if kljuc not in prevedene:
                prevedene[kljuc] = _prevedi(r, tmp)
            return prevedene[kljuc]

        _N.update(testi=testi, seme=seme, sirina=sirina, mapa=mapa, tmp=tmp,
                  checker=checker, veljaven=veljaven,
                  resitev=prevedi(resitev), ime_resitve=_ime(resitev), preveri=[])
        for r in preveri:
            r, kateri = r if isinstance(r, tuple) else (r, None)
            _N["preveri"].append((prevedi(r), _ime(r), kateri))

        print(f"Generiram {len(izbrani)} testov ({args.j} procesov) ...")
        rezultati, napake = [], 0
        ctx = multiprocessing.get_context("fork")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.j, mp_context=ctx) as pool:
            for k, velikost, cas, nap in pool.map(_naredi_test, izbrani):
                rezultati.append((k, cas))
                oznaka = "" if not nap else "  NAPAKA"
                print(f"  test{k:0{sirina}d}  {velikost / 1024:9.1f} KB  {cas:6.2f} s{oznaka}")
                for x in nap:
                    print(f"      {x}")
                napake += bool(nap)

    k, cas = max(rezultati, key=lambda x: x[1])
    print(f"Ustvarjenih {len(rezultati)} testov v {mapa} "
          f"(najpočasnejši test{k:0{sirina}d}: {cas:.2f} s)")
    if napake:
        sys.exit(f"Neujemanje pri {napake} testih!")
