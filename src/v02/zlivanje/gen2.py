#!/usr/bin/env python3
# Generator velikih testov za nalogo zlivanje (naravno K-smerno zlivanje).
# Ustvari testi2/test01.in ... testi2/test50.in in pričakovane izhode *.out ter
# vanjo skopira splošni Makefile (orodja/Makefile.testi), zato je mapa testi2/
# samostojna: make test name=<resitev>
# (mapa testi2/ ni v gitu - vedno jo ustvariš znova s tem skriptom).
#
# Vsi testi so tik pod omejitvami naloge (N med 950 000 in 10^6), med sabo pa
# se razlikujejo po obliki zaporedja (naključno, padajoče, urejeno, enaki
# elementi, čete določenih dolžin, žaga, ...), po K (2-10) in po A (od 1 do 20,
# z ustavljanjem pred A koraki ali brez). Pri testih "meje" je število čet
# točno K^A + 1 ipd., da se preveri zadnja (nepolna) skupina.
#
# Pričakovane izhode izračuna zlivanje_ai.cpp. Preveri jih neodvisna rešitev
# v Pythonu, ki po A korakih uredi vsak blok K^A originalnih čet.
#
# Testi se generirajo vzporedno v več procesih (Pythonove niti zaradi GIL
# generiranja ne bi pospešile). Vsak test ima svoje seme, zato so testi enaki
# ne glede na število procesov in vrstni red izvajanja.
#
# Uporaba: python3 gen2.py [-j PROCESOV]     (privzeto: število jeder)
import argparse, concurrent.futures, glob, os, random, shutil, subprocess, tempfile

MAPA = os.path.dirname(os.path.abspath(__file__))
TESTI = os.path.join(MAPA, "testi2")
MAKEFILE = os.path.join(MAPA, "..", "..", "..", "orodja", "Makefile.testi")
MAX_N, MAX_K, MAX_A, MAX_V = 10**6, 10, 20, 10**9
SEME = 2026

# ---------------------------------------------------------------- pomožne

def meje_cet(t):
    return [0] + [i for i in range(1, len(t)) if t[i-1] > t[i]] + [len(t)]

def potrebnih_korakov(R, K):
    """Koliko korakov zlivanja potrebujemo za R čet, da ostane ena."""
    koraki = 0
    while R > 1:
        R, koraki = (R + K - 1) // K, koraki + 1
    return koraki

def bloki(t, K, A):
    """Neodvisna rešitev: po A korakih je urejen vsak blok K^A originalnih čet."""
    meje = meje_cet(t)
    R = len(meje) - 1
    blok = min(K ** A, R)
    izhod = []
    for g in range(0, R, blok):
        izhod += sorted(t[meje[g]:meje[min(g + blok, R)]])
    return izhod

# ---------------------------------------------------------------- oblike zaporedij

def naklj(r, n, lo=0, hi=MAX_V):
    return [r.randint(lo, hi) for _ in range(n)]

def padajoce(r, n):
    """Strogo padajoče, različne vrednosti: n čet dolžine 1."""
    return sorted(r.sample(range(MAX_V + 1), n), reverse=True)

def iz_dolzin(r, dolzine, hi=MAX_V):
    """Zaporedje s četami točno podanih dolžin (vse >= 2)."""
    cete = [sorted(naklj(r, d, 0, hi)) for d in dolzine]
    for prej, zdaj in zip(cete, cete[1:]):
        if prej[-1] <= zdaj[0]:           # meja mora biti padec
            prej[-1], zdaj[0] = hi, 0
    return [x for c in cete for x in c]

def razdeli(r, n, R):
    """n razdeli na R delov, vsak vsaj 2."""
    m = n - R                              # m razrežemo na R delov >= 1, vsakemu prištejemo 1
    rezi = sorted(r.sample(range(1, m), R - 1))
    return [b - a + 1 for a, b in zip([0] + rezi, rezi + [m])]

def dolzine_do(r, n, gen):
    """Dolžine čet iz generatorja gen(), dokler ne pridemo do n (vse >= 2)."""
    d, vsota = [], 0
    while vsota < n:
        d.append(max(2, gen()))
        vsota += d[-1]
    d[-1] -= vsota - n
    if d[-1] < 2:
        d[-2] += d.pop()
    return d

def zaga(r, n, perioda):
    return [i % perioda for i in range(n)]

def bloki_padajoce(r, n, dolzina):
    """Urejeni bloki, vsak blok ima večje vrednosti od naslednjega."""
    t = []
    nivo = MAX_V
    while len(t) < n:
        d = min(dolzina, n - len(t))
        korak = MAX_V // (n // dolzina + 2)
        t += sorted(naklj(r, d, nivo - korak + 1, nivo))
        nivo -= korak
    return t

def skoraj_urejeno(r, n, zamenjav):
    t = sorted(naklj(r, n))
    for _ in range(zamenjav):
        i, j = r.randrange(n), r.randrange(n)
        t[i], t[j] = t[j], t[i]
    return t

def enake_cete(r, n, d):
    """Vse čete so enake (veliko izenačenj med začetki čet)."""
    c = sorted(naklj(r, d))
    return (c * (n // d + 1))[:n]

def orgle(r, n):
    """Narašča do sredine, nato pada."""
    t = sorted(naklj(r, n))
    return t[0::2] + t[1::2][::-1]

# ---------------------------------------------------------------- seznam testov
# (opis, funkcija (r, n) -> zaporedje, K, A)
# n je naključen med 950 000 in 10^6 (ali MAX_N, kjer je zapisano).
# A: število, "delno" (še ni urejeno), "max" (zadnji korak pred urejenostjo),
#    "tocno" (urejeno točno v A-tem koraku), "vec" (A = 20, ustavi se prej).

def N(r):
    return r.randint(950000, MAX_N)

TESTI_SPEC = [
    ("naključno, K=2",                         lambda r, n: naklj(r, n), 2, "delno"),
    ("naključno, K=10",                        lambda r, n: naklj(r, n), 10, "delno"),
    ("naključno, A=1",                         lambda r, n: naklj(r, n), 3, 1),
    ("naključno, A=20 (ustavi se prej)",       lambda r, n: naklj(r, n), 7, "vec"),
    ("vrednosti 0..1",                         lambda r, n: naklj(r, n, 0, 1), 2, "delno"),
    ("vrednosti 0..10",                        lambda r, n: naklj(r, n, 0, 10), 5, "delno"),
    ("vrednosti 0..1000",                      lambda r, n: naklj(r, n, 0, 1000), 4, "delno"),
    ("vsi enaki (ena četa)",                   lambda r, n: [r.randint(0, MAX_V)] * n, 2, 20),
    ("že urejeno, različne vrednosti",         lambda r, n: sorted(r.sample(range(MAX_V + 1), n)), 3, 20),
    ("že urejeno, ponovitve",                  lambda r, n: sorted(naklj(r, n, 0, 1000)), 10, 1),
    ("strogo padajoče, K=2, največ dela",      padajoce, 2, "max"),
    ("strogo padajoče, K=2, A=20",             padajoce, 2, 20),
    ("strogo padajoče, K=10",                  padajoce, 10, "max"),
    ("strogo padajoče, K=3",                   padajoce, 3, "delno"),
    ("padajoče po parih (x x y y ...)",        lambda r, n: [MAX_V - i // 2 for i in range(n)], 2, "delno"),
    ("izmenično 10^9, 0",                      lambda r, n: [MAX_V * (1 - i % 2) for i in range(n)], 4, "delno"),
    ("čete dolžine 10",                        lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: 10)), 6, "delno"),
    ("čete dolžine 1000",                      lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: 1000)), 9, "delno"),
    ("10 čet dolžine 100 000",                 lambda r, n: iz_dolzin(r, [n // 10] * 9 + [n - 9 * (n // 10)]), 3, 2),
    ("dve četi, A=1",                          lambda r, n: iz_dolzin(r, razdeli(r, n, 2)), 2, 1),
    ("dve četi, K=10, A=20",                   lambda r, n: iz_dolzin(r, razdeli(r, n, 2)), 10, 20),
    ("geometrijske dolžine čet",               lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: int(r.expovariate(1 / 5)))), 8, "delno"),
    ("dolžine čet z dolgim repom (Pareto)",    lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: int(r.paretovariate(1.2)))), 5, "delno"),
    ("ena ogromna četa na začetku",            lambda r, n: iz_dolzin(r, [900000] + dolzine_do(r, n - 900000, lambda: r.randint(2, 6))), 2, "delno"),
    ("ena ogromna četa na koncu",              lambda r, n: iz_dolzin(r, dolzine_do(r, n - 900000, lambda: r.randint(2, 6)) + [900000]), 3, "delno"),
    ("skoraj urejeno, 10 zamenjav",            lambda r, n: skoraj_urejeno(r, n, 10), 2, "delno"),
    ("skoraj urejeno, 1000 zamenjav",          lambda r, n: skoraj_urejeno(r, n, 1000), 10, "delno"),
    ("žaga s periodo 100",                     lambda r, n: zaga(r, n, 100), 7, "delno"),
    ("žaga s periodo 10 000",                  lambda r, n: zaga(r, n, 10000), 2, "delno"),
    ("orgle (gor, nato dol)",                  orgle, 4, "delno"),
    ("urejeni bloki v padajočem vrstnem redu", lambda r, n: bloki_padajoce(r, n, 1000), 5, "delno"),
    ("meje: R = 2^18 + 1, A=18",               lambda r, n: iz_dolzin(r, razdeli(r, n, 2**18 + 1)), 2, 18),
    ("meje: R = 2^18 - 1, A=17",               lambda r, n: iz_dolzin(r, razdeli(r, n, 2**18 - 1)), 2, 17),
    ("meje: R = 10^5 + 1, A=5",                lambda r, n: iz_dolzin(r, razdeli(r, n, 10**5 + 1)), 10, 5),
    ("meje: R = 3*10^5 - 1, A=5",              lambda r, n: iz_dolzin(r, razdeli(r, n, 3 * 10**5 - 1)), 10, 5),
    ("meje: R = 7^6 + 6, A=6",                 lambda r, n: iz_dolzin(r, razdeli(r, n, 7**6 + 6)), 7, 6),
    ("vse čete enake (izenačeni začetki)",     lambda r, n: enake_cete(r, n, 100), 4, "delno"),
    ("samo vrednosti 0 in 10^9",               lambda r, n: [r.choice((0, MAX_V)) for _ in range(n)], 9, "delno"),
    ("vse čete se začnejo z 0",                lambda r, n: [0 if i % 7 == 0 else r.randint(1, MAX_V) for i in range(n)], 6, "delno"),
    ("nenaraščajoče, skupine po 3",            lambda r, n: [MAX_V - i // 3 for i in range(n)], 3, "delno"),
    ("naključno, K=2, A=1",                    lambda r, n: naklj(r, n), 2, 1),
    ("naključno, urejeno točno v A-tem koraku", lambda r, n: naklj(r, n), 5, "tocno"),
    ("naključno, K=6, največ dela",            lambda r, n: naklj(r, n), 6, "max"),
    ("geometrijske dolžine, vrednosti 0..100", lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: int(r.expovariate(1 / 4))), 100), 10, "delno"),
    ("vrednosti blizu 10^9",                   lambda r, n: naklj(r, n, MAX_V - 100, MAX_V), 8, "delno"),
    ("nenaraščajoče s ponovitvami",            lambda r, n: sorted(naklj(r, n, 0, 1000), reverse=True), 2, "delno"),
    ("izmenično kratke in dolge čete",         lambda r, n: iz_dolzin(r, dolzine_do(r, n, lambda: 2 if r.random() < 0.5 else 2000)), 3, "delno"),
    ("pol padajoče, pol naključno",            lambda r, n: padajoce(r, n // 2) + naklj(r, n - n // 2), 2, "delno"),
    ("naključno, K=10, največ dela",           lambda r, n: naklj(r, n), 10, "max"),
    ("naključno, N = 10^6, K=2, največ dela",  lambda r, n: naklj(r, MAX_N), 2, "max"),
]
assert len(TESTI_SPEC) == 50

# ---------------------------------------------------------------- en test

def naredi_test(k, exe):
    opis, gen, K, A = TESTI_SPEC[k - 1]
    r = random.Random(SEME * 1000 + k)
    t = gen(r, N(r))
    n = len(t)
    R = len(meje_cet(t)) - 1
    potrebno = potrebnih_korakov(R, K)
    if A == "delno":
        A = r.randint(1, max(1, potrebno - 1))
    elif A == "max":
        A = max(1, potrebno - 1)
    elif A == "tocno":
        A = max(1, potrebno)
    elif A == "vec":
        A = MAX_A

    assert 950000 <= n <= MAX_N and 2 <= K <= MAX_K and 1 <= A <= MAX_A, opis
    assert all(0 <= x <= MAX_V for x in t), opis

    vhod = f"{n} {K} {A}\n" + "\n".join(map(str, t)) + "\n"
    izhod = subprocess.run([exe], input=vhod, capture_output=True, text=True, check=True).stdout
    assert list(map(int, izhod.split())) == bloki(t, K, A), f"izhod se ne ujema pri test{k:02d} ({opis})"

    ime = os.path.join(TESTI, f"test{k:02d}")
    with open(ime + ".in", "w") as f:
        f.write(vhod)
    with open(ime + ".out", "w") as f:
        f.write(izhod)
    return k, opis, n, K, A, R, potrebno

# ---------------------------------------------------------------- main

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generator velikih testov za zlivanje (v testi2/).")
    p.add_argument("-j", type=int, default=os.cpu_count(), help="število procesov (privzeto: število jeder)")
    j = p.parse_args().j

    os.makedirs(TESTI, exist_ok=True)
    for f in glob.glob(os.path.join(TESTI, "*.in")) + glob.glob(os.path.join(TESTI, "*.out")):
        os.remove(f)
    shutil.copy(MAKEFILE, os.path.join(TESTI, "Makefile"))

    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "zlivanje_ai")
        subprocess.run(["g++", "-O2", "-std=c++17", "-o", exe,
                        os.path.join(MAPA, "zlivanje_ai.cpp")], check=True)
        with concurrent.futures.ProcessPoolExecutor(max_workers=j) as pool:
            rezultati = sorted(pool.map(naredi_test, range(1, 51), [exe] * 50))

    print(f"{'test':<7}{'N':>8}{'K':>4}{'A':>4}{'čet':>9}{'korakov':>9}  opis")
    for k, opis, n, K, A, R, potrebno in rezultati:
        stanje = "urejeno" if A >= potrebno else f"{A}/{potrebno}"
        print(f"test{k:02d}{n:>8}{K:>4}{A:>4}{R:>9}{stanje:>9}  {opis}")
    print(f"Ustvarjenih {len(rezultati)} testov v {TESTI} ({j} procesov)")
