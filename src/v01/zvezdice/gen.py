#!/usr/bin/env python3
# Generator testov za nalogo zvezdice.
# Ustvari testi/test01.in ... testi/test50.in in pričakovane izhode *.out ter
# vanjo skopira splošni Makefile (orodja/Makefile.testi) in checker.awk, zato je
# mapa testi/ samostojna: make test name=<resitev>
# (mapa testi/ ni v gitu - vedno jo ustvariš znova s tem skriptom).
#
#   01-10: majhni testi za ročno preverjanje (primera iz naloge, robni primeri)
#   11-40: naraščajoča velikost, n od ~10 do ~400 (prehajajo tudi rešitve O(n^3))
#   41-45: n ~ 3000, n*w <= 2*10^7: rešitve O(n^3) presežejo časovno omejitev,
#          O(n^2) oz. O(n*w) (DP, požrešna brez kopic) še prehajajo
#   46-50: tik pod omejitvami naloge (n do 3*10^5): prehajajo le rešitve
#          O(n log n) oz. O((n+w) log n)
#
# Pričakovane izhode izračuna požrešna rešitev s kopicami
# (zvezdice_ai_pozresno.cpp); cena se preveri še z neodvisno rešitvijo
# z razcepom (zvezdice_ai_razcep.cpp), pri manjših testih tudi z DP
# (zvezdice_ai_dp.cpp), razporeditev pa s checker.awk.
#
# Uporaba: python3 gen.py      (seme je fiksno, vsakič nastanejo enaki testi)
import glob, os, random, shutil, subprocess, tempfile

MAPA = os.path.dirname(os.path.abspath(__file__))
TESTI = os.path.join(MAPA, "testi")
CHECKER = os.path.join(MAPA, "checker.awk")
MAKEFILE = os.path.join(MAPA, "..", "..", "..", "orodja", "Makefile.testi")
MAX_N, MAX_V = 3 * 10**5, 10**9
random.seed(2026)

def naklj(n, w, hi, razlika=None):
    """n ugank z a v [1, hi] in b = a + razlika (oz. naključno do 2*hi)."""
    vr = []
    for _ in range(n):
        a = random.randint(1, hi)
        vr.append((a, a + (razlika or random.randint(1, hi))))
    return n, w, vr

testi = []

# 01-10: majhni testi
testi.append((5, 3, [(10, 20), (25, 30), (6, 9), (5, 10), (10, 20)]))     # primer 1
testi.append((10, 4, [(5, 7), (1, 26), (26, 29), (12, 25), (3, 6),         # primer 2
                      (7, 21), (16, 25), (17, 24), (16, 25), (15, 23)]))
testi.append((1, 1, [(3, 5)]))                                             # n = 1
testi.append((1, 2, [(3, 5)]))                                             # n = 1, w = 2n
testi.append(naklj(6, 12, 20))                                             # w = 2n: vse na 2
testi.append(naklj(8, 1, 20))                                              # w = 1
testi.append((6, 5, [(4, 6)] * 6))                                         # vse uganke enake
testi.append(naklj(8, 7, 10, razlika=1))                                   # b = a + 1
testi.append(naklj(8, 9, 10, razlika=100))                                 # b >> a
testi.append(naklj(10, 19, MAX_V - 10, razlika=1))                         # vsota ne gre v int

# 11-40: naraščajoča velikost (geometrijsko od 10 do 400)
for k in range(30):
    n = round(10 * 40 ** (k / 29))
    w = random.randint(1, 2 * n)
    testi.append(naklj(n, w, random.choice([5, 1000, MAX_V // 2])))

# 41-45: prepočasno za O(n^3), dovolj hitro za O(n*w)
for _ in range(5):
    n = random.randint(2800, 3200)
    w = random.randint(n, min(2 * n, 2 * 10**7 // n))
    testi.append(naklj(n, w, random.choice([1000, MAX_V // 2])))

# 46-50: tik pod omejitvami, zadnji je največji možen
for _ in range(4):
    n = random.randint(250000, MAX_N)
    w = random.randint(n // 2, 2 * n)
    testi.append(naklj(n, w, random.choice([1000, MAX_V // 2])))
testi.append(naklj(MAX_N, 2 * MAX_N - 1, MAX_V // 2))

assert len(testi) == 50
for n, w, vr in testi:
    assert len(vr) == n and 1 <= n <= MAX_N and 1 <= w <= 2 * n
    assert all(1 <= a < b <= MAX_V for a, b in vr)

def prevedi(ime, tmp):
    exe = os.path.join(tmp, ime)
    subprocess.run(["g++", "-O2", "-std=c++20", "-o", exe,
                    os.path.join(MAPA, f"zvezdice_ai_{ime}.cpp")], check=True)
    return exe

def pozeni(exe, vhod):
    return subprocess.run([exe], input=vhod, capture_output=True, text=True, check=True).stdout

os.makedirs(TESTI, exist_ok=True)
for f in glob.glob(os.path.join(TESTI, "*.in")) + glob.glob(os.path.join(TESTI, "*.out")):
    os.remove(f)
shutil.copy(MAKEFILE, os.path.join(TESTI, "Makefile"))
shutil.copy(CHECKER, TESTI)

with tempfile.TemporaryDirectory() as tmp:
    pozresno, razcep, dp = prevedi("pozresno", tmp), prevedi("razcep", tmp), prevedi("dp", tmp)
    for k, (n, w, vr) in enumerate(testi, 1):
        vhod = f"{n} {w}\n" + "".join(f"{a} {b}\n" for a, b in vr)
        ime = os.path.join(TESTI, f"test{k:02d}")
        izhod = pozeni(pozresno, vhod)
        cena = izhod.split()[0]
        assert cena == pozeni(razcep, vhod).split()[0], f"razcep se ne ujema pri {k:02d}"
        if n * w <= 2 * 10**7:
            assert cena == pozeni(dp, vhod).split()[0], f"DP se ne ujema pri {k:02d}"
        with open(ime + ".in", "w") as f:
            f.write(vhod)
        with open(ime + ".out", "w") as f:
            f.write(izhod)
        subprocess.run(["awk", "-f", CHECKER, ime + ".in", ime + ".out", ime + ".out"], check=True)

print(f"Ustvarjenih {len(testi)} testov v {TESTI}")
