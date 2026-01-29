# MS2Function

MS2Function provides MS2 spectrum annotation and metabolite set analysis powered by
MS2BioText models. Large model/data assets are hosted on Hugging Face Hub and are
downloaded automatically on first use.

## Install

```bash
pip install ms2function
```

Or for local development:

```bash
pip install -e .
```

## Assets (Hugging Face Hub)

Default asset repo: `cgxjdzz/ms2function-assets`

The package looks for the following files:

- `models/best_model.pth`
- `models/config.json`
- `data/hmdb_subsections_WITH_NAME.jsonl`
- `data/all_jsonl_embeddings.pt`

Environment overrides:

- `MS2FUNCTION_ASSET_DIR` (use local assets directory)
- `MS2FUNCTION_ASSET_REPO` (override HF repo id)
- `HUGGINGFACE_HUB_TOKEN` or `HF_TOKEN` (for private repos)

## Quickstart (single spectrum)

```python
from pathlib import Path
from MS2Function import run_single

json_input = {
    "peaks": [[100.1, 200.0], [150.2, 300.0]],
    "precursor_mz": 250.3,
}

result = run_single(json_input, project_root=Path(r"d:\NTU\MS2Function"))
print(result)
```

## Quickstart (metabolite set)

```python
from pathlib import Path
from MS2Function import run_set

result = run_set(
    r"d:\path\to\your.csv",
    project_root=Path(r"d:\NTU\MS2Function"),
)
print(result)
```
