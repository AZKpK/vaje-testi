// Nebotičniki z monotonim skladom, O(N).
// Z i-tega nebotičnika vidimo levo do prvega strogo višjega: če je ta na
// indeksu j, vidimo i-j-1 nebotičnikov (če ga ni, vseh i). Desno enako.
// Na skladu so indeksi nebotičnikov s strogo padajočimi višinami; ko pride
// h[i], s sklada odstranimo vse z višino <= h[i], na vrhu ostane iskani j.
// Vsota je lahko do N(N-1) ~ 10^12, zato long long.
#include <cstdio>
#include <vector>
using namespace std;

int main() {
    int N;
    if (scanf("%d", &N) != 1) return 0;
    vector<int> h(N);
    for (int& x : h)
        if (scanf("%d", &x) != 1) return 0;

    long long Z = 0;
    vector<int> sklad;
    sklad.reserve(N);

    for (int i = 0; i < N; i++) {
        while (!sklad.empty() && h[sklad.back()] <= h[i]) sklad.pop_back();
        Z += sklad.empty() ? i : i - sklad.back() - 1;
        sklad.push_back(i);
    }

    sklad.clear();
    for (int i = N - 1; i >= 0; i--) {
        while (!sklad.empty() && h[sklad.back()] <= h[i]) sklad.pop_back();
        Z += sklad.empty() ? N - 1 - i : sklad.back() - i - 1;
        sklad.push_back(i);
    }

    printf("%lld\n", Z);
}
