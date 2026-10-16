
# Splošen Makefile za mape testi/ (osnova je šolski Makefile, npr. za inverzije).
# gen.py ga skopira v svojo mapo testi/ kot Makefile, zato je mapa samostojna.
#
# Razlike od šolskega:
#   - Če je v tej mapi checker.awk (naloge z več pravilnimi odgovori), izhod
#     preveri on:  awk -f checker.awk test.in test.out test.res
#     (izhodna koda 0 = pravilno, izpis gre v test*.diff). Sicer se izhod
#     primerja z diff kot v šolskem Makefile-u.
#   - ${name}.cpp je lahko v tej mapi ali v mapi naloge (eno višje).
#
# Pred poganjanjem programa make:
#     export name=<ime_datoteke_brez_koncnice>
#
# Prevajanje:
#     make
#
# Testiranje:
#     make test [neobvezni parametri]
#
#     Neobvezni parametri:
#         T: "casovna omejitev v sekundah (privzeto = 1)
#         M: za vsak testni primer izpi"si "cas izvajanja (1: da; 0: ne; privzeto = 0)
#         P: obseg testnih primerov, ki naj se obravnava (npr. 3-5 ali 7 ali 2- ali -6 ali -; privzeto = -)
#
#     Primeri:
#         make test
#         make test P=4-7
#         make test T=3
#         make test T=2 M=1 P=6-

CC = g++
CFLAGS = -std=c++17
LIBS = -lm

T = 5
M = 0
P = '-'

DIFF_TIMEOUT = 0.5

CHECKER = $(wildcard checker.awk)

vpath %.cpp ..

TIMEOUT_SIGNAL = 124
SHELL = /bin/bash
OK_STRING=\033[1;32mOK\033[0;38m
FAILED_STRING=\033[1;31mfailed\033[0;38m
TIMEOUT_STRING=\033[1;35mtimeout\033[0;38m

${name} : ${name}.cpp
	@echo "=== COMPILING: ==="
	${CC} ${CFLAGS} -o $@ $< ${LIBS}

test : ${name}
	@echo "=== TESTING: ==="; \
	singleTestFile=$$(ls -1 test*.in | head -1); \
	\
	testNumberLength=$$(( $${#singleTestFile} - 7 )); \
	cutParameter=$$((5 + testNumberLength - 1)); \
	nTests=$$(ls -1 test*.in | cut -c5-$$cutParameter | sort | tail -1); \
	firstTest=$$(echo $$P | cut -d'-' -f1); \
	lastTest=$$(echo $$P | cut -d'-' -f2); \
	if [[ -z $$firstTest ]]; then \
		firstTest=1; \
	fi; \
	if [[ -z $$lastTest ]]; then \
		lastTest=$$nTests; \
	fi; \
	\
	nPassedTests=0; \
	nConsideredTests=0; \
	\
	trap exit SIGINT; \
	\
	timeoutValue=${T}; \
	hardTimeoutValue=$$((timeoutValue + 2)); \
	\
	for i0 in $$(seq $$firstTest $$lastTest); do \
		i=$$(printf %0$${testNumberLength}d $$i0); \
		startTime=$$(date +%s.%N); \
		timeout -k $${hardTimeoutValue} $${timeoutValue} ./${name} < test$$i.in > test$$i.res 2> /dev/null; \
		result=$$?; \
		endTime=$$(date +%s.%N); \
		if [[ $$result == ${TIMEOUT_SIGNAL} ]]; then \
			if [[ ${M} = 1 ]]; then \
				echo -e "test$$i -- ${TIMEOUT_STRING}  [> $${timeoutValue} s]"; \
			else \
				echo -e "test$$i -- ${TIMEOUT_STRING}"; \
			fi; \
		else \
			timeDifference=$$(echo "scale=2; ($${endTime} - $${startTime}) / 1.00" | bc); \
			measuredTimeString=""; \
			if [[ ${M} = 1 ]]; then \
				measuredTimeString=" [$$timeDifference s]"; \
			fi; \
			if [[ -n "${CHECKER}" ]]; then \
				awk -f ${CHECKER} test$$i.in test$$i.out test$$i.res > test$$i.diff 2>&1; \
				result=$$?; \
			else \
				timeout -k ${DIFF_TIMEOUT} ${DIFF_TIMEOUT} diff --ignore-trailing-space test$$i.res test$$i.out > test$$i.diff; \
				result=$$?; \
				if [[ $$result == ${TIMEOUT_SIGNAL} ]]; then \
					cmp test$$i.res test$$i.out > test$$i.diff; \
					result=$$?; \
				fi; \
			fi; \
			if [[ $$result == 0 ]]; then \
				echo -e "test$$i -- ${OK_STRING} $${measuredTimeString}"; \
				nPassedTests=$$((nPassedTests + 1)); \
			else \
				echo -e "test$$i -- ${FAILED_STRING} $${measuredTimeString}"; \
			fi \
		fi; \
		nConsideredTests=$$((nConsideredTests + 1)); \
	done; \
	echo "Result: $$nPassedTests / $$nConsideredTests"

clean :
	rm -fr ${name} test*.res test*.diff
