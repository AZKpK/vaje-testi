#!/usr/bin/env bash
# Zapakira teste naloge in jih naloži v GitHub Release v repoju s testi
# (privzeto <tvoj_uporabnik>/vaje-testi, glej orodja/deli.sh).
#
# Uporaba:  orodja/izdaj.sh mapa_naloge [testi ...]
#
#   Vsako mapo testi* v mapi naloge (ali le naštete) zapakira v .tar.xz, ki
#   vsebuje le Makefile, checker.awk ter *.in in *.out (brez .res, .diff in
#   prevedenih programov), in arhive naloži v release z imenom naloge:
#     testi  -> <naloga>.tar.xz
#     testi2 -> <naloga>-testi2.tar.xz
#   Če release še ne obstaja, ga ustvari, sicer arhive zamenja. Opis releasa
#   se vsakič na novo sestavi iz vseh arhivov v njem.
#
#   Običajno ga v GitHub Actions kliče orodja/ci/generiraj.sh; lokalno je
#   uporaben za naloge brez generatorja (npr. s šolskimi testi):
#     orodja/izdaj.sh src/v02/inverzije
#
#   Repo je v spremenljivki REPO. Lokalno je potreben prijavljen gh
#   (sudo apt install gh && gh auth login).

set -eu

if [ $# -lt 1 ]; then
    sed -n '4,20p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi

naloga_dir=${1%/}
shift
naloga=$(basename "$(realpath "$naloga_dir")")
vaja=$(basename "$(dirname "$(realpath "$naloga_dir")")")

if ! command -v gh > /dev/null; then
    echo "Manjka gh: sudo apt install gh && gh auth login"
    exit 2
fi
# v GitHub Actions se gh prijavi z GH_TOKEN
if [ -z "${GH_TOKEN:-}" ] && ! gh auth status > /dev/null 2>&1; then
    echo "gh ni prijavljen: gh auth login"
    exit 2
fi
REPO=${REPO:-$(gh api user --jq .login)/vaje-testi}
if ! gh repo view "$REPO" > /dev/null 2>&1; then
    echo "Repo $REPO ne obstaja (ustvari ga orodja/deli.sh)"
    exit 2
fi

if [ $# -gt 0 ]; then
    mape=("$@")
else
    mape=()
    for d in "$naloga_dir"/testi*/; do
        [ -d "$d" ] && mape+=("$(basename "$d")")
    done
fi
if [ ${#mape[@]} -eq 0 ]; then
    echo "V mapi $naloga_dir ni map testi*"
    exit 2
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# xz z vsemi jedri; -6 namesto -9, ker -9 zaradi porabe pomnilnika uporabi
# manj niti in je ~5x počasnejši za le ~8 % manjši arhiv
export XZ_OPT=${XZ_OPT:--6 -T0}
max=$((2 * 1024 * 1024 * 1024))   # omejitev GitHuba za eno datoteko

arhivi=()
for m in "${mape[@]}"; do
    m=${m%/}
    if [ ! -d "$naloga_dir/$m" ]; then
        echo "Ni mape $naloga_dir/$m"
        exit 2
    fi
    if [ "$m" = testi ]; then
        arh="$tmp/$naloga.tar.xz"
    else
        arh="$tmp/$naloga-$m.tar.xz"
    fi

    # seznam datotek s potmi relativno na mapo naloge, da se arhiv razpakira v testi*/
    find "$naloga_dir/$m" -maxdepth 1 -type f \
        \( -name Makefile -o -name checker.awk -o -name '*.in' -o -name '*.out' \) \
        -printf "$m/%f\n" | sort > "$tmp/seznam"
    if ! grep -q '\.in$' "$tmp/seznam"; then
        echo "V mapi $naloga_dir/$m ni datotek *.in"
        exit 2
    fi

    echo "Pakiram $m (število testov: $(grep -c '\.in$' "$tmp/seznam")) ..."
    tar -cJf "$arh" -C "$naloga_dir" -T "$tmp/seznam"
    vel=$(stat -c %s "$arh")
    if [ "$vel" -gt "$max" ]; then
        echo "$(basename "$arh") je prevelik ($(numfmt --to=iec "$vel") > 2 GiB)"
        exit 1
    fi
    echo "  -> $(basename "$arh") ($(numfmt --to=iec "$vel"))"
    arhivi+=("$arh")
done

url="https://github.com/$REPO/releases/download/$naloga"
if gh release view "$naloga" -R "$REPO" > /dev/null 2>&1; then
    echo "Posodabljam release $naloga ..."
    gh release upload "$naloga" "${arhivi[@]}" --clobber -R "$REPO"
    # tag premaknemo na trenutni commit, da "Source code (zip)" vsebuje
    # trenutni generator
    if [ -n "${GITHUB_SHA:-}" ]; then
        gh api -X PATCH "repos/$REPO/git/refs/tags/$naloga" \
            -f sha="$GITHUB_SHA" -F force=true > /dev/null
    fi
else
    echo "Ustvarjam release $naloga ..."
    gh release create "$naloga" "${arhivi[@]}" -R "$REPO" \
        ${GITHUB_SHA:+--target "$GITHUB_SHA"} \
        --title "$vaja – $naloga" --notes ""
fi

# opis releasa iz vseh arhivov v njem (tudi tistih, ki jih ta zagon ni naložil)
mapfile -t vsi < <(gh release view "$naloga" -R "$REPO" --json assets \
                   --jq '.assets[].name' | grep '\.tar\.xz$' | sort)
mapa_arhiva() {   # zlivanje.tar.xz -> testi, zlivanje-testi2.tar.xz -> testi2
    local m=${1%.tar.xz}
    if [ "$m" = "$naloga" ]; then echo testi; else echo "${m#"$naloga"-}"; fi
}
notes="Testi so pod **Assets** (\"Source code\" ne vsebuje testov):
"
primer=${vsi[0]}
for a in "${vsi[@]}"; do
    [ "$a" = "$naloga.tar.xz" ] && primer=$a
    notes+="
- [\`$a\`]($url/$a) → mapa \`$(mapa_arhiva "$a")/\`"
done
notes+="

Prenos in testiranje (rešitev \`.cpp\` daj v mapo, kjer razpakiraš, ali v mapo testov):

\`\`\`bash
curl -LO $url/$primer
tar -xJf $primer
cd $(mapa_arhiva "$primer") && make test name=<ime_resitve_brez_.cpp>
\`\`\`"

shopt -s nullglob
gen=("$naloga_dir"/gen*.py)
if [ ${#gen[@]} -gt 0 ]; then
    rel=$(git -C "$naloga_dir" rev-parse --show-prefix 2> /dev/null || echo "$naloga_dir/")
    notes+="

Teste lahko ustvariš tudi sam (potrebuješ \`python3\` in \`g++\`): prenesi
**Source code (zip)**, ga razpakiraj in v razpakirani mapi zaženi:

\`\`\`bash"
    for g in "${gen[@]}"; do
        notes+="
python3 $rel$(basename "$g")"
    done
    notes+="
\`\`\`

Testi nastanejo v mapah \`${rel}testi*/\`."
fi
gh release edit "$naloga" -R "$REPO" --notes "$notes" > /dev/null

echo
echo "Povezave za prenos:"
for arh in "${arhivi[@]}"; do
    echo "  $url/$(basename "$arh")"
done
