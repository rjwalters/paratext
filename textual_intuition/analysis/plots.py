"""Optional plotting helpers. The report works without matplotlib — these are
only invoked if the user explicitly requests plot output.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_per_class_bar(per_class: pd.DataFrame, field: str, out_path: str | Path) -> None:
    """Render a bar chart of `field` over variant classes."""
    import matplotlib.pyplot as plt

    if per_class.empty or field not in per_class.columns:
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    per_class[field].plot.bar(ax=ax)
    ax.set_title(f"{field} by variant_class")
    ax.set_ylabel(field)
    ax.set_xlabel("variant_class")
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
