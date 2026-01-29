# PY DBMS — A Modern, Secure MySQL CLI Client

**Stable Release — v3.1.0**

PY DBMS is a modern, developer-focused command-line client for MySQL, built with Python.  
It provides a clean terminal UI, readable query output, powerful helper commands, and a robust export system—without sacrificing safety, clarity, or control.

Designed for developers who live in the terminal but want a more structured, reliable experience than the default MySQL CLI.

---

## Key Features

### 🏗️ Modular Architecture
- **Decoupled DB Connectors:** Connection logic is fully abstracted from the CLI core, enabling future support for additional engines (PostgreSQL, SQLite, etc.).
- **Internal Result Abstraction:** Query execution is cleanly separated from result representation and output/export logic.

### 📤 Query Export System (Stable)
- **Pluggable Export Manager:** Centralized export handling with strict validation and predictable UX.
- **CSV & JSON Support:** Export query results directly to `.csv` or `.json`.
- **Safe by Design:** Export failures (invalid format, empty result, I/O issues) never terminate the session.
- **Default Export Path:** Automatically creates an `exports/` directory when no path is provided.
- **Space-Safe Paths:** Quoted file paths with spaces are fully supported.

### 📊 Query Output Control
- **`--expand` Flag:** Expand query results inline to prevent column truncation.
- **Precedence-Aware Design:**
  - Query-level `--expand` overrides session configuration
  - Session configuration defines default behavior
- **Composable Flags:** `--expand` and `--export` work together in a single query.

### Terminal UX
- **Rich Interface:** Structured tables and panels for high readability.
- **Visual Feedback:** Color-coded status messages for success, warnings, and SQL errors.
- **Startup Dashboard:** ASCII banner and session summary on launch.

### Configuration & Control
- **Persistent Config (`config.json`):** Safely stored in an OS-appropriate runtime directory.
- **Session Config Layer:** Runtime-only overrides that reset on every launch.
- **Inline Query Flags:** Per-query behavior customization without mutating configuration.

### Security
- **Masked Credentials:** Secure password input at login.
- **Local-First:** Designed with safe defaults for development environments.
- **Zero Persistence:** Sensitive credentials are never stored on disk.

---

## Installation

### Prerequisites
- Python **3.10+**
- A running MySQL Server

### Install via pip
```bash
pip install py-dbms-cli 
```

### Usage

**1. Run from your terminal**
```bash
pydbms  
```

**2. When prompted, enter credentials to establish connection with MySQL**
You will be prompted for:
  - Host
  - Username
  - Password (masked)

**3. Begin querying**

Enter SQL commands as you normally would.  
Multi-line queries are supported and executed once terminated with ;.  

---

## Meta Commands

PY DBMS includes several helper commands, and helper flags for interactive usage:

| Command | Description |
|------|-----------|
| `.help` | Show all helper commands |
| `.databases` | List all databases |
| `.tables` | List tables in the current database |
| `.schema <table>` | Show CREATE TABLE definition |
| `.clear` | Clear the terminal screen |
| `.version` | Show build and version information |
| `.config` | Show persistent configuration |
| `.config set <section>.<key> <value>` | Update a config value |
| `.config reset <section>.<key>` | Reset a config value |
| `.session-config` | Show session-level configuration |
| `.session-config set <key> <value>` | Update session-only settings |
| `.session-config reset <key>` | Reset a session setting |
| `.exit` | Exit the CLI |


| Flag | Description |
|------|-----------|
| `--expand` | Expand the result of query to not truncate in-view at End Of Line (overrides the session-config) |
| `--export` | Export result of a query to save it |

**NOTE:** `--export` only implements {`csv`,`json`} as of v3.1.0  

---

## Roadmap

Planned future improvements include:

- [ ] pydbms profile: Integration of a Profile System for saved connections.

- [ ] Additional Export Formats : To be implemented later.

- [ ] Multi-Engine: Initial support for SQLite or PostgreSQL connectors.

- [ ] Query History: Implementation of persistent command history.

---

## Author

Anish Sethi  
B.Tech Computer Science & Engineering  
Delhi Technological University (Class of 2029)  

---

## License

This project is licensed under the BSD 3-Clause License.  
Visit the [BSD 3-Clause License page](https://opensource.org/license/bsd-3-clause) for more information.
