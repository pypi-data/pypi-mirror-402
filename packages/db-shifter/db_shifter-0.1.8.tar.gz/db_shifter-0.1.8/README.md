# **db-shifter**  

**_Because someone switched your DB URL again._**

---

### 👶 Did your intern point production to the wrong DB?  

### 🤡 Did your devops team swear "nothing changed" before disappearing?  

### 🔥 Did your CTO say "just restore from backup" like you weren't already stressed?  

Yeah. We've all been there.

Welcome to **`db-shifter`** — a smart tool that intelligently migrates data from your old PostgreSQL database to your new one, copying only the missing rows.

No overwrites. No full `pg_dump` restores. Just precise, calculated migration that preserves your existing data.

---

## ⚡ Why?

When database connections get misconfigured or you need to migrate specific data between environments, manual table-by-table copying is tedious and error-prone.  
`db-shifter` automates the process of **copying missing data table-by-table** while respecting your existing records and foreign key relationships.

---

## 🧰 Features

- ✅ Auto-detects all tables in `public` schema  
- ✅ Automatically finds primary keys  
- ✅ Copies only rows **missing** in the new DB  
- ✅ Skips duplicates (preserves your existing data)  

- ✅ **Column-based sync** — specify exactly which columns to sync
- ✅ **Circular FK handling** — automatically detects and handles circular foreign key dependencies
- ✅ Smart sync order optimization based on FK relationships
- ✅ Handles foreign key constraints intelligently — no more FK violation errors

---

## 💾 Installation

```bash
pip install db-shifter
```

Or install from source:

```bash
git clone https://github.com/goodness5/db-shifter.git
cd db-shifter
pip install -e .
```

---

## 🚀 Usage

### Sync Mode (Default)

#### Basic Sync
```bash
db-shifter --old-db-url postgresql://user:pass@oldhost/db --new-db-url postgresql://user:pass@newhost/db
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

This will:
- Insert missing rows (as usual)
- Compare column values for rows that exist in both databases
- Update rows where column values differ

### Insert Mode (New!)

Insert records directly into a database table. Perfect for adding people, records, or any data.

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

## 🧨 Command-line options

| Flag              | What it does                          |
|------------------|----------------------------------------|
| `--dry-run`       | Simulate the transfer, no data is hurt |
| `--verbose`       | Prints detailed logs of every row      |
| `--table users`   | Sync just one table |
| `--skip-fk`       | Ignores foreign key errors             |
| `--columns id,name,email` | Sync only specified columns (comma-separated). Primary key is always included. |
| `--deep-check`    | Deep check: compare column values for existing rows and update differences |

### Insert Mode Options

| Flag              | What it does                          |
|------------------|----------------------------------------|
| `--db-url`       | Database connection string (required) |
| `--table`        | Table name to insert into (required) |
| `--data`         | JSON data (object or array) or path to JSON/CSV file |
| `--file`         | Path to JSON or CSV file |
| `--dry-run`      | Simulate the insert, no data is changed |
| `--verbose`       | Print detailed logs of every record |
| `--skip-fk`       | Ignore foreign key errors |
| `--on-conflict`   | What to do on primary key conflict: `ignore`, `update`, or `error` (default) |

---

## 🧠 How It Works

1. Connects to both databases  
2. Lists all public tables  
3. Identifies primary keys for each table  
4. Pulls rows missing from the new database  
5. Inserts them without overwriting existing rows

---

## ⚠️ Caution

- Requires **primary keys** on tables you want to sync  
- Circular FK dependencies are now detected and handled, but you may need to manually re-add FK constraints after sync
- Large databases may take time to sync — be patient  
- **Always backup your databases before syncing** — safety first!

---

## 🔄 Circular Foreign Key Handling

When `db-shifter` detects circular foreign key dependencies (e.g., Table A → Table B → Table A), it will:

1. **Detect the cycle** and warn you about it
2. **Temporarily disable FK constraints** for tables in the cycle during sync
3. **Sync all data** without FK constraint violations
4. **Note**: You may need to manually re-add FK constraints after sync completes

Example output:
```
⚠️  Circular foreign key dependencies detected:
   Cycle 1: users → profiles → users
   🔄 Will sync these tables in multiple passes with FK constraint handling
```

---

## ✨ Coming Soon

- Timestamp-based syncing (`created_at` support)  
- GUI interface for easier data management

---

## 🪦 Contributing

Found a bug? Great!  
Fix it, submit a PR, and help make `db-shifter` better for everyone.

---

## 📜 License

MIT. Do whatever the f**k you want. Just don’t call me if you drop prod again.
