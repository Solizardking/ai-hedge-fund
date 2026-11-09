# hedge-fund-backend

HTTP backend for the **aihf v2 hedge fund engine** (`hedge_fund/` package),
deployed to Railway. The CloddsBot client and the Solana-branded front end
build on this API.

## Source of the engine code

`hedge_fund/` is the package from the owner's copy at
`/Users/8bit/Downloads/Vision-Agents/ai-hedge-fund/hedge_fund` (Mac),
verified identical to `Solizardking/ai-hedge-fund` @ `147d576` (upstream:
virattt/ai-hedge-fund, aihf v2.7.1, MIT) by file-size match on every
top-level file and content reads of README/run.py/pyproject. Test files
(`test_*.py`, `conftest.py`) are excluded from the image, per the upstream
pyproject's own exclude list.

## Posture

- **Paper only.** The engine's brokers are `SimBroker` (backtest) and
  `PaperBroker` (persisted paper book). There is no live-trading code path
  in this package.
- **Read-only API v1.** `GET /healthz`, `GET /api/status`,
  `GET /api/funds`, `GET /api/funds/<name>`. Mutations return 501 until the
  client phase defines auth.
- **No keys in the image.** Data/LLM features activate only when the owner
  sets env vars on the Railway service (`FINANCIAL_DATASETS_API_KEY` for
  market data, `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `XAI_API_KEY` for
  LLM persona pods). `/api/status` reports key *presence* only.
- Paper-fund state lives under `$HOME/.hedge-fund/paper/` in the container
  (ephemeral across redeploys until a volume is attached — known v1 limit).

## Run locally

```bash
pip install -r requirements.txt
PORT=8080 python server.py
curl localhost:8080/healthz
```
