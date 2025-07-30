📁 Custom_News_Flow_02_project/
│
├── .env
├── .gitignore
├── .python-version
├── main.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── scheduler.py
├── uv.lock
│
├── 📁 .venv/                # (virtual environment)
│
├── 📁 myagents/             # ✅ all agents and tools go here
│   ├── __init__.py
│   ├── mainagent.py        # 🧠 Orchestrates flow
│   ├── collectoragent.py   # 📰 Collects news
│   ├── summarizeragent.py  # 📝 Summarizes
│   ├── taggeragnet.py      # 🏷️ Tags topics
│   └── mytools.py          # 🛠️ All @function_tool tools live here
│
└── 📁 schemas/
    ├── __init__.py
    └── feed.py             # 📦 FeedInput & FeedOut schemas
