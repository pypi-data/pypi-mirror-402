#!/bin/bash

SCRIPT_DIR=$(dirname $(readlink -f "$0"))

function launch_benchmark() {
    MODEL_NAME=$1
    MODEL_PATH=$2
    LOG_PATH=$3
    BACKEND=$4
    CHIP_NAME=$5
    NUM_GPUS=$6

    echo "Going to run benchmark for: "
    echo "-model: ${MODEL_NAME}"
    echo "-model path: ${MODEL_PATH}"
    echo "-log path: ${LOG_PATH}"
    echo "-backend: ${BACKEND}"
    echo "-chip name: ${CHIP_NAME}"
    echo "-num gpus: ${NUM_GPUS}"

    for bs in 2 4 8 16 32 64 96 128 160 192 224 256; do
        if [ $bs -le 4 ]; then
            num_prompts=500
        else
            num_prompts=1000
        fi

        for input_output in "1000 250" "2000 500" "4000 1000" "6000 1000"; do
            INPUT_TOKENS=$(echo $input_output | cut -d' ' -f1)
            OUTPUT_TOKENS=$(echo $input_output | cut -d' ' -f2)

            echo "Running BS: $bs, NUM PROMPTS: $num_prompts, INPUT_TOKENS: $INPUT_TOKENS, OUTPUT_TOKENS: $OUTPUT_TOKENS"

            python3 $SCRIPT_DIR/benchmark_serving.py \
                --backend vllm \
                --model ${MODEL_NAME} \
                --dataset-name random \
                --random-input-len ${INPUT_TOKENS} \
                --random-output-len ${OUTPUT_TOKENS} \
                --random-range-ratio 0.9 \
                --max-concurrent-requests ${bs} \
                --num-prompts ${num_prompts} \
                --tokenizer ${MODEL_PATH} &> $LOG_PATH/runlog_${bs}_${INPUT_TOKENS}_${OUTPUT_TOKENS}.log
        done
    done
}

launch_benchmark "$@"
