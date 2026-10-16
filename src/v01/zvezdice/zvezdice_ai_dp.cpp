// Zvezdice - dinamično programiranje (referenčna rešitev za preverjanje).
//
// dp[i][s] = najmanjši čas, da s prvimi i ugankami dobimo natanko s zvezdic.
//   dp[0][0] = 0, dp[0][s>0] = INF
//   dp[i][s] = min(dp[i-1][s],              // uganko i preskočimo
//                  dp[i-1][s-1] + a[i],     // uganko i rešimo za 1 zvezdico
//                  dp[i-1][s-2] + b[i])     // uganko i rešimo za 2 zvezdici
//
// Pravilnost: vsaka razporeditev prvih i ugank se konča z eno od treh odločitev
// za uganko i, ostanek pa je razporeditev prvih i-1 ugank z ustrezno manj
// zvezdicami. Cena je vsota po ugankah, zato je optimalni ostanek kar dp[i-1][.].
// Pravo rešitev rekonstruiramo s sledenjem nazaj od dp[n][w].
//
// Časovna zahtevnost: O(n * w), prostor O(n * w).
// Za n = 3*10^5, w = 6*10^5 je to ~10^11 korakov in preveč pomnilnika -> samo za
// majhne vhode (npr. n <= 2000), kjer služi za preverjanje hitrejših rešitev.

#include <iostream>
#include <vector>
#include <string>
#include <climits>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, w;
    cin >> n >> w;
    vector<long long> a(n + 1), b(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i] >> b[i];

    const long long INF = LLONG_MAX / 4;
    vector<vector<long long>> dp(n + 1, vector<long long>(w + 1, INF));
    dp[0][0] = 0;
    for (int i = 1; i <= n; i++)
        for (int s = 0; s <= w; s++) {
            long long best = dp[i-1][s];
            if (s >= 1) best = min(best, dp[i-1][s-1] + a[i]);
            if (s >= 2) best = min(best, dp[i-1][s-2] + b[i]);
            dp[i][s] = best;
        }

    // rekonstrukcija
    string res(n, '0');
    int s = w;
    for (int i = n; i >= 1; i--) {
        if (dp[i][s] == dp[i-1][s]) continue;
        if (s >= 1 && dp[i][s] == dp[i-1][s-1] + a[i]) { res[i-1] = '1'; s -= 1; }
        else                                           { res[i-1] = '2'; s -= 2; }
    }

    cout << dp[n][w] << "\n" << res << "\n";
}
