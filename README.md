markdown


<p align="center">
  <img src="docs/logo.png" alt="Sentinal logo" width="200"/>
  <br>
  <strong>AI-ready system guardian for 1 GB laptops</strong>
  <br>
  <code>pip install sentinal</code> → <code>sentinal health</code>
</p>
<p align="center">
  <a href="https://pypi.org/project/sentinal/"><img src="https://img.shields.io/pypi/v/sentinal?style=flat-square" alt="PyPI"/></a>
  <a href="https://github.com/you/sentinal/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License"/></a>
  <a href="https://github.com/you/sentinal/actions"><img src="https://github.com/you/sentinal/workflows/Tests/badge.svg?style=flat-square" alt="Tests"/></a>
</p>
---
## What is Sentinal?
Sentinal is a **single-command**, **AI-ready** system administration CLI that stays under **1 GB RAM** even with all extras loaded.  
Designed for MX-Linux, Debian, and friends — but works **anywhere** Python 3.9+ and `psutil` run.
> Think of it as `htop` + `ncdu` + `lsof` + **AI advisor** + **safe cleanup** in one **tiny** package.
---
## ⚡ One-liner Install
```bash
python3 -m pip install --user sentinal
sentinal health
📊 SQLite Inside — Query Your System Like a Database
Sentinal logs two tables into ~/.sentinal/history.db:

1. metrics — health history
Column	Type	Description
ts	int	epoch sec
cpu	real	CPU %
mem	real	RAM %
disk	real	root %
2. files — directory/file index (no contents)
Column	Type	Description
ts	int	epoch sec
path	text	absolute
is_dir	int	1=directory
size_bytes	int	file size
Example queries:

sql


-- CPU spikes in last 24 h
SELECT datetime(ts,'unixepoch','localtime') as time, cpu
FROM metrics
WHERE ts > strftime('%s','now','-1 day')
ORDER BY ts;
-- Top 20 newest files > 100 MB
SELECT path, size_bytes/1e6 as MB
FROM files
WHERE is_dir = 0 AND size_bytes > 100*1024*1024
ORDER BY ts DESC
LIMIT 20;
🔧 CLI in 30 Seconds
bash


sentinal health --json --spark          # live stats + sparkline
sentinal clean --force                  # delete .tmp/.log/etc
sentinal lint main.py                  # AST + regex audit
sentinal kill-top 3 --force            # SIGTERM memory hogs (safe whitelist)
sentinal audit ~/projects              # key-file permission check
sentinal --gpu                         # NVIDIA util/mem
sentinal --metrics 9101                # Prometheus export
sentinal --ask-local "why is my RAM high?"  # 3B llama-cpp (850 MB)
sentinal --trace-io 60                 # eBPF block-I/O trace (spawns new terminal)
sentinal --index-tree /media/extra     # index path into SQLite
Long-running tasks spawn a new terminal with SENTRY_AI_DISABLED=1 to keep memory low.

🧠 Optional Features Table
Feature	Flag	Needs (one-liner)	Peak RAM
GPU telemetry	--gpu	pip install pynvml	~5 MB
Local 3B LLM	--ask-local	Download GGUF + llama-cpp-python	~850 MB
Prometheus	--metrics	pip install prometheus-client	~10 MB
eBPF tracing	--trace-io	apt install bcc-tools python3-bcc	~60 MB
Index tree	--index-tree	—	—
All heavy commands spawn a new terminal to avoid blocking your shell.

🤖 ADK Integration
Sentinal can integrate with a local ADK (Agent Development Kit) server to provide more advanced AI capabilities. This allows you to offload more complex questions to a dedicated AI agent.

**Setup:**
1.  Install the `google-adk`: `pip install google-adk`
2.  Start the ADK server: `adk-server`

**Usage:**
```bash
sentinal adk "your question here"
```

🛡️ Safety by Design
DRY-RUN default — destructive actions require --force
Process whitelist (systemd, Xorg, etc.) — never auto-killed
Key-file permission audit warns on ≠ 600/400
No sudo calls inside the tool
All AI features are opt-in and can be disabled per terminal
🧪 Testing
bash


git clone https://github.com/you/sentinal
cd sentinal
pip install -e .[dev]
pytest
Covers:

lint detection on sample files
clean DRY-run correctness
kill-top dry-run with mocked psutil
Contributing
Fork & clone
Create a feature branch
Add tests → pytest -v
Open a PR
License
MIT © Your Name

Enjoy Sentinal — your AI-ready, 1 GB-friendly system guardian.
