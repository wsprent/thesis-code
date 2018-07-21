#! /usr/bin/env bash


function usage () {
    echo "Usage:"
    echo "util/run-tests.sh [-t <per run timeout in minutes>] [-r < #repitions>] [-l <logfile>] [tests...]"
    echo "Default is 10 repetions with 10 minute timeout"
    echo "Timings will be placed in ./timings"
    echo
    echo "Be the root folder of the repo"
    exit 2
}

if [[ ! -f "mtp/main.py" ]]; then
    echo "Error: \"mtp/main.py\" is not a file"
    usage
fi

args=`getopt ht:r:l: $*`
# you should not use `getopt abo: "$@"` since that would parse
# the arguments differently from what the set command below does.
if [[ $? != 0 ]]; then
    usage
    exit 2
fi

set -- $args

reps=10
timeout=$[10*60]
log=""

for i; do
    case "$i"
    in
        "-r")
            reps="$2"
            shift; shift;;
        "-t")
            timeout=$["$2"*60]
            shift; shift;;
        "-h")
            usage;;
        "-l")
            log="$2"
            shift; shift;;
        "--")
            shift
            break;;
    esac
done
extra_args=$(cat)
declare -a args_array
if [[ -z extra_args ]]; then
    args_array[0] = ""
else
    IFS=';' read -r -a args_array <<< "$extra_args"
fi

n=$[${#}*${#args_array[@]}]
echo "Running $n tests"
i=1
for stp in $@; do

    for extra_args in "${args_array[@]}"; do
        echo "Running test $i out of $n"
        cmd="mtp/main.py -r $reps -l $timeout -t ./timings $stp"

        if [[ ! -z $extra_args ]]; then
            cmd="$cmd $extra_args"
        fi
        echo $cmd

        if [[ -z $log ]]; then
            $cmd
        else
            $cmd &> $log
        fi

        if [[ $? != 0 ]]; then
            echo "Something went wrong with running $stp"
            exit 1
        fi
        let "i++"
    done
done
