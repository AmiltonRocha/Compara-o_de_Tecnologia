# Trabalho 6 — Comparação de Tecnologias de Invocação de Serviços Remotos

Serviço de **streaming de músicas** implementado em **SOAP, REST, GraphQL e gRPC**,
em **3 linguagens** (cada linguagem implementa as 4 tecnologias):

| Linguagem | SOAP | REST | GraphQL | gRPC | Status |
|---|---|---|---|---|---|
| Python 3.12 | `soap/` (XML/HTTP) | `rest/` (FastAPI) | `graphql_api/` (Strawberry) | `grpc_api/` (grpcio) | ✅ testado |
| TypeScript / Node 22 | `src/soap/` (node-soap) | `src/rest/` (Express) | `src/graphql/` (Yoga) | `src/grpc/` (@grpc/grpc-js) | ✅ testado |
| Java 21 | pendente | pendente | pendente | pendente | ⏳ ver `java/README.md` |

## Domínio

```
User 1 --- N Playlist N --- N Music
```

Consultas obrigatórias: listar usuários, listar músicas, playlists de um usuário,
músicas de uma playlist e playlists que contêm uma música. CRUD completo dos 3 recursos.

Os **contratos são compartilhados** em `specs/`, então as 3 linguagens expõem o mesmo serviço:

| Arquivo | Contrato |
|---|---|
| `specs/music-service.wsdl` | SOAP 1.1 document/literal |
| `specs/openapi.yaml` | REST |
| `specs/schema.graphql` | GraphQL |
| `specs/music.proto` | gRPC / Protobuf |
| `specs/data-model.md` | modelo + seed comum |

## Estrutura

```
music-service/
├── specs/                 contratos compartilhados (WSDL, OpenAPI, GraphQL, Proto)
├── python/                4 servidores em Python
│   ├── common/store.py    modelo + seed em memória
│   ├── rest/ soap/ graphql_api/ grpc_api/
│   ├── run_all.sh stop_all.sh
│   └── requirements.txt
├── typescript/            4 servidores em TypeScript
│   ├── src/common/store.ts
│   ├── src/{rest,soap,graphql,grpc}/
│   ├── run_all.sh stop_all.sh
│   └── package.json
├── java/                  planejamento (ainda não implementado)
└── load-tests/
    ├── bench.py           benchmark de carga das 4 tecnologias
    ├── run_matrix.sh      roda vários níveis de concorrência
    ├── plot.py            gera gráficos PNG
    └── results/           CSV + gráficos gerados
```

## Portas

| Tecnologia | Porta | Endpoint principal |
|---|---|---|
| REST | 8000 | `http://localhost:8000` (Swagger em `/docs`) |
| SOAP | 8001 | `http://localhost:8001/` (WSDL em `/?wsdl`) |
| GraphQL | 8002 | `http://localhost:8002/graphql` |
| gRPC | 8003 | `localhost:8003` |

## Como rodar — Python

```bash
cd python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

./run_all.sh          # sobe os 4 servidores em background
./stop_all.sh         # derruba todos

# ou individualmente:
.venv/bin/uvicorn rest.app:app --port 8000
.venv/bin/uvicorn soap.app:app --port 8001
.venv/bin/uvicorn graphql_api.app:app --port 8002
./grpc_api/generate.sh && .venv/bin/python grpc_api/server.py
```

Exemplos de chamada:

```bash
curl localhost:8000/users
curl localhost:8000/users/1/playlists
curl -X POST localhost:8002/graphql -H 'Content-Type: application/json' \
  -d '{"query":"{ musicsByPlaylist(playlistId: 1) { title artist } }"}'
.venv/bin/python grpc_api/client.py     # cliente gRPC de exemplo
.venv/bin/python soap/client.py         # cliente SOAP (zeep) de exemplo
```

> **SOAP no Python:** o Spyne 2.14 não funciona no Python 3.12 (usa APIs de import
> removidas). Por isso o servidor SOAP monta/parseia o envelope com `xml.etree`
> seguindo o WSDL compartilhado. Funciona e evidencia a verbosidade do protocolo.

## Como rodar — TypeScript

```bash
cd typescript
npm install
./run_all.sh          # sobe os 4 servidores em background
./stop_all.sh
```

Testes cruzados já validados: cliente Python `zeep` contra servidor SOAP TypeScript e
cliente gRPC Python contra servidor gRPC TypeScript (e vice-versa), pois os contratos
são os mesmos.

## Testes de carga

Com os servidores de uma linguagem no ar:

```bash
cd load-tests
../python/.venv/bin/python bench.py --tech all --requests 500 --concurrency 20 --label python

# matriz de concorrências (diferentes cargas de trabalho) + gráficos
./run_matrix.sh python 300 "1 10 50"
../python/.venv/bin/python plot.py
```

Saídas: `results/results.csv`, `results/scenarios.csv` e os PNGs
`rps_por_tech.png`, `p95_por_tech.png`, `rps_vs_concorrencia.png`, `p95_vs_concorrencia.png`.

### Amostra de resultados (500 reqs, concorrência 20, máquina local)

| tech | Python rps | Python p95 | TS rps | TS p95 |
|---|---|---|---|---|
| REST | 396 | 146 ms | 386 | 147 ms |
| GraphQL | 386 | 101 ms | 343 | 178 ms |
| SOAP | 358 | 175 ms | 358 | 160 ms |
| gRPC | **4204** | **8 ms** | **2870** | **13 ms** |

Leitura rápida: gRPC é ~10x mais rápido (binário + HTTP/2 + sem parsing textual);
SOAP carrega o maior overhead (XML verboso); REST e GraphQL ficam próximos, com GraphQL
pagando custo de parsing/validação da query. Números são ilustrativos — rode na sua máquina.

## Próximos passos

1. Implementar os 4 servidores em **Java** (ver `java/README.md`).
2. Adicionar mais cenários de carga (operações de escrita) e rodar a matriz completa.
3. Montar os slides com: equipe, características das tecnologias, trechos de código das
   3 linguagens, gráficos e análise crítica.
# Compara-o_de_Tecnologia
