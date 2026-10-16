#!/usr/bin/env bash
# Teče v GitHub Actions repoja s testi (workflow testi.yml, ki ga tja skopira
# orodja/deli.sh): zažene generatorje nalog in z orodja/izdaj.sh zapakira in
# naloži nastale mape testi* v release naloge.
#
#   Ob pushu se za vsako mapo naloge (src/<vaja>/<naloga>/) s spremembami
#   zaženejo spremenjeni gen*.py; če se je spremenilo kaj drugega (npr.
#   rešitev *_ai*.cpp), vsi gen*.py naloge. Pri ročnem zagonu
#   (workflow_dispatch) se zaženejo vsi gen*.py nalog v NALOGE oz. vseh nalog.
#
#   Spremenljivke (nastavi jih workflow): GITHUB_EVENT_NAME, PRED (commit pred
#   pushem), NALOGE (mape nalog, ločene s presledki), REPO, GH_TOKEN.

set -eu
cd "$(dirname "$0")/../.."
shopt -s nullglob

declare -A gen=()   # mapa naloge -> generatorji, ločeni s presledki; "*" = vsi
if [ "${GITHUB_EVENT_NAME:-}" = push ] && [[ ${PRED:-0} =~ [1-9a-f] ]]; then
    while read -r f; do
        [[ $f =~ ^(src/[^/]+/[^/]+)/([^/]+)$ ]] || continue
        d=${BASH_REMATCH[1]}; ime=${BASH_REMATCH[2]}
        [ -d "$d" ] || continue
        if [[ $ime == gen*.py ]]; then
            [ -f "$f" ] || continue                 # izbrisan generator
            [ "${gen[$d]:-}" = "*" ] || gen[$d]="${gen[$d]:-}$ime "
        else
            gen[$d]="*"
        fi
    done < <(git diff --name-only "$PRED" HEAD)
else
    # ročni zagon ali prvi push: vse naštete naloge oz. vse naloge z generatorjem
    naloge=(${NALOGE:-})
    if [ ${#naloge[@]} -eq 0 ]; then
        for g in src/*/*/gen*.py; do naloge+=("$(dirname "$g")"); done
    fi
    for d in "${naloge[@]}"; do gen[${d%/}]="*"; done
fi

if [ ${#gen[@]} -eq 0 ]; then
    echo "Nobena naloga se ni spremenila, ni kaj generirati."
    exit 0
fi

napake=0
for d in $(printf '%s\n' "${!gen[@]}" | sort); do
    if [ "${gen[$d]}" = "*" ]; then
        gens=("$d"/gen*.py)
    else
        gens=()
        for g in ${gen[$d]}; do gens+=("$d/$g"); done
    fi
    if [ ${#gens[@]} -eq 0 ]; then
        echo "::warning::$d nima generatorja gen*.py, preskakujem"
        continue
    fi

    # napaka pri eni nalogi ne ustavi ostalih; podlupina ne sme biti v pogoju
    # (if, ||), ker bash tam set -e ignorira
    set +e
    (
        set -e
        for g in "${gens[@]}"; do
            echo "::group::$g"
            start=$(date +%s)
            python3 "$g"
            echo "($g: $(( $(date +%s) - start )) s)"
            echo "::endgroup::"
        done
        echo "::group::izdaj $d"
        bash orodja/izdaj.sh "$d"
        echo "::endgroup::"
    )
    status=$?
    set -e
    if [ $status -ne 0 ]; then
        echo "::endgroup::"
        echo "::error::Napaka pri nalogi $d, release ni posodobljen"
        napake=1
    fi
done
exit $napake
