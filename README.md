# Engineering Ops Agent

Built for the **Gappy AI x Lemma Hackathon** (June 2026) - one pod, three
connected AI-powered workflows on **Lemma SDK**, covering three of the
hackathon's curated problem statements at once:

1. **AI Bug Triage & Release Operator**
2. **AI PR Review & Release Readiness Assistant**
3. **AI Customer Support Desk for a Startup**

## The idea

Small engineering teams juggle bugs, risky PRs, and customer complaints
across disconnected tools. Engineering Ops Agent puts all three on one
shared pod, with AI agents handling the judgment calls and a real,
connected data model tying them together:

- A **support ticket** that turns out to be a real bug **automatically
  creates a linked row in the bug tracker** - nothing falls through the
  cracks between support and engineering.
- A **bug report** gets triaged: severity, priority, reproduction steps,
  and duplicate detection, all written by an AI agent.
- A **pull request** gets a release-readiness review: risk level, risk
  flags, a test plan, and release notes - automatically blocked if risk
  is high.

## Architecture

    Pod: engineering-ops-agent

    TABLES
      issues    - bug reports (severity, priority, repro steps, status)
      prs       - pull requests (risk level, test plan, release notes)
      tickets   - support tickets (escalation, draft reply, linked issue)

    AGENTS (reason only - no direct table access)
      triage    - reads a bug report, returns a JSON triage decision
      release   - reads a PR diff summary, returns a risk assessment
      support   - reads a ticket, decides escalate/reply + is-it-a-bug

    FUNCTIONS (deterministic - do the actual table writes)
      parse_triage_output    / write_triage_result
      parse_release_output   / write_release_result
      parse_support_output   / write_support_result
          (this one can also CREATE a new row in issues)

    WORKFLOWS (FORM -> AGENT -> FUNCTION -> FUNCTION -> END)
      bug-intake-to-triage
      pr-review-to-release
      ticket-intake-to-escalation

**Why agents don't write to tables directly:** Lemma's own docs recommend
it ("Typed validation and writes -> Function. Research, summarization,
extraction, classification -> Agent."), and we also hit a real platform
bug on the direct agent-to-table path on day one of the public SDK launch
- see [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) for the full writeup, including
an upstream GitHub issue reference and how we worked around it.

## Live dashboard

`app/index.html` is a no-build, single-file HTML dashboard (Lemma's
`lemma app init --html` scaffold, customized) that reads all three tables
live through the authenticated Lemma SDK and shows status breakdowns and
recent records for each workflow.

## Running this pod

```bash
lemma pods import . --dry-run   # validate everything first
lemma pods import .             # create/update all resources
```

Try a workflow directly:

```bash
lemma workflow run bug-intake-to-triage -d '{"record_id": "<id>", "title": "...", "description": "..."}'
```

See [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) for platform-level issues we hit
on this SDK release (some resolved with help from the Lemma team, some
worked around) and environment notes for local Docker/WSL setups.

## Stack

- **Lemma SDK** - datastores, agents, functions, workflows, apps
- **Groq** (`llama-3.3-70b-versatile`) - model backend, via Lemma's
  OpenAI-compatible runtime profile
- Local self-hosted Lemma stack (Docker, WSL2)
