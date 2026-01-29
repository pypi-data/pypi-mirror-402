export https_proxy=http://10.51.6.1:7890
export http_proxy=http://10.51.6.1:7890

# install what you need

unset https_proxy
unset http_proxy

python3 -m sglang.launch_server --model-path=/gpfs/users/zhouenyu/r1_sft/converted_ckpts_v3/sft-qwen2a5-7b-math-base-enyu-20250402-v3-aops-dedup-13w-5e5-0/iter_0006369_HF \
    --tp-size=1 \
     --max-running-requests=256 \
     --cuda-graph-max-bs=256 \
     --max-total-tokens=131072 \
     --enable-mixed-chunk \
     --enable-metrics --port=8000 --host=0.0.0.0 \
     --served-model-name=tianboyu-check-host-network-sglang 2>&1 | tee -a /var/log/vllm.log
