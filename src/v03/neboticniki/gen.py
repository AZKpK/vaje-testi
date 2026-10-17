#!/usr/bin/env python3
# Generator testov za nalogo neboticniki (orodja/gen.py).
# Ustvari testi/test01.in ... testi/test50.in in pričakovane izhode *.out ter
# vanjo skopira splošni Makefile, zato je mapa testi/ samostojna:
#     make test name=<resitev>
# (mapa testi/ ni v gitu - vedno jo ustvariš znova s tem skriptom).
#
#   01-12: majhni testi za ročno preverjanje (primer iz naloge, robni primeri)
#   13-40: naraščajoča velikost, N od 10 do ~3000 (prehajajo tudi rešitve O(N^2))
#   41-45: N ~ 10^5, a vsak vidi daleč: naivne rešitve O(N^2) presežejo
#          časovno omejitev
#   46-50: tik pod omejitvami naloge (N = 10^6); vsota Z je večinoma večja od
#          2^31, pri vseh enakih celo N(N-1) ~ 10^12 (int se prelije)
#
# Pričakovane izhode izračuna neboticniki_ai.cpp (monoton sklad), na testih
# 01-40 pa se preverijo še z naivno rešitvijo v Pythonu.
#
# Uporaba: python3 gen.py [-j PROCESOV] [-t 3-7]   (testi so vedno enaki)
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "orodja"))
from gen import generiraj, iz_datoteke

MAX_N, MAX_H = 10**6, 10**9

def vhod(h):
    return [len(h)] + h

# ---------------------------------------------------------------- oblike ulic

def naklj(n, hi):
    return lambda r: vhod([r.randint(0, hi) for _ in range(n)])

def narascajoce(n, strogo=True):
    """Strogo naraščajoče (vsak vidi vse levo) ali nepadajoče z ponovitvami."""
    def f(r):
        h, x = [], r.randint(0, 10)
        for _ in range(n):
            x += r.randint(1 if strogo else 0, 3)
            h.append(x)
        return vhod(h)
    return f

def padajoce(n, strogo=True):
    return lambda r: vhod(narascajoce(n, strogo)(r)[1:][::-1])

def gora(n):
    """Naraščajoče do vrha, nato padajoče (vrh vidi vse)."""
    def f(r):
        h = sorted(r.randint(0, MAX_H) for _ in range(n))
        k = r.randint(n // 3, 2 * n // 3)
        return vhod(h[:k] + sorted(h[k:], reverse=True))
    return f

def dolina(n):
    """Padajoče do dna, nato naraščajoče (robova vidita skoraj vse)."""
    return lambda r: vhod([MAX_H - x for x in gora(n)(r)[1:]])

def zaga(n, zob):
    """Ponavljajoči se zobje naraščajočih višin; vrhovi vseh zob enaki."""
    return lambda r: vhod([(i % zob) * (MAX_H // zob) for i in range(n)])

def enaki(n, x=None):
    return lambda r: vhod([r.randint(0, MAX_H) if x is None else x] * n)

def nakljucni(n):
    """Naključna oblika, ki je uporabljena pri srednjih testih."""
    def f(r):
        izbira = r.randrange(7)
        if izbira == 0: return naklj(n, MAX_H)(r)
        if izbira == 1: return naklj(n, r.choice([1, 3, 10]))(r)    # veliko enakih
        if izbira == 2: return narascajoce(n, strogo=False)(r)
        if izbira == 3: return padajoce(n, strogo=r.random() < 0.5)(r)
        if izbira == 4: return gora(n)(r)
        if izbira == 5: return dolina(n)(r)
        return zaga(n, r.randint(2, max(2, n // 3)))(r)
    return f

# ---------------------------------------------------------------- testi

testi = [
    iz_datoteke("primer.in"),                       # 01 primer iz naloge (11)
    "1\n5\n",                                       # 02 N = 1
    "2\n3\n3\n",                                    # 03 dva enaka: vidita drug drugega
    "2\n0\n1000000000\n",                           # 04 skrajni višini
    narascajoce(10),                                # 05 strogo naraščajoče
    padajoce(10),                                   # 06 strogo padajoče
    "6\n0\n0\n0\n0\n0\n0\n",                        # 07 vse ničle: Z = N(N-1)
    "7\n1\n3\n1\n3\n1\n3\n1\n",                     # 08 izmenično, enaki vrhovi
    "8\n5\n1\n2\n5\n1\n5\n2\n5\n",                  # 09 enaki se ne zastirajo
    gora(12),                                       # 10
    dolina(12),                                     # 11
    naklj(15, 3),                                   # 12 veliko ponovitev
]

# 13-40: naraščajoča velikost (geometrijsko od 10 do 3000)
testi += [nakljucni(round(10 * 300 ** (k / 27))) for k in range(28)]

# 41-45: N ~ 10^5, vsak vidi daleč - naivna rešitev naredi ~N^2/2 korakov
testi += [
    enaki(100000),
    narascajoce(100000),
    padajoce(100000, strogo=False),
    dolina(100000),
    zaga(100000, 50000),
]

# 46-50: tik pod omejitvami
testi += [
    naklj(MAX_N, MAX_H),                            # 46 naključno
    naklj(MAX_N, 5),                                # 47 malo različnih višin
    gora(MAX_N),                                    # 48
    narascajoce(MAX_N, strogo=False),               # 49
    enaki(MAX_N, MAX_H),                            # 50 največji Z = N(N-1)
]
assert len(testi) == 50

def veljaven(v):
    st = list(map(int, v.split()))
    N, h = st[0], st[1:]
    assert 1 <= N <= MAX_N and len(h) == N, "N"
    assert all(0 <= x <= MAX_H for x in h), "h"

def naivna(v):
    """Z vsakega nebotičnika gre levo in desno, dokler ne naleti na višjega."""
    st = list(map(int, v.split()))
    N, h = st[0], st[1:]
    Z = 0
    for i in range(N):
        j = i - 1
        while j >= 0 and h[j] <= h[i]: j -= 1
        k = i + 1
        while k < N and h[k] <= h[i]: k += 1
        Z += (i - j - 1) + (k - i - 1)
    return [Z]

generiraj(testi, resitev="neboticniki_ai.cpp", veljaven=veljaven,
          preveri=[(naivna, range(1, 41))])
