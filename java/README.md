# Java 21 — implementação pendente

Esta pasta está reservada para a terceira linguagem. **Ainda não implementada** porque o
ambiente atual não tem Maven nem Gradle instalados (`mvn`/`gradle` ausentes), então nada
aqui foi compilado/testado.

## Stack planejada (uma única linguagem, as 4 tecnologias)

| Tecnologia | Biblioteca | Porta |
|---|---|---|
| REST | Javalin 6 (ou Spring Boot 3) | 8000 |
| SOAP | Apache CXF (JAX-WS, Jakarta) + Jetty | 8001 |
| GraphQL | graphql-java + Javalin | 8002 |
| gRPC | grpc-java + `protobuf-maven-plugin` (usa `specs/music.proto`) | 8003 |

Reaproveitar os mesmos contratos de `../specs/` e a mesma seed de `../specs/data-model.md`.

## Alternativas

- **A — servidores completos:** instalar Maven (ex.: baixar Apache Maven 3.9.x, ou
  `sudo apt install maven`) e implementar os 4 servidores Java, com `mvn package` e
  smoke tests iguais aos de Python/TypeScript.
- **B — apenas exemplos de código:** manter Java só como trechos de código para os
  slides (exemplos de SOAP/REST/GraphQL/gRPC), sem servidores executáveis.

Definir a alternativa antes de continuar.
