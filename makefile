CONFIGS="--max-cuts 10; --max-cuts 150; ; --no-heuristics;"
OPTS="-r 10 -t 5 -l bench.log"

benchmarks:
	echo $(CONFIGS) | util/run-tests.sh $(OPTS) data/tests/JMP-40/* data/tests/JMP-70/* data/tests/JMP-100/*
