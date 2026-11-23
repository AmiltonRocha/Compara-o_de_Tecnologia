#!/usr/bin/env python3
"""Benchmark de carga comparando SOAP, REST, GraphQL e gRPC.

Executa uma carga mista (as 5 consultas obrigatórias do enunciado) contra um host
e mede throughput, latência (p50/p95/p99) e erros. Funciona tanto contra os
servidores Python quanto os TypeScript, pois os contratos são os mesmos.

Uso (a partir de load-tests/):
    ../python/.venv/bin/python bench.py --tech all --requests 1000 --concurrency 50
    ../python/.venv/bin/python bench.py --tech rest --requests 200 --concurrency 10

Saída: tabela no terminal + append em results/results.csv e results/scenarios.csv.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import random
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, "results")
PORTS = {"rest": 8000, "soap": 8001, "graphql": 8002, "grpc": 8003}

# ---------------------------------------------------------------- workloads
REST_SCENARIOS = [
    ("list_users", "/users"),
    ("list_musics", "/musics"),
    ("playlists_by_user", "/users/1/playlists"),
    ("musics_by_playlist", "/playlists/1/musics"),
    ("playlists_by_music", "/musics/2/playlists"),
]

GRAPHQL_QUERIES = [
    ("list_users", "{ users { id name email } }"),
    ("list_musics", "{ musics { id title artist } }"),
    ("playlists_by_user", "{ playlistsByUser(userId: 1) { id name } }"),
    ("musics_by_playlist", "{ musicsByPlaylist(playlistId: 1) { id title } }"),
    ("playlists_by_music", "{ playlistsByMusic(musicId: 2) { id name } }"),
]

SOAP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:tns="http://music.example.com/wsdl">
  <soapenv:Body><tns:{op}>{inner}</tns:{op}></soapenv:Body>
</soapenv:Envelope>"""

SOAP_SCENARIOS = [
    ("list_users", SOAP_TEMPLATE.format(op="ListUsers", inner="")),
    ("list_musics", SOAP_TEMPLATE.format(op="ListMusics", inner="")),
    (
        "playlists_by_user",
        SOAP_TEMPLATE.format(op="ListPlaylistsByUser", inner="<userId>1</userId>"),
    ),
    (
        "musics_by_playlist",
        SOAP_TEMPLATE.format(op="ListMusicsByPlaylist", inner="<playlistId>1</playlistId>"),
    ),
    (
        "playlists_by_music",
        SOAP_TEMPLATE.format(op="ListPlaylistsByMusic", inner="<musicId>2</musicId>"),
    ),
]

GRPC_SCENARIOS = [
    "list_users",
    "list_musics",
    "playlists_by_user",
    "musics_by_playlist",
    "playlists_by_music",
]


# ------------------------------------------------------------------- helpers
def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def make_grpc_stub(host: str):
    grpc_dir = os.path.join(os.path.dirname(HERE), "python", "grpc_api")
    sys.path.insert(0, grpc_dir)
    import grpc  # noqa: PLC0415

    import music_pb2_grpc as pb2_grpc  # noqa: PLC0415

    channel = grpc.aio.insecure_channel(f"{host}:{PORTS['grpc']}")
    return channel, pb2_grpc.MusicServiceStub(channel)


class Runner:
    def __init__(self, tech: str, host: str, client: httpx.AsyncClient, stub=None):
        self.tech = tech
        self.host = host
        self.client = client
        self.stub = stub
        self._import_grpc()

    @staticmethod
    def _import_grpc():
        for path in (os.path.join(os.path.dirname(HERE), "python", "grpc_api"),):
            if path not in sys.path:
                sys.path.insert(0, path)

    def scenarios(self) -> list[str]:
        if self.tech == "rest":
            return [name for name, _ in REST_SCENARIOS]
        if self.tech == "soap":
            return [name for name, _ in SOAP_SCENARIOS]
        if self.tech == "graphql":
            return [name for name, _ in GRAPHQL_QUERIES]
        return GRPC_SCENARIOS

    async def call(self, scenario: str) -> None:
        if self.tech == "rest":
            path = dict(REST_SCENARIOS)[scenario]
            response = await self.client.get(
                f"http://{self.host}:{PORTS['rest']}{path}"
            )
            response.raise_for_status()
            return

        if self.tech == "graphql":
            query = dict(GRAPHQL_QUERIES)[scenario]
            response = await self.client.post(
                f"http://{self.host}:{PORTS['graphql']}/graphql",
                json={"query": query},
            )
            response.raise_for_status()
            if "data" not in response.json():
                raise RuntimeError("resposta GraphQL sem data")
            return

        if self.tech == "soap":
            envelope = dict(SOAP_SCENARIOS)[scenario]
            response = await self.client.post(
                f"http://{self.host}:{PORTS['soap']}/",
                content=envelope.encode("utf-8"),
                headers={"Content-Type": "text/xml; charset=utf-8"},
            )
            response.raise_for_status()
            if b"Envelope" not in response.content:
                raise RuntimeError("resposta SOAP inválida")
            return

        # gRPC
        import music_pb2 as pb2  # noqa: PLC0415

        if scenario == "list_users":
            await self.stub.ListUsers(pb2.Empty())
        elif scenario == "list_musics":
            await self.stub.ListMusics(pb2.Empty())
        elif scenario == "playlists_by_user":
            await self.stub.ListPlaylistsByUser(pb2.IdRequest(id=1))
        elif scenario == "musics_by_playlist":
            await self.stub.ListMusicsByPlaylist(pb2.IdRequest(id=1))
        else:
            await self.stub.ListPlaylistsByMusic(pb2.IdRequest(id=2))


async def run_load(
    runner: Runner,
    total: int,
    concurrency: int,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    names = runner.scenarios()
    queue: asyncio.Queue[str] = asyncio.Queue()
    for _ in range(total):
        queue.put_nowait(rng.choice(names))

    latencies: dict[str, list[float]] = {name: [] for name in names}
    errors: dict[str, int] = {name: 0 for name in names}
    error_samples: list[str] = []

    async def worker() -> None:
        while True:
            try:
                scenario = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            started = time.perf_counter()
            try:
                await runner.call(scenario)
                latencies[scenario].append((time.perf_counter() - started) * 1000)
            except Exception as exc:  # noqa: BLE001
                errors[scenario] += 1
                if len(error_samples) < 5:
                    error_samples.append(f"{scenario}: {exc}")
            finally:
                queue.task_done()

    started = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(concurrency)))
    elapsed = time.perf_counter() - started

    all_latencies = [value for values in latencies.values() for value in values]
    total_errors = sum(errors.values())
    return {
        "tech": runner.tech,
        "host": runner.host,
        "requests": total,
        "concurrency": concurrency,
        "elapsed_s": round(elapsed, 3),
        "rps": round(total / elapsed, 2) if elapsed else 0.0,
        "p50_ms": round(percentile(all_latencies, 50), 2),
        "p95_ms": round(percentile(all_latencies, 95), 2),
        "p99_ms": round(percentile(all_latencies, 99), 2),
        "errors": total_errors,
        "scenario_latencies": latencies,
        "scenario_errors": errors,
        "error_samples": error_samples,
    }


def append_csv(path: str, row: dict, fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({key: row[key] for key in fieldnames})


def save_results(result: dict) -> None:
    summary_fields = [
        "label",
        "tech",
        "host",
        "requests",
        "concurrency",
        "elapsed_s",
        "rps",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "errors",
    ]
    append_csv(os.path.join(RESULTS_DIR, "results.csv"), result, summary_fields)

    scenario_fields = [
        "label",
        "tech",
        "host",
        "scenario",
        "requests",
        "concurrency",
        "rps",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "errors",
    ]
    for scenario, values in result["scenario_latencies"].items():
        requests = len(values)
        scenario_row = {
            "label": result["label"],
            "tech": result["tech"],
            "host": result["host"],
            "scenario": scenario,
            "requests": requests,
            "concurrency": result["concurrency"],
            "rps": round(requests / result["elapsed_s"], 2) if result["elapsed_s"] else 0.0,
            "p50_ms": round(percentile(values, 50), 2),
            "p95_ms": round(percentile(values, 95), 2),
            "p99_ms": round(percentile(values, 99), 2),
            "errors": result["scenario_errors"][scenario],
        }
        append_csv(os.path.join(RESULTS_DIR, "scenarios.csv"), scenario_row, scenario_fields)


async def benchmark_tech(
    tech: str, host: str, total: int, concurrency: int, seed: int, warmup: int
) -> dict:
    stub = None
    channel = None
    if tech == "grpc":
        channel, stub = make_grpc_stub(host)

    limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency * 2)
    async with httpx.AsyncClient(limits=limits, timeout=30.0) as client:
        runner = Runner(tech, host, client, stub)

        # warm-up (não contabilizado)
        if warmup > 0:
            warm_runner = Runner(tech, host, client, stub)
            await run_load(warm_runner, warmup, min(concurrency, warmup), seed)
            warm_runner = None

        result = await run_load(runner, total, concurrency, seed)

    if channel is not None:
        await channel.close()
    return result


async def main_async(args: argparse.Namespace) -> int:
    techs = ["rest", "graphql", "soap", "grpc"] if args.tech == "all" else [args.tech]
    print(
        f"Carga: {args.requests} requisições, concorrência {args.concurrency}, "
        f"host {args.host}\n"
    )
    header = f"{'tech':<9}{'reqs':>7}{'conc':>6}{'rps':>10}{'p50(ms)':>10}{'p95(ms)':>10}{'p99(ms)':>10}{'erros':>7}"
    print(header)
    print("-" * len(header))

    failed = 0
    for tech in techs:
        try:
            result = await benchmark_tech(
                tech,
                args.host,
                args.requests,
                args.concurrency,
                args.seed,
                args.warmup,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"{tech:<9} ERRO: {exc}")
            failed += 1
            continue

        print(
            f"{result['tech']:<9}{result['requests']:>7}{result['concurrency']:>6}"
            f"{result['rps']:>10.2f}{result['p50_ms']:>10.2f}{result['p95_ms']:>10.2f}"
            f"{result['p99_ms']:>10.2f}{result['errors']:>7}"
        )
        result["label"] = args.label
        if result["error_samples"]:
            for sample in result["error_samples"]:
                print(f"  ! {sample}")
        if not args.no_save:
            save_results(result)

    if not args.no_save:
        print(f"\nResultados salvos em {RESULTS_DIR}/results.csv e scenarios.csv")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark SOAP/REST/GraphQL/gRPC")
    parser.add_argument("--tech", choices=["all", "rest", "graphql", "soap", "grpc"], default="all")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--label", default="python", help="rótulo da implementação (ex.: python, typescript)")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    if args.concurrency < 1 or args.requests < 1:
        parser.error("--requests e --concurrency devem ser >= 1")
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
