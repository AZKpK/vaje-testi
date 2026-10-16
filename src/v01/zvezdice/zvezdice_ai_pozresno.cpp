// Zvezdice - požrešna rešitev (ena zvezdica naenkrat) s kopicami.
//
// IDEJA
// Začnemo z razporeditvijo, kjer je vsaka uganka preskočena (0 zvezdic, čas 0),
// kar je očitno optimalno za 0 zvezdic. Nato w-krat izvedemo najcenejšo izmed
// potez, ki skupno število zvezdic povečajo za natanko 1:
//   A) i: 0 -> 1                cena  a[i]
//   B) i: 1 -> 2                cena  b[i] - a[i]
//   C) i: 1 -> 0,  j: 0 -> 2    cena  b[j] - a[i]
//   D) i: 2 -> 1,  j: 0 -> 2    cena  b[j] - (b[i] - a[i])
//
// DOKAZ PRAVILNOSTI
// Lema: Naj bo R optimalna razporeditev za w zvezdic. Potem obstaja optimalna
// razporeditev za w+1 zvezdic, ki jo iz R dobimo z eno od potez A-D.
//
// Dokaz: Med vsemi optimalnimi razporeditvami za w+1 vzemimo R', ki se od R
// razlikuje v čim manj ugankah. Naj bo d_i = R'_i - R_i (razlika v številu
// zvezdic pri uganki i); velja d_i ∈ {-2,-1,0,1,2} in vsota vseh d_i = 1.
// Denimo, da obstaja neprazna množica S ugank z d_i != 0, pri kateri je
// vsota d_i po S enaka 0. Ker je čas vsota po ugankah, lahko spremembo cene
// zaradi sprememb na S označimo z Δ(S).
//   - R, spremenjena le na S (kot v R'), ima w zvezdic, zato je njena cena
//     >= cena(R)  =>  Δ(S) >= 0.
//   - R', na S vrnjena nazaj na R, ima w+1 zvezdic, zato je njena cena
//     >= cena(R') =>  Δ(S) <= 0.
// Torej Δ(S) = 0 in R' vrnjena na S je prav tako optimalna za w+1, a se od R
// razlikuje v manj ugankah - protislovje. Zato med neničelnimi d_i ni
// nobene podmnožice z vsoto 0, kar pomeni, da ne nastopajo hkrati:
// +1 in -1;  +2 in -2;  +1,+1 in -2;  -1,-1 in +2.
// Primeri:
//   - ni negativnih d_i: vsota pozitivnih je 1, torej en sam +1
//       -> poteza A (0->1) ali B (1->2).
//   - nastopa -2 (in zato ni +2): pozitivni so le +1 in največ en (sicer
//       +1,+1,-2), vsota bi bila <= 1 - 2 < 1 - protislovje.
//   - nastopa -1 (in zato ni +1, ni -2): pozitivni so +2; največ en -1 ob +2
//       (sicer -1,-1,+2), torej vsota 2p - 1 = 1 => p = 1: en +2 in en -1.
//       +2 je lahko le 0->2, -1 pa 1->0 ali 2->1  -> poteza C ali D.
// S tem je lema dokazana.
//
// Iz leme sledi z indukcijo po številu zvezdic: če je trenutna razporeditev
// optimalna za k zvezdic, je najcenejša poteza izmed A-D (za vsako potezo
// izberemo najugodnejše uganke, glej spodaj) vsaj tako poceni kot poteza do
// neke optimalne razporeditve za k+1, zato je nova razporeditev optimalna za k+1.
// Poteza vedno obstaja, ker je w <= 2n (dokler niso vse uganke na 2, obstaja A ali B).
//
// IZVEDBA
// Najugodnejše uganke za posamezno potezo hranimo v petih min-kopicah:
//   hA0   : a[i]          med used == 0   (A, najmanjši a)
//   hB0   : b[i]          med used == 0   (C, D: najmanjši b)
//   hBA1  : b[i]-a[i]     med used == 1   (B, najmanjša nadgradnja)
//   hA1   : -a[i]         med used == 1   (C, največji a)
//   hBA2  : -(b[i]-a[i])  med used == 2   (D, največja nadgradnja)
// Uporabljamo leno brisanje: ob spremembi stanja uganke je ne odstranimo iz
// starih kopic, temveč jo le dodamo v kopice novega stanja. Preden pogledamo
// vrh, z njega odstranimo vnose, katerih uganka ni več v pravem stanju.
// Ključ vnosa je odvisen le od uganke, zato je stari vnos, ki je spet veljaven
// (uganka se je vrnila v isto stanje), še vedno pravilen.
//
// ČASOVNA ZAHTEVNOST
// Začetno polnjenje: O(n log n). Vsaka od w potez spremeni stanje največ dvema
// ugankama, kar doda O(1) vnosov v kopice, torej je vseh vnosov O(n + w) in
// vsak se največ enkrat odstrani. Skupaj O((n + w) log(n + w)), prostor O(n + w).

#include <iostream>
#include <vector>
#include <queue>
#include <string>
#include <climits>
#include <algorithm>
using namespace std;

using P = pair<long long, int>;
using MinHeap = priority_queue<P, vector<P>, greater<P>>;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, w;
    cin >> n >> w;
    vector<long long> a(n), b(n);
    for (int i = 0; i < n; i++) cin >> a[i] >> b[i];

    vector<int> used(n, 0);
    MinHeap hA0, hB0, hBA1, hA1, hBA2;

    auto dodaj = [&](int i) {
        if (used[i] == 0)      { hA0.push({a[i], i}); hB0.push({b[i], i}); }
        else if (used[i] == 1) { hBA1.push({b[i] - a[i], i}); hA1.push({-a[i], i}); }
        else                     hBA2.push({-(b[i] - a[i]), i});
    };
    // vrne indeks uganke na vrhu kopice h, ki je v stanju 'stanje', ali -1
    auto vrh = [&](MinHeap& h, int stanje) {
        while (!h.empty() && used[h.top().second] != stanje) h.pop();
        return h.empty() ? -1 : h.top().second;
    };

    for (int i = 0; i < n; i++) dodaj(i);

    const long long INF = LLONG_MAX;
    long long sum = 0;
    for (int k = 0; k < w; k++) {
        int iA = vrh(hA0, 0), jB = vrh(hB0, 0), iBA1 = vrh(hBA1, 1),
            iA1 = vrh(hA1, 1), iBA2 = vrh(hBA2, 2);

        long long cA = iA   >= 0 ? a[iA] : INF;
        long long cB = iBA1 >= 0 ? b[iBA1] - a[iBA1] : INF;
        long long cC = (jB >= 0 && iA1  >= 0) ? b[jB] - a[iA1] : INF;
        long long cD = (jB >= 0 && iBA2 >= 0) ? b[jB] - (b[iBA2] - a[iBA2]) : INF;
        long long best = min({cA, cB, cC, cD});

        if (best == cA)      { used[iA] = 1;   dodaj(iA); }
        else if (best == cB) { used[iBA1] = 2; dodaj(iBA1); }
        else if (best == cC) { used[iA1] = 0;  used[jB] = 2; dodaj(iA1);  dodaj(jB); }
        else                 { used[iBA2] = 1; used[jB] = 2; dodaj(iBA2); dodaj(jB); }
        sum += best;
    }

    string res(n, '0');
    for (int i = 0; i < n; i++) res[i] = '0' + used[i];
    cout << sum << "\n" << res << "\n";
}
