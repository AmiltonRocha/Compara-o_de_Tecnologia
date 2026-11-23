#!/usr/bin/env python3
"""Gera gráficos (PNG) a partir de results/results.csv.

Gráficos:
  - rps_por_tech.png        throughput por tecnologia (última concorrência de cada label)
  - p95_por_tech.png        latência p95 por tecnologia
  - rps_vs_concorrencia.png throughput x concorrência (linhas por label/tech)
  - p95_vs_concorrencia.png latência p95 x concorrência

Uso (a partir de load-tests/):
    ../python/.venv/bin/python plot.py
"""

from __future__ import annotations

import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "results", "results.csv")
OUT_DIR = os.path.join(HERE, "results")
TECHS = ["rest", "graphql", "soap", "grpc"]
COLORS = {"rest": "#4C78A8", "graphql": "#E45756", "soap": "#F58518", "grpc": "#54A24B"}


def load_rows() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["concurrency"] = int(row["concurrency"])
        row["requests"] = int(row["requests"])
        for field in ("rps", "p50_ms", "p95_ms", "p99_ms"):
            row[field] = float(row[field])
    return rows


def last_per_group(rows: list[dict], key_fields: list[str], metric: str) -> dict:
    latest: dict[tuple, dict] = {}
    for row in rows:
        key = tuple(row[field] for field in key_fields)
        # como o CSV é append-only, a última linha do grupo é a mais recente
        latest[key] = row
    return {key: row[metric] for key, row in latest.items()}


def bar_chart(
    rows: list[dict], metric: str, title: str, ylabel: str, filename: str
) -> None:
    labels = sorted({row["label"] for row in rows})
    latest = last_per_group(rows, ["label", "tech"], metric)
    max_conc = max(row["concurrency"] for row in rows)

    width = 0.8 / max(len(labels), 1)
    x_positions = range(len(TECHS))
    fig, ax = plt.subplots(figsize=(8, 5))
    for index, label in enumerate(labels):
        values = [latest.get((label, tech), 0.0) for tech in TECHS]
        offsets = [x + index * width for x in x_positions]
        bars = ax.bar(offsets, values, width=width, label=label)
        ax.bar_label(bars, fmt="%.1f", fontsize=8)

    ax.set_xticks([x + width * (len(labels) - 1) / 2 for x in x_positions])
    ax.set_xticklabels(TECHS)
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title}\n(concorrência mais recente <= {max_conc})")
    ax.legend(title="implementação")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  {filename}")


def line_chart(rows: list[dict], metric: str, title: str, ylabel: str, filename: str) -> None:
    labels = sorted({row["label"] for row in rows})
    fig, ax = plt.subplots(figsize=(9, 5))
    for label in labels:
        for tech in TECHS:
            series = sorted(
                (row for row in rows if row["label"] == label and row["tech"] == tech),
                key=lambda row: row["concurrency"],
            )
            if not series:
                continue
            xs = [row["concurrency"] for row in series]
            ys = [row[metric] for row in series]
            ax.plot(
                xs,
                ys,
                marker="o",
                color=COLORS[tech],
                linestyle="-" if label == labels[0] else "--",
                label=f"{tech} ({label})",
            )

    ax.set_xscale("log")
    ax.set_xticks(sorted({row["concurrency"] for row in rows}))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("concorrência")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  {filename}")


def main() -> None:
    if not os.path.exists(CSV_PATH):
        raise SystemExit(f"CSV não encontrado: {CSV_PATH}\nRode bench.py ou run_matrix.sh primeiro.")
    rows = load_rows()
    if not rows:
        raise SystemExit("CSV vazio.")

    print("Gráficos gerados em results/:")
    bar_chart(rows, "rps", "Throughput por tecnologia", "requisições/segundo", "rps_por_tech.png")
    bar_chart(rows, "p95_ms", "Latência p95 por tecnologia", "p95 (ms)", "p95_por_tech.png")
    if len({row["concurrency"] for row in rows}) > 1:
        line_chart(
            rows,
            "rps",
            "Throughput x concorrência",
            "requisições/segundo",
            "rps_vs_concorrencia.png",
        )
        line_chart(
            rows,
            "p95_ms",
            "Latência p95 x concorrência",
            "p95 (ms)",
            "p95_vs_concorrencia.png",
        )


if __name__ == "__main__":
    main()
