# 🥷 Ninja CLI

### The Modern, AI-Powered Command Line Interface

Ninja CLI is a high-performance terminal assistant that bridges the gap between natural language and system execution. Powered by state-of-the-art LLMs, it allows you to build, manage, and automate your development workflow using simple conversational commands.

---

## 🚀 Key Features

- **Multi-Model Support**: Seamlessly switch between OpenAI, Gemini, and OpenRouter.
- **Intelligent Execution**: Translates your intent into safe, executable shell commands.
- **Advanced UI**: Features a "Gemini-inspired" aesthetic with real-time status spinners, progress bars, and syntax-highlighted panels.
- **Permission Logic**: Granular control over restricted commands with a session-wide "Always Allow" bypass for power users.
- **Custom Exit Logic**: Clean shutdown sequence with automated interrupt signals.

---

## 🛠️ Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`

### Setup

1. **Clone the repository**:

```bash
git clone https://github.com/your-username/ninja-cli.git
cd ninja-cli

```

2. **Install using uv**:
   (Fastest):

```bash
uv add ninjacli

```

2. **Install using pip**:

```bash
pip install ninjacli

```

---

## 📖 How to Use

### 1. Launching the AI

Simply type the following command from any directory:

```bash
ninjacli

```

### 2. Configuration

On the first run, Ninja CLI will guide you through:

- **Provider Selection**: Choose between OpenAI, Gemini, or OpenRouter.
- **API Key Setup**: Securely link your API key (stored in your local `.env`).

### 3. Interacting with the Agent

You can ask Ninja CLI to perform complex tasks such as:

- _"Create a new React project in a folder named 'dashboard' and install tailwind."_
- _"Read the content of main.py and tell me if there are any security risks."_
- _"Find all log files in this directory and delete those older than 7 days."_

### 4. Handling Restricted Commands

For safety, commands like `rm` or `sudo` trigger a confirmation prompt:

- **[y] Yes**: Execute this specific command once.
- **[n] No**: Skip this command.
- **[always] Always Allow**: Grants permission for all restricted commands for the remainder of the current session.

---

## ⌨️ Useful Shortcuts

| Action         | Command / Key                 |
| -------------- | ----------------------------- |
| **New Line**   | `SHIFT + ENTER`               |
| **Exit CLI**   | Type `exit`, `quit`, or `bye` |
| **Force Stop** | `CTRL + C` (Double press)     |
| **Select API** | Arrow Keys + `ENTER`          |

---

## 🛡️ Security Note

Ninja CLI performs a directory check on startup. It is highly recommended to run the CLI within a specific project directory rather than your system's root directory to prevent accidental file modifications.
