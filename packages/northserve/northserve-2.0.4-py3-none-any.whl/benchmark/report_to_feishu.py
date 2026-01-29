#! /usr/bin/env python3

import os
import argparse
import time
from feishu import Feishu

FIELD_TO_LOG_KEYWORDS = {
    '请求成功数': 'Successful requests',
    '总耗时': 'Benchmark duration',
    '总输入tokens数': 'Total input tokens',
    '总输出tokens数': 'Total generated tokens',
    '输入处理吞吐': 'Input token throughput',
    '输出处理吞吐': 'Output token throughput',
    '首token时延均值': 'Mean TTFT',
    '首token时延中位数': 'Median TTFT',
    '首token时延P99': 'P99 TTFT',
    '吐字时延均值': 'Mean TPOT',
    '吐字时延中位数': 'Median TPOT',
    '吐字时延P99': 'P99 TPOT',
    'token间时延均值': 'Mean ITL',
    'token间时延中位数': 'Median ITL',
    'token间时延P99': 'P99 ITL',
}

LOG_KEYWORDS_TO_FIELD = {v: k for k, v in FIELD_TO_LOG_KEYWORDS.items()}

class Report:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.common_metadata = {}
        self.records = []
        self._parse_log_metadata()

    def __len__(self):
        return len(self.records)

    def __iter__(self):
        for metadata in self.records:
            details = self._parse_single_runlog(metadata)
            payload = {**self.common_metadata, **metadata, **details}
            yield payload


    def _parse_single_runlog(self, metadata: dict):
        runlog_file = f'runlog_{metadata["batch_size"]}_{metadata["输入长度"]}_{metadata["输出长度"]}.log'
        runlog_path = os.path.join(self.log_path, runlog_file)
        with open(runlog_path, 'r') as f:
            runlog_content = f.read()

        details = {}
        last_100_lines = runlog_content.split('\n')[-100:]
        for line in last_100_lines:
            for keyword, field in LOG_KEYWORDS_TO_FIELD.items():
                if keyword in line:
                    value = line.split(':')[-1].strip()
                    details[field] = float(value)
                    break

        return details

    def _parse_log_metadata(self):
        path = os.path.join(self.log_path, 'run.log')
        with open(path, 'r') as f:
            log_content = f.read()

        self.records = []
        for line in log_content.split('\n'):
            if line.startswith('-model: '):
                self.common_metadata['模型名称'] = line.split(': ')[1]
            if line.startswith('-chip name:'):
                self.common_metadata['芯片类型'] = line.split(': ')[1]
            if line.startswith('-num gpus:'):
                self.common_metadata['芯片数量'] = int(line.split(': ')[1])
            if line.startswith('-backend:'):
                self.common_metadata['推理引擎'] = line.split(': ')[1]
            if line.startswith('Running BS:'):
                parts = line.split(', ')
                self.records.append({
                  'batch_size': int(parts[0].split(': ')[1]),
                  '输入长度': int(parts[2].split(': ')[1]),
                  '输出长度': int(parts[3].split(': ')[1])
                })

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--log-path", type=str, required=True)
    argparser.add_argument("--config-file", type=str, required=True)
    args = argparser.parse_args()

    report = Report(args.log_path)
    feishu = Feishu(args.config_file)

    for r in report:
        feishu.add_inference_record(r)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
