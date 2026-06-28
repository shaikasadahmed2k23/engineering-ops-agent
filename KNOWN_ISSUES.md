# Known Issues — Lemma SDK v0.5.2 (local self-hosted)

Documented during the Gappy AI x Lemma Hackathon (June 2026 build window).
These are platform-level issues encountered on day 1-2 of the public SDK
launch, not bugs in this pod's own code.

## 1. Agent direct table-tool calls fail (`pod_query` not in request.tools)

**Symptom:** Any agent with `toolsets: ["POD"]` and table permission grants
fails immediately when asked to read/write a table directly via chat:

Error: tool call validation failed: attempted to call tool 'pod_query'
which was not in request.tools

Reproduced on two independent agents (hello, the unmodified starter agent,
and our own triage agent) - confirms it's not a config mistake on our side.

Related upstream report: GitHub issue #31 on lemma-work/lemma-platform
describes a related symptom on the write side (pod_write_record strips the
payload). Same root cause family: the direct agent-to-table tool path is
unreliable in this release.

Workaround (also Lemma's own documented best practice): Split
responsibility per Lemma's own CLI docs ("Typed validation and writes ->
Function. Research, summarization, extraction, classification -> Agent.").
Agent reasons over data passed to it as plain input, returns a JSON string
answer, with no table permissions granted at all. A Function then parses
that JSON and performs the actual table write via pod.table(...).update(...),
which works reliably. This is the architecture used throughout this pod
(triage agent + parse_triage_output + write_triage_result functions).

## 2. Workflow node JMESPath expressions: no string concatenation, no .output

- input_mapping expressions use JMESPath, not JS-style string templates.
  The + operator for string concatenation is not supported
  (Bad jmespath expression: Unknown token +).
- FORM and FUNCTION node outputs are referenced directly by node id
  (e.g. intake.title, parse_step.severity) - no .output wrapper.
- AGENT nodes are the exception: their raw text reply is under
  <node_id>.answer (a string), not <node_id>.output. If the agent's
  reply is JSON, it must be parsed by a downstream FUNCTION node before
  any other node can read individual fields from it.
- Fields that map to Optional[str] = None in a Function's Pydantic input
  model can resolve to "nothing" in JMESPath rather than null, causing
  "Context path 'X' resolved to nothing" errors even when the field is
  legitimately optional. Workaround: always return a concrete value
  (e.g. empty string) instead of None/omitting the key.

## 3. EVENT-type workflow triggers require a Composio connector - catalog
   appears empty even after configuring COMPOSIO_API_KEY

- start: { "type": "EVENT" } requires config.connector_id and
  config.connector_trigger_id - there is no generic/raw webhook trigger
  type exposed on the workflow resource itself.
- After setting COMPOSIO_API_KEY via lemma-stack config set and
  restarting the stack (clean restart, no errors in backend logs),
  lemma connector list still returns "No results," and
  lemma connector get github / get GITHUB both 404 (CONNECTOR_NOT_FOUND).
- Root cause not fully diagnosed - likely either a missing catalog-sync
  step not exposed in this CLI version, or an incomplete feature in this
  specific local self-hosted release (v0.5.2, 2 days post public launch).
- Decision: did not pursue further given hackathon time constraints.
  Bug-triage workflow runs on MANUAL start instead; demoed by feeding it
  real GitHub issue title/description content rather than a live webhook.

## 4. Deployed HTML app returned APP_NOT_FOUND - RESOLVED

- Symptom: "lemma app deploy" / "lemma apps deploy" always reported
  status READY with a valid current_release_id and "Bundle uploaded
  successfully," but the public app URL
  (http://<slug>.apps.lemma.work) and even Lemma's own pod-workspace
  "Apps" preview both returned:
  {"message": "App with public slug '<slug>' not found", "code": "APP_NOT_FOUND"}
- Root cause (confirmed by Lemma's own team on Discord): the local
  self-hosted stack ships with a default APP_BASE_DOMAIN pointing at the
  cloud domain (apps.lemma.work) instead of the local loopback host,
  so deployed apps get registered under a domain that never routes back
  to the local stack.
- Fix: add an explicit override under [backend.env] in
  ~/.lemma/local/config.toml:
    APP_BASE_DOMAIN = "127-0-0-1.sslip.io:8711"
  (port must match [ports].backend in the same config file), then run
  "lemma-stack restart" and redeploy the app. Apps then resolve at
  http://<slug>.127-0-0-1.sslip.io:<backend_port> and load correctly.
- This is expected to be fixed by default in the next Lemma release.
- Separately, while debugging this we found a real bug in our own
  index.html: a blanket "sed -i s/\\'/'/g" cleanup (used earlier to fix
  a different escaping mistake) had stripped legitimate backslash-escaped
  apostrophes inside JS string literals elsewhere in the file (e.g.
  "this table's own columns" inside a single-quoted string), which is
  invalid JavaScript and caused "Uncaught SyntaxError: Unexpected
  identifier" in the browser console once the app actually started
  loading. Found and fixed via "node --check" on the extracted script
  block, which pinpoints the exact line of any JS syntax error - much
  faster than manual inspection for a file this size.

## Environment notes (useful if containers get into a bad state)

- Docker Desktop + WSL2 bind mounts can desync after sleep/restart - a
  container's view of /app/.local/... can silently fall back to a fresh
  empty directory while the host folder still has real data. lemma-stack
  restart (stop+start) does NOT always fix this. Running
  "docker rm -f lemma-local-backend" followed by "lemma-stack start"
  forces a true recreate and re-resolves the mount correctly.
- lemma-local-agentbox does not auto-restart with the other containers
  after a Docker Desktop relaunch; start it manually with
  "docker start lemma-local-agentbox" if agent chat calls hang or fail
  after a reboot.
