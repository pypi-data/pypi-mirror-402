<div align="center">

# **db-shifter**  

**_Because someone switched your DB URL again._**

[![PyPI version](https://badge.fury.io/py/db-shifter.svg)](https://badge.fury.io/py/db-shifter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)

</div>

---

<div align="center">

**Did your intern point production to the wrong DB?**  
**Did your devops team swear "nothing changed" before disappearing?**  
**Did your CTO say "just restore from backup" like you weren't already stressed?**

Yeah. We've all been there.

</div>

---

Welcome to **`db-shifter`** — the script that digs through your old PostgreSQL database and copies only the missing rows into your new one. Oh, it also syncs columns too — just add the `--deep-check` flag.

> **No overwrites. No dumb `pg_dump` restores. Just calculated migration that doesn't wreck your existing data.**

---

## <span style="color:rgb(6, 40, 151)">Why?</span>

Because your CTO is a clown.  
Because your devops team "accidentally" pointed production at the wrong database.  
Because you need to **copy missing data table-by-table** and you're too busy to do it manually.

`db-shifter` handles the grunt work while you figure out who to blame.

---

## <span style="color: #4ecdc4">Features</span>

### Core Functionality
- ✅ **Auto-detects** all tables in `public` schema  
- ✅ **Finds primary keys** automatically  
- ✅ **Copies only missing rows** in the new DB  
- ✅ **Skips duplicates** (doesn't ruin your existing data)  

### Advanced Features
- 🔧 **Column-based sync** — specify exactly which columns to sync
- 🔄 **Circular FK handling** — automatically detects and handles circular foreign key dependencies
- 🧠 **Smart sync order** optimization based on FK relationships
- 🛡️ **FK constraint handling** — no more FK violation errors

---

## <span style="color: #95e1d3">Installation</span>

### Quick Install

```bash
pip install db-shifter
```

### From Source

```bash
git clone https://github.com/goodness5/db-shifter.git
cd db-shifter
pip install -e .
```

---

## <span style="color: #f38181">Usage</span>

### Sync Mode (Default)

#### Basic Sync
```bash
db-shifter --old-db-url postgresql://user:pass@oldhost/db \
           --new-db-url postgresql://user:pass@newhost/db
```

#### Column-based Sync
Sync only specific columns (useful when schemas differ):
```bash
db-shifter --old-db-url postgresql://user:pass@oldhost/db \
           --new-db-url postgresql://user:pass@newhost/db \
           --columns id,name,email,created_at
```

#### Single Table Sync
```bash
db-shifter --old-db-url postgresql://user:pass@oldhost/db \
           --new-db-url postgresql://user:pass@newhost/db \
           --table users
```

#### Deep Check Mode
Compare and update column values for existing rows (not just insert missing rows):
```bash
db-shifter --old-db-url postgresql://user:pass@oldhost/db \
           --new-db-url postgresql://user:pass@newhost/db \
           --deep-check
```

**This will:**
- Insert missing rows (as usual)
- Compare column values for rows that exist in both databases
- Update rows where column values differ

---

### Insert Mode

Insert records directly into a database table. Perfect for adding data without writing SQL.

#### Insert from JSON String
```bash
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --data '{"name":"John Doe","email":"john@example.com","age":30}'
```

#### Insert Multiple Records from JSON
```bash
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --data '[{"name":"John","email":"john@example.com"},{"name":"Jane","email":"jane@example.com"}]'
```

#### Insert from JSON File
```bash
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --file data.json
```

#### Insert from CSV File
```bash
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --file data.csv
```

#### Handle Conflicts Gracefully
```bash
# Ignore conflicts (skip duplicate records)
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --file data.json \
           --on-conflict ignore

# Update on conflict (upsert)
db-shifter --db-url postgresql://user:pass@host/db \
           --table users \
           --file data.json \
           --on-conflict update
```

---

## <span style="color: #a8e6cf">Command-line Options</span>

### Sync Mode Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Simulate the transfer, no data is hurt |
| `--verbose` | Prints detailed logs of every row |
| `--table <name>` | Sync just one table |
| `--skip-fk` | Ignores foreign key errors |
| `--columns <list>` | Sync only specified columns (comma-separated). Primary key is always included. |
| `--deep-check` | Deep check: compare column values for existing rows and update differences |

### Insert Mode Options

| Flag | Description |
|------|-------------|
| `--db-url` | Database connection string (required) |
| `--table` | Table name to insert into (required) |
| `--data` | JSON data (object or array) or path to JSON/CSV file |
| `--file` | Path to JSON or CSV file |
| `--dry-run` | Simulate the insert, no data is changed |
| `--verbose` | Print detailed logs of every record |
| `--skip-fk` | Ignore foreign key errors |
| `--on-conflict` | What to do on primary key conflict: `ignore`, `update`, or `error` (default) |

---

## <span style="color: #ffd93d">How It Works</span>

```
1. Connects to both databases
2. Lists all public tables
3. Checks the primary keys
4. Pulls rows missing from the new database
5. Inserts them without wrecking existing rows
```

---

## <span style="color: #ff6b6b">⚠️ Caution</span>

> **Important Notes:**
> - Assumes **you have primary keys** (don't be a barbarian)  
> - Circular FK dependencies are detected and handled, but you may need to manually re-add FK constraints after sync
> - If you're syncing 50GB of data, don't cry when it takes time  
> - **Backups are your friend. Don't be dumb.**

---

## <span style="color: #6c5ce7">Circular Foreign Key Handling</span>

When `db-shifter` detects circular foreign key dependencies (e.g., Table A → Table B → Table A), it will:

1. **Detect the cycle** and warn you about it
2. **Temporarily disable FK constraints** for tables in the cycle during sync
3. **Sync all data** without FK constraint violations
4. **Note**: You may need to manually re-add FK constraints after sync completes

**Example output:**
```
Circular foreign key dependencies detected:
   Cycle 1: users → profiles → users
   Will sync these tables in multiple passes with FK constraint handling
```

---

## <span style="color: #a29bfe">Coming Soon</span>

- 🕐 Timestamp-based syncing (`created_at` support)  
- 🗄️ `.sqlite` → postgres sync
- 📦 `.bak` and json data support input
- 🖥️ GUI with a "FIX EVERYTHING" button (for product managers)

---

## <span style="color: #fd79a8">Contributing</span>

Found a bug? Good.  
Fix it, submit a PR, and don't drop your cashapp in the description.

---

<div align="center">

## <span style="color: #00b894">License</span>

**MIT.** Do whatever you want. Just don't call me if you drop prod again.

---

**Made with ❤️ (and frustration)**

[⬆ Back to Top](#db-shifter)

</div>
