## 配置文件命名规则
配置文件统一使用 `{lower(engine)}_{lower(protocol)}_{lower(scenario)}.yaml` 描述。

例如使用 `vLLM` 引擎的 `OpenAI` 协议，在 `generation` 场景下启动服务的命令配置，就是 `vllm_openai_generation.yaml` 文件。

这个文件只是当做base config，可以通过启动命令中的 `--extra-cmds` 和 `--extra-envs` 追加。
注意：**目前仅支持追加，不支持覆盖和替换。**

## 配置文件内容
配置文件中有4部分内容，都是必填内容，具体包括：
- image: 字符串，引擎对应的镜像名称
- cmd: 字符串数组，用于拼接最终引擎启动命令的数组，将使用空格做拼接后替换到最终的启动命令中
- livenessPath: 用于活性检查的http url相对路径，如 `/health`
- readinessPath: 用于服务健康检查的http url相对路径，如 `/list`
