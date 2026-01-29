# DimeAI

DIMEFIL Analyst CLI - AI-powered geopolitical event analysis.

## Installation

```bash
cd dimeai
uv pip install -e .
```

## Quick Start

```bash
# Collect articles about a situation
dimeai collect "South China Sea tensions 2024" -n 20

# Extract entities and relationships
dimeai extract -i articles -o graph.json

# Train TGN model
dimeai train -g graph.json -o model.pt

# Analyze a situation
dimeai analyze "China coast guard incident" -m model.pt -g graph.json

# Interactive session
dimeai interactive -g graph.json

# Run benchmarks
dimeai benchmark -g graph.json
```

## Commands

| Command | Description |
|---------|-------------|
| `collect` | Collect articles via web scraping |
| `extract` | Extract entities with GLiNER 2 |
| `train` | Train TGN model |
| `analyze` | Analyze a situation |
| `simulate` | Interactive what-if simulation |
| `interactive` | REPL for graph exploration |
| `benchmark` | Compare TGN vs baselines |
| `features compute` | Compute semantic features |
| `features inspect` | Inspect node features |
| `config show` | Show configuration |
| `config set` | Set configuration value |
| `dossier list` | List investigation dossiers |
| `dossier create` | Create new dossier |
| `dossier show` | Show dossier details |
| `dossier open` | Interactive dossier session |
| `dossier collect` | Add articles to dossier |
| `dossier export` | Export dossier as graph |
| `dossier note` | Add analyst note |
| `dossier delete` | Delete dossier |

## Dossier System

Dossiers are persistent investigation sessions stored in SQLite (`~/.dimeai/dossiers.db`).

```bash
# Create a new dossier
dimeai dossier create "SCS Tensions 2024" -d "Investigating recent incidents"

# Collect articles (uses DuckDuckGo search)
dimeai dossier collect 1 "Philippines coast guard incident" -n 5

# Open interactive session
dimeai dossier open 1

# In session:
#   collect <query>  - Search and add articles
#   extract          - Extract entities from articles
#   articles         - List collected articles
#   entities         - List extracted entities
#   events           - List events
#   note <text>      - Add observation
#   hypothesis <text> - Add hypothesis
#   analyze          - Analyze patterns
#   export           - Export as graph JSON
#   quit             - Exit session

# Export dossier
dimeai dossier export 1 -o my_investigation.json
```

## DIMEFIL Framework

- **D**iplomatic - Protests, talks, negotiations
- **I**nformation - Propaganda, disinformation
- **M**ilitary - Exercises, deployments
- **E**conomic - Fishing, trade, sanctions
- **F**inancial - (not yet implemented)
- **I**ntelligence - (not yet implemented)
- **L**aw Enforcement - Coast guard, patrols

## Model Performance

| Model | Accuracy | Macro F1 | vs Random F1 |
|-------|----------|----------|--------------|
| Random | 16.0% | 14.1% | - |
| Majority | 20.1% | 5.6% | -8.5pp |
| **TGN** | **28.7%** | **20.9%** | **+6.9pp** |

TGN beats both baselines on Macro F1 (the right metric for imbalanced data).
Class-weighted loss helps the model learn rare classes (diplomatic, information).

## Limitations

1. **Low absolute accuracy** - 26.6% on 7-class problem
2. **Class imbalance** - legal (36%), law_enforcement (13%)
3. **Temporal patterns** - Response patterns show 79% law_enforcement → law_enforcement
4. **Graph heuristics** - Agent uses heuristics, not neural predictions

## Development

```bash
# Run tests
python -m pytest dimeai/tests/ -v

# Run property-based tests
python -m pytest dimeai/tests/test_properties.py -v
```
