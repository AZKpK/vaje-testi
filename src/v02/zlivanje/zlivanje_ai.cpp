#include <iostream>
#include <vector>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, K, A;
    cin >> N >> K >> A;
    vector<int> t(N), buf(N);
    for (int& x : t) cin >> x;

    // Meje čet: b[j] je začetek j-te čete, zadnji element je N (konec zadnje čete).
    vector<int> b = {0};
    for (int i = 1; i < N; i++)
        if (t[i-1] > t[i]) b.push_back(i);
    b.push_back(N);

    // Korak ponavljamo, dokler ni ostala samo ena četa (b = {0, N}).
    for (int a = 0; a < A && b.size() > 2; a++) {
        int R = b.size() - 1;   // število čet
        vector<int> nb;         // meje po tem koraku

        for (int g = 0; g < R; g += K) {
            int m = min(K, R - g);   // zadnja skupina ima lahko manj kot K čet
            // Trenutni položaj in konec vsake čete v skupini. (Fiksni tabeli int[10]
            // na skladu sta bili z g++ -O2 pri velikih K ~2x počasnejši.)
            vector<int> pos(m), end(m);
            for (int j = 0; j < m; j++) {
                pos[j] = b[g+j];
                end[j] = b[g+j+1];
            }

            // Zlivanje: vsakič vzamemo najmanjši element z začetkov nepraznih čet.
            for (int k = b[g]; k < b[g+m]; k++) {
                int best = -1, minimum = 0;
                for (int j = 0; j < m; j++)
                    if (pos[j] < end[j] && (best == -1 || t[pos[j]] < minimum))
                        best = j, minimum = t[pos[j]];
                buf[k] = t[pos[best]++];
            }

            // Zlita skupina je nova četa. Med skupinami ostane padec,
            // zato so nove meje kar vsaka K-ta stara meja.
            nb.push_back(b[g]);
        }
        nb.push_back(N);

        swap(t, buf);
        b = nb;
    }

    for (int i = 0; i < N; i++)
        cout << t[i] << (i + 1 < N ? ' ' : '\n');
}