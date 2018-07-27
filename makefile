CONFIGS="--max-cuts 0 --no-heuristics; --max-cuts 1 --no-heuristics; --max-cuts 25 --no-heuristics; ; --no-heuristics --strengthen"
OPTS="-r 5 -t 5 -l bench.log"

benchmarks:
	echo $(CONFIGS) | util/run-tests.sh $(OPTS) data/tests/JMP-60/* data/tests/JMP-80/*
