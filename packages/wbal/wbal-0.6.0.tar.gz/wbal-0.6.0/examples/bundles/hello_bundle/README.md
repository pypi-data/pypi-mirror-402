# hello_bundle

Minimal WandBSwarm-compatible WBAL agent bundle.

Validate/run:
```bash
wbal bundle validate --agent-dir examples/bundles/hello_bundle
wbal bundle run --agent-dir examples/bundles/hello_bundle --task-dir . --workspace-dir ./workspace
```

Requires:
- `run.sh` (required)
- `install.sh` (optional)

