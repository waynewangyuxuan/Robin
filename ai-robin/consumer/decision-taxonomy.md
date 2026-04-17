# Decision Taxonomy

The catalog of decision points per project type. Consumer Agent uses this
in Phase 2 (Gap Analysis) to check which decisions must be covered before
intake can complete.

**How to use this file**: identify the project type from the user's input
(Consumer Phase 1), find the matching section, walk the decision points,
classify each per Phase 2's four buckets (covered / derivable / proxy-able /
must-ask).

The defaults listed are Consumer's go-to choices when proxying (Phase 6).
Override only with clear user signal.

---

## Shared across all project types

These apply regardless of project type. Check these first.

| Decision point | Default | Notes |
|---|---|---|
| Source language | TypeScript (for web/JS) / Python (for data/ML/CLI) / Rust (performance-critical) | Follow ecosystem norm for the domain |
| Package manager | pnpm for TS, uv/pip for Python, cargo for Rust | Modern, fast, lock-file-first |
| Version control | git | Effectively non-optional |
| License | MIT | Unless user indicates otherwise |
| Git hosting | GitHub | Unless user indicates |
| CI strategy | Lint + test on PR; nothing fancy for MVP | Tighten for production-ready |
| Testing strategy | Unit tests for logic, integration tests for contracts, skip E2E for MVP | Scope-up for production-ready |
| Error handling convention | Typed errors, structured error shapes (see contract-design.md conventions) | |
| Logging | Structured JSON logs for services; console for CLI | |
| Secrets | Env vars loaded via .env (dev); platform-specific for prod | Never in code, never in git |

---

## Web app (frontend + backend + DB)

Target: user-facing web application with persistent data.

### Must-ask (no reasonable default)

- **Data storage**: what DB engine? (Postgres / SQLite / MongoDB / hosted
  service)
- **Authentication approach**: email+password / OAuth / magic link /
  passwordless / third-party (Clerk, Auth0, Supabase auth)
- **Data ownership model**: is data per-user, shared, collaborative?
- **Deployment target** if budget-sensitive: free tier requirements narrow
  the options (Vercel free, Netlify free, Railway free tier, etc.)

### Proxy-able defaults

| Decision point | Default | Reasoning |
|---|---|---|
| Frontend framework | Next.js 14 (App Router) | Current ecosystem default for full-stack TS web apps |
| Styling | Tailwind CSS | Modern convention; plays well with component libraries |
| Component library | shadcn/ui if user wants pre-built; else bare Tailwind | shadcn is current go-to for polished-looking MVPs |
| State management | React Context for small; Zustand for medium+ | Avoid Redux unless user asks |
| Data fetching | TanStack Query (React Query) for client; server-side in Next.js RSC | |
| Form handling | React Hook Form + Zod | Type-safe, ecosystem default |
| Validation | Zod | Shared types between client + server |
| API layer | tRPC if full-stack TS; REST if not | End-to-end type safety when full-stack |
| ORM | Prisma for Postgres/SQLite; Drizzle as modern alt | Prisma has better DX for MVPs |
| Dev tooling | ESLint + Prettier + TypeScript strict | |
| Testing | Vitest for unit; Playwright for E2E if requested | |
| Deployment | Vercel | Best Next.js fit; free tier exists |
| Analytics / monitoring | Skip for MVP unless user asks | |

### Additional contextual considerations

- If user mentions "offline support" → PWA + IndexedDB considerations
- If user mentions "mobile-first" → responsive defaults, touch-optimized
- If user mentions "real-time" / "live updates" → consider Server-Sent
  Events or WebSockets; adds infrastructure complexity

---

## Backend service / API

Target: a service exposing APIs, no frontend in scope.

### Must-ask

- **Data storage**
- **Authentication**: service-to-service (API keys, mTLS) or user-facing
  (JWT, sessions)?
- **Deployment target**: serverless functions or long-running server?
- **Request volume expectations**: affects architecture choices

### Proxy-able defaults

| Decision point | Default |
|---|---|
| Language | Node.js + TypeScript (if Web-adjacent) or Python (if data-adjacent) or Go (if performance) |
| Framework | Express / Fastify for TS; FastAPI for Python; Axum for Rust |
| ORM | Prisma / Drizzle for TS; SQLAlchemy for Python |
| API style | REST; GraphQL only if user mentions federation or complex fetch patterns |
| Validation | Zod (TS) / Pydantic (Python) |
| Deployment | Railway / Fly.io for persistent; Vercel Functions / AWS Lambda for serverless |
| Containerization | Dockerfile for persistent deploys; skip for serverless |
| Observability | Structured logs + platform defaults; skip APM for MVP |

---

## Agent / LLM application

Target: an application that uses LLMs to accomplish tasks (chatbot,
assistant, automation, etc.).

### Must-ask

- **Which LLM provider** (OpenAI / Anthropic / other)? Affects pricing,
  capability, SDK
- **Deployment / runtime**: is this a web chat, a CLI, a background
  agent, a Slack bot?
- **What's the primary "tool" the agent uses**? (web search, code
  execution, file manipulation, API calls, DB queries)
- **Conversation state**: per-session, persistent, or shared?

### Proxy-able defaults

| Decision point | Default |
|---|---|
| LLM SDK | Official SDK for chosen provider (Anthropic SDK, OpenAI SDK) |
| Model | Claude Sonnet or GPT-4o class (default "reasonably smart" tier) |
| Framework | Direct SDK calls; avoid heavyweight agent frameworks (LangChain, AutoGen) unless user asks — they add complexity without clear gain |
| Prompt storage | In-repo as .md files or .txt, versioned; not in DB for MVP |
| Tool calling | Native tool-use API (function calling) |
| Streaming | Yes if user-facing chat; no for batch |
| Conversation memory | Simple message history in DB keyed by session_id; more elaborate only if requested |
| Evaluation | Manual review for MVP; skip automated evals unless requested |

### Additional considerations

- If multi-agent → use a minimal orchestrator (or even simpler: sequential
  function calls). Avoid frameworks.
- If rate-limited → include retry-with-backoff from the start
- If the agent does file manipulation → sandboxing strategy matters

---

## CLI tool

Target: a command-line tool run locally.

### Must-ask

- **Target OS**: cross-platform or specific?
- **Distribution**: how do users install? (pypi / npm / homebrew / cargo /
  binary releases)
- **Configuration model**: flags / env vars / config file / all three?

### Proxy-able defaults

| Decision point | Default |
|---|---|
| Language | Python (rich ecosystem for CLI) / Rust (performance + single binary) / TypeScript via Node.js (if JS-ecosystem-adjacent) |
| CLI framework | Click (Python) / Clap (Rust) / Commander (Node) |
| Config | CLI flags primary, env vars for secrets, no config file unless needed |
| Output | Colored + structured; JSON mode if scriptable |
| Testing | Unit tests; golden-file tests for output; skip fuzz |
| Distribution | PyPI for Python, cargo for Rust, npm for Node; single binary releases via GitHub if user asks |

---

## Library / package

Target: reusable code library published for others to import.

### Must-ask

- **Package registry**: pypi, npm, crates.io, etc.
- **Target audience**: internal team, open source, enterprise?
- **Semver policy**: current major version and stability expectations

### Proxy-able defaults

| Decision point | Default |
|---|---|
| Language | Match the target ecosystem |
| Build tooling | Language-standard (tsup/rollup for TS; setuptools/hatch for Python; cargo for Rust) |
| Testing | Comprehensive — libraries are read more than written |
| Documentation | README with examples; API docs via language-standard tooling (typedoc, mkdocs, rustdoc) |
| Changelog | Keep-a-changelog format |
| Versioning | Semver |
| Distribution | Publish to registry on tag push |
| License | MIT unless user indicates stronger (GPL) or more permissive (unlicense) |

---

## Data pipeline

Target: ETL, batch processing, data workflows.

### Must-ask

- **Data sources**: what are the inputs? (files / APIs / DBs / streams)
- **Data sinks**: where do outputs go?
- **Schedule**: one-off, periodic, event-driven, continuous?
- **Scale**: small (laptop) / medium (single server) / large (distributed)?

### Proxy-able defaults

| Decision point | Default |
|---|---|
| Language | Python (pandas / DuckDB) unless scale demands distributed (Spark / Flink) |
| Storage | Parquet for intermediate, Postgres/DuckDB for results |
| Orchestration | cron or simple schedulers for MVP; Airflow / Prefect if complex workflows |
| Testing | Fixture-based; small sample data in repo |
| Idempotency | Required; design tasks to be safely re-runnable |
| Observability | Log progress; track runs in a state table; skip full observability for MVP |

---

## ML experiment / model

Target: training or evaluating a machine learning model.

### Must-ask

- **Task type**: classification / regression / generation / RL / other?
- **Data availability**: is data ready? labeled? size?
- **Compute**: local / colab / cloud GPU?
- **Goal**: prototype understanding, publishable results, or production deploy?

### Proxy-able defaults

| Decision point | Default |
|---|---|
| Framework | PyTorch (default for research); JAX if user mentions TPU or scale |
| Data loading | torch.utils.data.DataLoader with standard splits |
| Experiment tracking | Weights & Biases if public / permitted; else local CSV logging |
| Config | Hydra for structured configs; plain argparse for simple scripts |
| Seed control | Set seeds explicitly; document reproducibility caveats |
| Checkpointing | Save every N steps + best-so-far; disk or W&B artifacts |
| Evaluation | Held-out test set + documented metrics |

---

## How to extend this taxonomy

As AI-Robin runs on new project types, Consumer will hit gaps in this
catalog. When that happens:

1. The run's Consumer can still proceed by asking the user directly for
   decision points not in the catalog.
2. After the run, the human verifier (or maintainer) adds the project
   type to this file with the decisions encountered.

This file is meant to be extended over time. Each addition makes Consumer
faster and less reliant on asking.

---

## Anti-patterns in decision-taxonomy use

- **Treating the catalog as exhaustive**: user may mention decisions
  outside the catalog. Capture those too.
- **Forcing the project into a type**: if a user's project genuinely
  straddles categories (e.g., web app + CLI tool combined), walk both
  checklists and merge.
- **Defaulting aggressively without user signal**: the defaults are
  defaults, not mandatory choices. If user has explicit preferences, the
  catalog entry doesn't apply.
