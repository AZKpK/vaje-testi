#!/usr/bin/env python3
# Generator testov za nalogo zlivanje (naravno K-smerno zlivanje).
# Ustvari testi/test01.in ... testi/test50.in in pričakovane izhode *.out ter
# vanjo skopira splošni Makefile (orodja/Makefile.testi), zato je mapa testi/
# samostojna: make test name=<resitev>
# (mapa testi/ ni v gitu - vedno jo ustvariš znova s tem skriptom).
#
#   01-10: majhni testi za ročno preverjanje (primer iz naloge, robni primeri)
#   11-40: naraščajoča velikost, N od 10 do ~5000 (prehajajo tudi rešitve O(N^2))
#   41-45: N ~ 10^5: rešitve O(N^2) presežejo časovno omejitev
#   46-50: tik pod omejitvami naloge (N do 10^6)
#
# A je večinoma izbran tako, da zaporedje po A korakih še ni urejeno (sicer bi
# bil izhod kar sort), v nekaterih testih pa je dovolj velik, da se zlivanje
# konča prej (preverja ustavljanje).
#
# Pričakovane izhode izračuna zlivanje_ai.cpp. Preverijo se z neodvisno
# rešitvijo v Pythonu, ki po A korakih uredi vsak blok K^A originalnih čet,
# pri manjših testih pa še z dobesedno simulacijo (čete išče v vsakem koraku).
#
# Uporaba: python3 gen.py      (seme je fiksno, vsakič nastanejo enaki testi)
import glob, os, random, shutil, subprocess, tempfile

MAPA = os.path.dirname(os.path.abspath(__file__))
TESTI = os.path.join(MAPA, "testi")
MAKEFILE = os.path.join(MAPA, "..", "..", "..", "orodja", "Makefile.testi")
MAX_N, MAX_K, MAX_A, MAX_V = 10**6, 10, 20, 10**9
random.seed(2026)

def stevilo_cet(t):
    return 1 + sum(t[i-1] > t[i] for i in range(1, len(t)))

def potrebnih_korakov(t, K):
    """Koliko korakov zlivanja je potrebnih, da je zaporedje urejeno."""
    R, koraki = stevilo_cet(t), 0
    while R > 1:
        R, koraki = (R + K - 1) // K, koraki + 1
    return koraki

def naklj(n, hi):
    return [random.randint(0, hi) for _ in range(n)]

def cete(n, povp, hi):
    """Zaporedje iz urejenih čet z dolžino okrog povp."""
    t = []
    while len(t) < n:
        t += sorted(naklj(min(random.randint(1, 2 * povp), n - len(t)), hi))
    return t

def skoraj_urejeno(n, zamenjav, hi):
    t = sorted(naklj(n, hi))
    for _ in range(zamenjav):
        i, j = random.randrange(n), random.randrange(n)
        t[i], t[j] = t[j], t[i]
    return t

def test(t, K, A=None):
    """A = None: naključen A, pri katerem zaporedje še ni urejeno (če se da)."""
    if A is None:
        A = random.randint(1, max(1, potrebnih_korakov(t, K) - 1))
    return len(t), K, A, t

def nakljucni(n):
    hi = random.choice([5, 100, MAX_V])
    t = random.choice([lambda: naklj(n, hi),
                       lambda: cete(n, random.choice([3, 10, 50]), hi),
                       lambda: skoraj_urejeno(n, max(1, n // 20), hi)])()
    return test(t, random.randint(2, MAX_K))

testi = []

# 01-10: majhni testi
testi.append(test([13, 18, 7, 8, 17, 3, 16, 9, 10, 11, 11, 0, 2, 19, 14, 5, 6, 15,
                   4, 5, 12, 3, 18, 1, 3], 3, 2))                          # primer iz naloge
testi.append(test([42], 2, 1))                                             # N = 1
testi.append(test(list(range(10)), 3, 5))                                 # že urejeno
testi.append(test([5, 5, 5, 5, 5, 5], 2, 3))                               # vsi enaki (ena četa)
testi.append(test(list(range(12, 0, -1)), 2, 2))                           # padajoče: N čet
testi.append(test(list(range(12, 0, -1)), 2, 20))                          # A večji od potrebnega
testi.append(test([3, 1, 2, 1, 2, 0, 1, 1, 2, 0, 0, 3], 10, 1))            # K > število čet
testi.append(test([4, 2, 2, 7, 1, 1, 3, 0, 5, 5, 2, 6, 3, 3], 2, 1))       # enaki elementi na mejah
testi.append(test(cete(20, 3, 9), 4, 1))                                   # A = 1
testi.append(test([MAX_V, 0, MAX_V, MAX_V - 1, 0, MAX_V, 1], 2, 2))        # vrednosti do 10^9

# 11-40: naraščajoča velikost (geometrijsko od 10 do 5000)
for k in range(30):
    testi.append(nakljucni(round(10 * 500 ** (k / 29))))

# 41-45: prepočasno za O(N^2)
for _ in range(5):
    testi.append(nakljucni(random.randint(80000, 120000)))

# 46-50: tik pod omejitvami, zadnji je največji možen
testi.append(test(naklj(MAX_N, MAX_V), MAX_K))                              # K = 10
testi.append(test(cete(MAX_N, 5, MAX_V), 3))                                # daljše čete
testi.append(test(list(range(MAX_N, 0, -1)), 2, MAX_A))                     # N čet, vseh 20 korakov
testi.append(test(naklj(MAX_N, 100), 2))                                    # veliko enakih
t = naklj(MAX_N, MAX_V)
testi.append(test(t, 2, potrebnih_korakov(t, 2) - 1))                       # največ korakov, še ni urejeno

assert len(testi) == 50
for N, K, A, t in testi:
    assert len(t) == N and 1 <= N <= MAX_N and 2 <= K <= MAX_K and 1 <= A <= MAX_A
    assert all(0 <= x <= MAX_V for x in t)

def bloki(t, K, A):
    """Neodvisna rešitev: po A korakih je urejen vsak blok K^A originalnih čet."""
    meje = [0] + [i for i in range(1, len(t)) if t[i-1] > t[i]] + [len(t)]
    R = len(meje) - 1
    blok = min(K ** A, R)
    izhod = []
    for g in range(0, R, blok):
        izhod += sorted(t[meje[g]:meje[min(g + blok, R)]])
    return izhod

def simulacija(t, K, A):
    """Dobesedna simulacija: v vsakem koraku znova poišče čete in jih zlije po K."""
    for _ in range(A):
        meje = [0] + [i for i in range(1, len(t)) if t[i-1] > t[i]] + [len(t)]
        if len(meje) == 2:
            break
        nov = []
        for g in range(0, len(meje) - 1, K):
            cete_skupine = [t[meje[j]:meje[j+1]] for j in range(g, min(g + K, len(meje) - 1))]
            while any(cete_skupine):
                m = min((c for c in cete_skupine if c), key=lambda c: c[0])
                nov.append(m.pop(0))
        t = nov
    return t

def pozeni(exe, vhod):
    return subprocess.run([exe], input=vhod, capture_output=True, text=True, check=True).stdout

os.makedirs(TESTI, exist_ok=True)
for f in glob.glob(os.path.join(TESTI, "*.in")) + glob.glob(os.path.join(TESTI, "*.out")):
    os.remove(f)
shutil.copy(MAKEFILE, os.path.join(TESTI, "Makefile"))

with tempfile.TemporaryDirectory() as tmp:
    exe = os.path.join(tmp, "zlivanje_ai")
    subprocess.run(["g++", "-O2", "-std=c++17", "-o", exe,
                    os.path.join(MAPA, "zlivanje_ai.cpp")], check=True)
    for k, (N, K, A, t) in enumerate(testi, 1):
        vhod = f"{N} {K} {A}\n" + "".join(f"{x}\n" for x in t)
        izhod = pozeni(exe, vhod)
        rezultat = list(map(int, izhod.split()))
        assert rezultat == bloki(t, K, A), f"bloki se ne ujemajo pri {k:02d}"
        if N <= 5000:
            assert rezultat == simulacija(t, K, A), f"simulacija se ne ujema pri {k:02d}"
        ime = os.path.join(TESTI, f"test{k:02d}")
        with open(ime + ".in", "w") as f:
            f.write(vhod)
        with open(ime + ".out", "w") as f:
            f.write(izhod)

print(f"Ustvarjenih {len(testi)} testov v {TESTI}")
