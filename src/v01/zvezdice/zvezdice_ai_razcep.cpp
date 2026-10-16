// Zvezdice - sortiranje po b in razcep na predpono/pripono (Fenwickovo drevo).
//
// IDEJA IN DOKAZ PRAVILNOSTI
// Uganke uredimo naraščajoče po b.
//
// 1) Zamenjava: če ima uganka i 2 zvezdici, uganka j pa 0, in je b[i] > b[j],
//    jima stanji zamenjamo (j dobi 2, i dobi 0). Število zvezdic ostane enako,
//    čas se spremeni za b[j] - b[i] < 0 oz. <= 0 pri enakih b. Vzemimo
//    optimalno rešitev, ki ima najmanjšo vsoto položajev (v urejenem vrstnem
//    redu) ugank z 2 zvezdicama. Če bi v njej neka 2 stala za neko 0, bi ju
//    zamenjali: cena se ne poveča, vsota položajev pa se zmanjša - protislovje.
//    Torej obstaja optimalna rešitev, v kateri so vse 2 pred vsemi 0.
//
// 2) Razcep: naj bo k položaj prve 0 (oz. n, če je ni). Potem ima vsaka od
//    prvih k ugank vsaj 1 zvezdico, nobena od ostalih pa nima 2.
//    Za fiksen k je torej rešitev natanko:
//      - vsaka uganka v predponi [0,k) plača a[i] in jo lahko nadgradimo na 2
//        za dodatnih b[i]-a[i],
//      - vsako uganko v priponi [k,n) lahko rešimo za 1 zvezdico za a[i].
//    Potrebujemo še m = w - k dodatnih zvezdic, vsaka "izbira" iz multimnožice
//      U_k = { b[i]-a[i] : i < k }  ∪  { a[i] : i >= k }   (|U_k| = n)
//    prinese natanko eno zvezdico in izbire so med seboj neodvisne. Najcenejše
//    je torej vzeti m najmanjših elementov U_k:
//      cena(k) = sum_{i<k} a[i] + (vsota m najmanjših v U_k),   0 <= m <= n.
//    Vsak cena(k) ustreza veljavni razporeditvi z w zvezdicami, po 1) pa je
//    optimum enak eni od njih, zato je odgovor min po k od cena(k).
//
// IZVEDBA
// k povečujemo od 0 do n. Pri prehodu k -> k+1 iz U odstranimo a[k] in dodamo
// b[k]-a[k]. Vse možne vrednosti (2n) stisnemo in nad njimi vodimo dve
// Fenwickovi drevesi: število elementov in vsoto elementov po vrednosti.
// Vsoto m najmanjših dobimo s spustom po Fenwickovem drevesu: poiščemo največji
// položaj p, do katerega je manj kot m elementov; m-ti najmanjši ima vrednost
// na položaju p+1, vsota pa je vsota(do p) + (m - število(do p)) * vrednost(p+1).
// Za najboljši k rešitev zgradimo eksplicitno: uredimo U_k in vzamemo m najmanjših.
//
// ČASOVNA ZAHTEVNOST
// Urejanje in stiskanje O(n log n); n+1 korakov, vsak z O(log n) posodobitvami
// in poizvedbo; rekonstrukcija O(n log n). Skupaj O(n log n), prostor O(n).

#include <iostream>
#include <vector>
#include <string>
#include <climits>
#include <algorithm>
using namespace std;

struct Fenwick {
    int n, LOG;
    vector<long long> cnt, sum;
    Fenwick(int n) : n(n), cnt(n + 1, 0), sum(n + 1, 0) {
        LOG = 1;
        while ((1 << LOG) <= n) LOG++;
    }
    void add(int pos, long long c, long long v) {   // pos je 1-indeksiran
        for (; pos <= n; pos += pos & -pos) { cnt[pos] += c; sum[pos] += c * v; }
    }
    // vsota m najmanjših elementov; vals[p] = vrednost na položaju p (1-indeksirano)
    long long smallest(long long m, const vector<long long>& vals) const {
        if (m == 0) return 0;
        int p = 0;
        long long c = 0, s = 0;
        for (int step = 1 << LOG; step > 0; step >>= 1)
            if (p + step <= n && c + cnt[p + step] < m) {
                p += step;
                c += cnt[p];
                s += sum[p];
            }
        return s + (m - c) * vals[p + 1];
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, w;
    cin >> n >> w;
    vector<long long> a(n), b(n);
    for (int i = 0; i < n; i++) cin >> a[i] >> b[i];

    vector<int> ord(n);
    for (int i = 0; i < n; i++) ord[i] = i;
    sort(ord.begin(), ord.end(), [&](int x, int y){ return b[x] < b[y]; });

    // stiskanje vrednosti: vals[1..V]
    vector<long long> vals = {LLONG_MIN};
    for (int i = 0; i < n; i++) { vals.push_back(a[i]); vals.push_back(b[i] - a[i]); }
    sort(vals.begin() + 1, vals.end());
    vals.erase(unique(vals.begin() + 1, vals.end()), vals.end());
    int V = vals.size() - 1;
    auto poz = [&](long long v) {
        return int(lower_bound(vals.begin() + 1, vals.end(), v) - vals.begin());
    };

    Fenwick fw(V);
    for (int i = 0; i < n; i++) fw.add(poz(a[i]), 1, a[i]);   // k = 0: U = {a[i]}

    long long predpona = 0, best = LLONG_MAX;
    int bestK = -1;
    for (int k = 0; k <= n; k++) {
        long long m = w - k;
        if (0 <= m && m <= n) {
            long long c = predpona + fw.smallest(m, vals);
            if (c < best) { best = c; bestK = k; }
        }
        if (k == n) break;
        int i = ord[k];   // uganka i preide iz pripone v predpono
        fw.add(poz(a[i]), -1, a[i]);
        fw.add(poz(b[i] - a[i]), 1, b[i] - a[i]);
        predpona += a[i];
    }

    // rekonstrukcija za bestK
    string res(n, '0');
    vector<pair<long long, int>> U;   // (vrednost, položaj v ord)
    for (int k = 0; k < n; k++) {
        int i = ord[k];
        if (k < bestK) { res[i] = '1'; U.push_back({b[i] - a[i], k}); }
        else             U.push_back({a[i], k});
    }
    sort(U.begin(), U.end());
    for (int t = 0; t < w - bestK; t++) {
        int i = ord[U[t].second];
        res[i] = (U[t].second < bestK) ? '2' : '1';
    }

    cout << best << "\n" << res << "\n";
}
