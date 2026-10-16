#!/usr/bin/awk -f
# Checker za nalogo zvezdice.
# Uporaba: awk -f checker.awk vhod.in pricakovan.out dejanski.out
#
# Pravilnih razporeditev je lahko več, zato druge vrstice ne primerjamo dobesedno:
#   1. vrstica (najmanjši čas) mora biti enaka pričakovani,
#   2. vrstica mora biti niz n znakov iz {0,1,2} z vsoto w, katerega čas je
#      enak izpisanemu.
# Izhodna koda 0 = pravilno, 1 = napačno (razlog izpišemo).
# Vsote so do 3*10^14 < 2^53, zato so v awk (double) natančne.

# prebere vse besede datoteke f v t[1..m], vrne m
function beri(f, t,   m, k, j, v, x) {
    m = 0
    while ((getline v < f) > 0) {
        k = split(v, x)
        for (j = 1; j <= k; j++) t[++m] = x[j]
    }
    close(f)
    return m
}

function napaka(msg) {
    print msg
    exit 1
}

BEGIN {
    beri(ARGV[1], vh)                   # vh: n w a1 b1 a2 b2 ...
    n = vh[1]; w = vh[2]
    beri(ARGV[2], pr)
    if (beri(ARGV[3], iz) < 2) napaka("pricakovani 2 vrstici")

    if (iz[1] != pr[1]) napaka("cas " iz[1] ", pricakovan " pr[1])

    s = iz[2]
    if (length(s) != n || s !~ /^[012]+$/)
        napaka("razporeditev mora biti niz " n " znakov iz 0/1/2")

    z = 0; c = 0
    for (i = 1; i <= n; i++) {
        d = substr(s, i, 1)
        z += d
        if (d == "1") c += vh[2 * i + 1]
        else if (d == "2") c += vh[2 * i + 2]
    }
    if (z != w) napaka("razporeditev da " z " zvezdic, potrebnih " w)
    if (c != pr[1]) napaka(sprintf("razporeditev stane %.0f, izpisano %s", c, iz[1]))
    exit 0
}
