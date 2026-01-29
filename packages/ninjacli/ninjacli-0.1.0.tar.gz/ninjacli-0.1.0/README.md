ninjacli/
│
├── src/
│ └── ninjacli/
│ ├── **init**.py
│ ├── main.py # CLI entry point
│ │
│ ├── cli/
│ │ ├── commands/ # explain, generate, refactor, chat
│ │ ├── interactive.py # REPL mode
│ │ └── router.py # command dispatcher
│ │
│ ├── ai/
│ │ ├── client.py # AI API abstraction
│ │ ├── prompts.py # system + task prompts
│ │ └── models.py # provider config
│ │
│ ├── config/
│ │ ├── loader.py # load/save config
│ │ └── schema.py # config structure
│ │
│ ├── ui/
│ │ ├── theme.py # colors, styles
│ │ ├── printer.py # success/error/info
│ │ └── logo.py
│ │
│ ├── core/
│ │ ├── context.py # project context
│ │ ├── files.py # file reading
│ │ └── history.py # conversation memory
│ │
│ └── utils/
│ └── validators.py
│
├── pyproject.toml # UV-managed
├── README.md
├── LICENSE
└── .gitignore
