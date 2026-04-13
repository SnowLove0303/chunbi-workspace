# lobster Workflow 完整指南

## 标准结构

```yaml
name: <任务名>
description: <描述>
settings:
  max_retries: 3
  retry_delay: 5
  checkpoint_dir: ./checkpoints
  on_failure: abort_and_notify
variables:
  target_url: "https://www.example.com"
steps:
  # 端口预检
  - id: pre_check
    run: python check_ports.py
    on_error: abort

  # 导航
  - id: navigate
    run: playwright navigate ${target_url}
    verify: screenshots/navigate.png

  # 三维验证
  - id: verify_navigate
    run: python verify_step.py --step navigate
         --expected-url "\${target_url}"
         --timeout-ms 5000
    on_error: abort

  # 操作
  - id: click
    run: playwright click \"\${selector}\"
    verify: screenshots/click.png

  # 数据提取
  - id: extract
    run: python extract_data.py
    stdin: \$click.stdout
    always_run: true
```

## 关键特性

| 特性 | 用途 |
|------|------|
| `verify:` | 每步截图留存，可审计 |
| `checkpoint:` | 状态持久化，失败可恢复 |
| `on_error: abort/continue` | 错误控制 |
| `always_run: true` | 清理/保存总是执行 |
| `approval:` | 人工审批门 |
| `when:` | 条件执行 |
| `lobster graph --format mermaid` | 生成流程图 |

## 完整模板文件

实际 YAML 模板见：`scripts/browser-precision-workflow.yaml`
