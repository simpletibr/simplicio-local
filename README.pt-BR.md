<h1 align="center">Simplicio Local</h1>

<p align="center">
  <strong>Runtime local-first para inferência any-LLM em CPU e aceleração Apple Silicon, com CLI prática.</strong><br />
  <em>Os comandos ficam em inglês para poder copiar exatamente.</em>
</p>

<p align="center">
<a href="https://github.com/wesleysimplicio/simplicio-local/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/wesleysimplicio/simplicio-local?style=flat-square" /></a>
<img alt="Apple Silicon" src="https://img.shields.io/badge/Apple%20Silicon-M1--M5-111827?style=flat-square" />
<img alt="CMake" src="https://img.shields.io/badge/CMake-3.27+-064f8c?style=flat-square" />
</p>

<p align="center">
<a href="README.md">English</a> | <a href="READMEs/README.pt-BR.md">Português</a> | <a href="READMEs/README.es-ES.md">Español</a> | <a href="READMEs/README.ja-JP.md">日本語</a> | <a href="READMEs/README.ko-KR.md">한국어</a> | <a href="READMEs/README.zh-CN.md">简体中文</a> | <a href="READMEs/README.it-IT.md">Italiano</a> | <a href="READMEs/README.fr-FR.md">Français</a> | <a href="READMEs/README.ru-RU.md">Русский</a> | <a href="READMEs/README.pl-PL.md">Polski</a> | <a href="READMEs/README.hi-IN.md">हिन्दी</a> | <a href="READMEs/README.ar-SA.md">العربية</a> | <a href="READMEs/README.he-IL.md">עברית</a> | <a href="READMEs/README.ms-MY.md">Bahasa Melayu</a> | <a href="READMEs/README.id-ID.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="assets/us4-v6-apple-edition-promo.png" alt="Simplicio Local preview" width="860" />
</p>

---

## Resumo direto

Runtime local-first para inferência any-LLM em CPU e aceleração Apple Silicon, com CLI prática.

## DNA do projeto

`simplicio-local` é a borda de inferência local do ecossistema: um engine
CPU vendorizado para workloads profundos/offline, o runtime C++ nativo e o
caminho Apple Silicon. Os nomes históricos US4 continuam em flags, variáveis
de ambiente e caminhos de implementação por compatibilidade; não são mais a
identidade do repositório.

A primeira tela nova e a porta de entrada; o guia restaurado abaixo e a oficina. Este README precisa convencer rapido sem perder a memoria operacional que ja existia no projeto.

## Começo rápido

```bash
brew install cmake ninja node
npm ci
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
./build/apps/us4-cli --probe
```

## O que faz

- Local-first runtime path for Apple Silicon inference experiments.
- CMake + Ninja build with CLI smoke flows.
- Ollama/custom upstream serve path for practical chat backends.
- Runtime docs for MLX, Metal, scheduler, memory, cache and benchmarks.

## Por que este README foi feito para ganhar atenção

- promessa clara na primeira tela
- links de idioma antes do install
- badges e hero visual para confiança imediata
- quick start copiável
- seção de prova antes de detalhes longos
- gráfico de estrelas para social proof

## Como funciona

```mermaid
flowchart LR
  mapper["simplicio-mapper
repo context"] --> current["Simplicio Local
this project"]
  prompt["simplicio-prompt
reasoning runtime"] --> current
  current --> evidence["validated evidence
tests, docs, screenshots"]
  current --> sprint["simplicio-sprint
delivery loop"]
```

## Fluxo do Projeto (End-to-End)

Pipeline de execução declarativo (`simplicio.flow/v1`), mapeando todas as entradas, passos de aceleração SIMD, caches e saídas:

<p align="center">
  <img src="docs/flow/simplicio-local.svg" alt="Fluxo Simplicio Local" width="860" />
</p>

Regeneração e verificação local:

```bash
npm run flow
# ou: python3 scripts/generate_flow.py
npm run test:flow
```

## Prova e validação

- Changelog tracks CMake project version and starter package version separately.
- Playwright CLI smoke tests are the high-signal E2E path.
- Repo atualmente resolve no GitHub como wesleysimplicio/simplicio-local.

## Ecossistema Simplicio

- [simplicio-mapper](https://github.com/wesleysimplicio/simplicio-mapper) supplies repo context before interpretation.
- [simplicio-dev-cli](https://github.com/wesleysimplicio/simplicio-dev-cli) executa tarefas focadas com verificação.
- [simplicio-prompt](https://github.com/wesleysimplicio/simplicio-prompt) provides fan-out and consensus runtime patterns.
- [simplicio-sprint](https://github.com/wesleysimplicio/simplicio-sprint) turns cards into draft PR delivery loops.

## Padrão de documentação

- [runtime/README.md](runtime/README.md)
- [CHANGELOG.md](CHANGELOG.md)
- [docs/readme-globalization-standard.md](docs/readme-globalization-standard.md)

## Guia histórico US4/Apple restaurado

A secao abaixo recupera o material especifico que existia em `README.pt-BR.md` antes da passada de globalizacao. A regra daqui para frente e simples: melhorar a capa, acrescentar contexto e nunca apagar a memoria operacional.

> Universal State Runtime para inferencia LLM local em Apple Silicon.
> pt-BR. EN version: [README.md](README.md).

![Banner de divulgacao US4 V6 Apple Edition](assets/us4-v6-apple-edition-promo.png)

### Executar localmente

Este e o caminho mais direto para clonar, compilar, executar e validar o projeto na sua maquina.

![Fluxo para executar US4 V6 localmente](assets/local-run-flow.png)

#### 1. Clone

```bash
git clone https://github.com/wesleysimplicio/simplicio-local.git
cd simplicio-local
```

#### 2. Instale as ferramentas

Ferramentas minimas:

- Node.js 16.7 ou mais novo
- npm
- CMake 3.27 ou mais novo
- Ninja
- compilador C++20

Recomendado no macOS:

```bash
xcode-select --install
brew install cmake ninja node
npm ci
npx playwright install
```

Recomendado no Windows:

```powershell
npm ci
npx playwright install
```

No Windows, prefira rodar os comandos CMake nativos em um Visual Studio Developer shell.

#### 3. Configure e compile

macOS/Linux:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Windows PowerShell:

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Se o Ninja nao estiver instalado, o CMake pode usar o gerador padrao da plataforma. Mantenha o mesmo diretorio `build`.

#### 4. Rode a CLI

macOS/Linux:

```bash
./build/apps/us4-cli --probe
./build/apps/us4-cli run --model qwen-0.5b --prompt "hi" --max-tokens 8
./build/apps/us4-cli run --model qwen-0.5b --prompt "hi" --max-tokens 8 --json
```

Windows PowerShell:

```powershell
.\build\apps\us4-cli.exe --probe
.\build\apps\us4-cli.exe run --model qwen-0.5b --prompt "hi" --max-tokens 8
.\build\apps\us4-cli.exe run --model qwen-0.5b --prompt "hi" --max-tokens 8 --json
```

Exemplos uteis com fixtures:

```bash
./build/apps/us4-cli run --model-path tests/fixtures/models/qwen-0.5b/model.us4manifest --prompt "hi" --json
./build/apps/us4-cli run --model-path tests/fixtures/models/llama-3.1-8b --prompt "hello" --json
./build/apps/us4-cli run --model-path tests/fixtures/models/bitnet-b1.58-2b/model.us4manifest --backend neon --prompt "tiny" --json
```

#### 5. Valide tudo

![Checklist de validacao local](assets/local-validation-checklist.png)

Rode os gates JavaScript rapidos:

```bash
npm run lint
npm test -- --coverage
npm run pack:dry
```

Rode build nativo e regressao:

```bash
cmake --build build --config Release
ctest --test-dir build --output-on-failure -C Release
```

Rode evidencia E2E da CLI:

```bash
npx playwright test --reporter=list,html tests/e2e/us4-cli.spec.ts
```

Rode evidencia de benchmark:

macOS/Linux:

```bash
./build/runtime/benchmarks/dense_baseline
./build/runtime/benchmarks/matrix_runner
```

Windows PowerShell:

```powershell
.\build\runtime\benchmarks\dense_baseline.exe
.\build\runtime\benchmarks\matrix_runner.exe
```

#### Como saber que funcionou

- `us4-cli --probe` imprime capacidades de hardware/runtime.
- `us4-cli run ...` imprime tokens gerados pelas fixtures e telemetria explicita de backend.
- `ctest` mostra os testes nativos configurados passando.
- Playwright mostra os smoke tests da CLI passando e grava evidencia em `playwright-report/` e `test-results/`.
- `dense_baseline` imprime linhas de benchmark com backend solicitado, backend observado, fallback, token count e placeholders de corretude onde referencia externa ainda nao esta conectada.

Se o GoogleTest nao estiver instalado localmente, o CMake ainda compila os testes `smoke` e `native contract runner` e avisa que os testes especificos de GTest foram pulados.

### O que este repo eh

Este repositorio contém o **Simplicio Local**: o engine local CPU-first,
os slices do runtime C++ nativo e o caminho Apple Silicon. US4 V6 permanece
como nome histórico da superfície nativa do runtime.

Hoje ele contem:

1. a **camada llm-project-mapper/bootstrap**, usada para estruturar trabalho com agentes;
2. o **planejamento do projeto** em `.specs/`;
3. o scaffold nativo em `runtime/`;
4. a CLI em `apps/cli`;
5. caminhos de unit, contrato nativo, Playwright e benchmark.

Fonte de referencia: [US4-V6-simplicio.md](US4-V6-simplicio.md).

### Escopo do produto

O Simplicio Local mira inferencia local para:

- adapters dense: Qwen, Llama, Gemma;
- adapters MoE: DeepSeek, Kimi, MiniMax, GLM;
- adapters low-memory: BitNet e PT-BitNet ternary;
- execucao portavel em CPU escalar primeiro, com NEON quando disponivel;
- backends Apple opcionais: MLX, Metal, Accelerate e ANE em M5+.

O produto eh explicitamente:

- single-machine first;
- CPU-first: aceleracao Apple e opcional, nao pre-requisito;
- correctness-first antes de qualquer claim de performance;
- CLI + biblioteca, nao app GUI;
- fallback explicito e relato de capacidades do hardware.

### Estado atual do repo

**O planejamento e o scaffold de runtime agora existem no nivel de projeto.**

- Os docs de produto definem visao, dominio, personas, modos de runtime e alvos de compatibilidade.
- Os docs de arquitetura definem boundaries do runtime, contratos centrais e padroes de codigo para C++/Metal/MLX.
- Os docs de workflow explicam como a implementacao passa por task, DoD, PR e release gates.
- Runtime, CLI, fixtures, benchmarks e testes E2E estao presentes.
- Issues do GitHub estao sincronizadas com os arquivos locais de sprint.

### Teste local do Qwen3.8

O adapter OpenAI-compatible pode servir uma pagina local de benchmark em `/`.
Com um `llama-server` disponivel e um GGUF Q4, execute:

```bash
SIMPLICIO_LOCAL_LLAMA_SERVER=/caminho/llama-server \
  python3 bin/local-openai.py \
  --model /caminho/Qwen3.8-27B-Q4_K_M.gguf \
  --model-id qwen3.8-27b-q4km \
  --backend llama-cpp \
  --port 8080
```

Abra `http://127.0.0.1:8080/`. A pagina salva cada execucao no navegador e
permite baixar `simplicio-qwen38-benchmarks.json`. O primeiro capture real
feito neste host esta em
[`docs/benchmarks/qwen38-27b-q4km-2026-08-18.json`](docs/benchmarks/qwen38-27b-q4km-2026-08-18.json).

Para usar o caminho TurboQuant do Atomic Agent, instale o `llama-server`
compatível e peça explicitamente o backend:

```bash
python3 bin/install-turboquant-backend.py --json
python3 bin/local-openai.py \
  --model /caminho/Qwen3.8-27B-UD-Q4_K_XL.gguf \
  --model-id qwen3.8-27b --backend turboquant --turboquant --port 8080
```

O provider verifica a presença de `turbo3` no `--help` antes de iniciar; um
`llama-server` upstream sem o fork TurboQuant não é aceito como se fosse o
backend otimizado. O instalador resolve o manifesto de plataformas do Atomic;
no Linux x64, o release atual testado é `b10269-1.4.0`.

### Stack planejada

- C++20 + CMake + Ninja
- CPU escalar e engine C vendorizado como baseline portavel
- NEON / Accelerate para hot paths de CPU medidos
- MLX e Metal como caminhos opcionais de aceleracao Apple
- ANE como caminho opt-in em M5+
- GoogleTest + CTest para unit e regression
- Playwright para evidencia E2E da CLI

### Modelo de trabalho

O repo segue o ecossistema `AGENTS.md`. As instrucoes centrais vivem em:

- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)

Todo trabalho tecnico deve seguir o loop:

`ler task -> planejar -> editar -> format/lint -> unit -> e2e -> regression -> corrigir -> commit -> PR`

### Roadmap

| Sprint | Tema |
|---|---|
| 01 | Foundations and Skeleton |
| 02 | CPU Scalar Baseline |
| 03 | MLX and Metal Skeleton |
| 04 | NEON Hot Paths |
| 05 | BitNet and Ternary |
| 06 | KV Memory Architecture |
| 07 | Llama Adapter |
| 08 | MoE Foundation |
| 09 | MoE Advanced |
| 10 | Continuous Batching and Speculative Decoding |
| 11 | ANE M5+ Offload |
| 12 | Auto-Tune and v1.0 Release |

Detalhes:

- [.specs/sprints/BACKLOG.md](.specs/sprints/BACKLOG.md)
- [.specs/sprints/TIMELINE.md](.specs/sprints/TIMELINE.md)

### Layout do repo hoje

```text
.specs/        fonte de verdade do planejamento
.agents/       agentes customizados
.skills/       skills reutilizaveis
.claude/       hooks/settings do Claude
.codex/        hooks/settings do Codex
.github/       CI/DoD do starter e templates
apps/          entrada da CLI nativa
bin/           CLI do llm-project-mapper
runtime/       runtime C++, backends, adapters, tuning, telemetria, benchmarks
test/          self-tests do starter
tests/         testes de contrato nativos e E2E Playwright da CLI
```

### Fora de escopo

- inferencia em nuvem ou distribuida;
- treino ou fine-tuning;
- aceleracao Metal/MLX/ANE especifica de Apple em hosts nao-Apple (o caminho
  CPU continua suportado);
- shell GUI antes de CLI e biblioteca estarem estaveis.

## Histórico de estrelas

<a href="https://www.star-history.com/#wesleysimplicio/simplicio-local&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=wesleysimplicio/simplicio-local&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=wesleysimplicio/simplicio-local&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=wesleysimplicio/simplicio-local&type=Date" />
  </picture>
</a>

## Licença

See the repository license and distribution notes before production use.
