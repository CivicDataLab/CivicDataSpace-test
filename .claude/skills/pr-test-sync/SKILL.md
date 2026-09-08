---
name: pr-test-sync
description: After a PR merges in a product repo, read the real diff, decide which test categories it warrants, write those tests in the matching test repo using existing page objects and fixtures, prove they can actually fail, and open a DRAFT PR for review. Use when a merge needs test coverage, or when catching up coverage for already-merged PRs. Never merges anything.
---

# PR test sync

A merged PR changed behaviour. This adds the tests that cover it, in the right test
repo, with the right markers, and hands you a draft PR — it never merges.

**The output is a draft PR, always.** Not a merge, not a ready-for-review PR. The
review gate is the point.

## Who reads this file

Two callers, and they have different capabilities:

1. **A local Claude Code session**, invoked on demand as `/pr-test-sync` with a repo and
   PR number. Has the test repos checked out and a real `.env` with working credentials.
2. **The scheduled cloud routine** ("Test-coverage sync: merged dev PRs → product test
   repos"), which clones this repo fresh and sweeps for recent merges on a cron.

This file is the single source of truth for both. It lives on `main` because that is the
branch a fresh clone gets — a cloud run cannot see anything committed only to `CI`.

**The cloud sandbox has no test credentials.** `TEST_EMAIL_1` / `TEST_PASSWORD_1` exist
only in local `.env` files and GitHub Actions secrets. A cloud run can therefore only
execute unauthenticated checks — status codes, OIDC discovery, redirect targets, public
pages. See §6 for what that means for the red/green proof, which is not optional but is
satisfiable differently depending on which caller you are.

## 0. Inputs

Needed: **source repo** + **merged PR number**. Everything else is resolved here.

Never work from a PR title or body alone — they describe intent, not what shipped:

```bash
gh pr view $N --repo CivicDataLab/$SRC \
  --json title,body,files,mergeCommit,baseRefName,mergedAt,url
gh pr diff $N --repo CivicDataLab/$SRC        # the actual diff
```

If the PR isn't merged, stop and say so — this skill covers merged behaviour, not
proposals.

## 1. Which test repo

| Source | Test repo |
|---|---|
| `DataSpaceBackend`, `DataSpaceFrontend` | `CivicDataSpace-test` |
| `DataSpaceKeycloakTheme`, `DataSpaceKeycloak`, `DataSpaceAuth` | `CivicDataSpace-test` |
| `dashboard-superset`, `analytics`, `superset*` | `CivicDataSpace-test` |
| `ParakhAI-Backend` (`ParakhAPI` redirects), `ParakhAI-frontend`, `ParakhAI-Keycloakify-theme` | `ParakhAI_test` |
| `IDS-DRR-Frontend`, `IDS-DRR-Data-Management`, risk-model / pipeline repos | `IDS-DRR-QA-Automation` |

Two standing decisions, already made — don't relitigate them per-PR:

- **Analytics/Superset coverage lives in `CivicDataSpace-test`.** There is deliberately
  no separate analytics test repo.
- **Keycloak/theme coverage lives in `CivicDataSpace-test`** too. But auth is
  cross-cutting: ParakhAI authenticates through DataSpace's issuer, and that coupling
  is what broke in ParakhAI#107. An auth change may need a matching test in
  `ParakhAI_test` as well — check, and say which you chose and why.

## 2. Markers differ per repo — check before writing

Both `ParakhAI_test` and `IDS-DRR-QA-Automation` run `--strict-markers`. An invented
marker doesn't warn, it **fails collection for the whole suite**. Read the target's
markers first:

```bash
sed -n '/^markers/,/^$/p' pytest.ini
```

Verified 2026-09-09 — a starting map only. **This table goes stale**: IDS-DRR gained
`security`, `performance`, `load`, `accessibility` and `responsive` within a day of the
first version of this file being written. Re-read `pytest.ini` every time.

| Category | `CivicDataSpace-test` | `ParakhAI_test` | `IDS-DRR-QA-Automation` |
|---|---|---|---|
| smoke | `smoke` | `smoke` | `smoke` |
| functional | `functional` | `e2e` | `flow` |
| api | `api` | `api` | **none** |
| regression | `regression` | `regression` | **none** |
| security | **none** | `security` | `security` |
| performance | **none** | `performance` | `performance` |
| load | **none** | `load` | `load` (opt-in, `-m load` only) |

Also available: CDS `mobile`/`seo`/`accessibility`/`widget`; Parakh `visual`/`auth`/
`mobile`/`accessibility`/`regression_write` (write-side, sandbox-org only, opt-in);
IDS-DRR `accessibility`/`responsive`/`analytics`/`dataset`/`component`/`multistate`/
`map_validation`/`chart_validation`/`table_validation`/`cross_state`.

IDS-DRR still has **no `api` and no `regression`** marker, and no API layer or login flow
to test — it is Selenium against public pages. Its `load` marker is opt-in and excluded
from the default run; do not add `load` tests that would fire in normal CI.

When a category has no home in the target repo, **write what fits and name the rest as
a gap in the PR body**. Do not stand up new infrastructure — an API harness inside a
100%-Selenium suite is not something an auto-generated PR gets to decide. (If a marker
you need is genuinely missing, say so; the owner may add it, as happened for IDS-DRR's
`security`/`performance`/`load`.)

## 3. Decide what the diff actually warrants

Map changed paths → categories:

| Changed | Likely categories |
|---|---|
| GraphQL schema / resolver / mutation / serializer | `api` + `regression` |
| New or changed UI page/component | `smoke` + `functional` (CDS) / `e2e` (Parakh) / `flow` (DRR) |
| Auth, session, token, Keycloak, middleware | `security` (Parakh) or `regression` (CDS) + the cross-app check above |
| List/query/pagination, N+1-prone paths | consider `performance` / `load` (Parakh only) |
| Health, deploy, infra wiring | usually `smoke` only |
| Docs, CI config, formatting, lockfiles | **nothing — stop, see below** |

**A PR that changed no user-visible or API-visible behaviour gets no tests.** Say that
plainly and stop. A test written to justify the run is worse than no test: it costs CI
time forever and passes whether or not the thing works. This repo family already made
this exact call once — `security` and `data` were deliberately denied their own CI jobs
because they'd have collected nothing meaningful.

Prefer one or two tests that would genuinely have caught the bug over broad coverage of
everything the diff touched.

## 4. Get a clean checkout without touching the user's work

*Local caller only — a cloud run already has a fresh clone and can branch normally.*

**Never `git checkout` in the test repo's main working tree.** These repos routinely sit
on a feature branch with dozens of uncommitted changes (`CivicDataSpace-test` had 32 on
`feat/backend-smoke-gate` during this skill's first run). Use a worktree:

```bash
git -C <test-repo> fetch origin <base> --quiet
git -C <test-repo> worktree add <scratch>/wt -b test-sync/$SRC-pr$N origin/<base>
# ... work in <scratch>/wt ...
git -C <test-repo> worktree remove <scratch>/wt --force
```

Verify afterwards that the original tree is still on its branch with its changes intact.

## 5. Write using what already exists

The suites enforce a three-layer split:

```
tests/     assertions + fixture wiring only
pages/     Page Objects (actions, no assertions)
locators/  raw selectors, one file per page
```

Before writing anything: grep for an existing Page Object, locator file, fixture, or
GraphQL client helper covering this area. Reuse it.

- **Never put a raw selector in a test.** If the feature has no Page Object yet, that's
  a real gap — say so in the PR body and scope the test to what existing objects can
  reach, rather than hacking selectors inline.
- **`CivicDataSpace-test` and `IDS-DRR-QA-Automation` are both Selenium.** Only
  `ParakhAI_test` is Playwright. Don't write Playwright idioms into a Selenium suite.
- `CivicDataSpace-test` splits by persona (`consumer/`, `provider/`) then by kind
  (`smoke/`, `functional/`, `mobile/`) — follow the existing tree, don't invent a path.
- `ParakhAI_test` has **path-filtered CI**: a new test in a directory the `changes`
  filters don't route to will silently never run. Check `.github/workflows/ci.yml`'s
  `filters:` block and update it in the same PR if the path is new.

### Confirm your test is actually collected

Existence in the file is not execution. Always:

```bash
python -m pytest <file> --collect-only -q | grep <your_test_name>
```

Real instance: `tests/consumer/smoke/test_components.py` has a `'''` at line 57 closing
at 122, so `TC_HOM_02`–`TC_HOM_09` sit inside a string literal and have never run — and
they use a broken calling convention (`By.XPATH, Locators.X` where `Locators.X` is
already a `(By, str)` tuple) that survived precisely because nothing collected them.
Copying a neighbouring test blindly can mean copying dead, broken code. Match the form
of a test you have **confirmed collects and passes**.

## 6. Prove the test can fail

A regression test that cannot fail is worthless, and a generated one gets no benefit of
the doubt. Required, both directions:

1. Run it against dev. Capture the real pass output.
2. Flip the assertion to an intentionally wrong expected value. Run again. **Confirm
   red.**
3. Revert to the correct assertion. Confirm green.

Paste both outputs in the PR body. This only ever touches the test's own assertions —
never mutate the dev deployment to force a failure.

If it passes before the feature exists, or passes with the assertion inverted, it isn't
testing anything. Fix it or drop it.

### `skipped` is NOT `passed` — check the count, not the exit code

`2 skipped` exits 0 and looks like success at a glance. It means your test never ran and
you have proven nothing. **Read the summary line and require an explicit `N passed`
matching the number of tests you added.** Run with `-rs` so skip reasons are visible.

The auth fixtures are the usual cause. `_get_keycloak_token` in
`CivicDataSpace-test/tests/api/conftest.py` turns a **401 into `pytest.skip(...)`**, not a
failure — so any authenticated API test silently disappears when credentials are wrong,
missing, or incomplete.

Most common instance, hit on this skill's second run: the realm's client is
**confidential**, so ROPC needs `client_secret`. Omit it and everything skips:

```python
kc_token = _get_keycloak_token(
    keycloak_config["url"], keycloak_config["realm"],
    keycloak_config["client_id"], email, password,
    client_secret=keycloak_config.get("client_secret"),   # REQUIRED
)
```

The `auth_token` fixture already passes it — prefer that fixture over re-implementing the
token fetch. (`test_api_002_auth.py::test_auth_token_has_required_fields` re-implements it
*without* the secret and has been silently skipping as a result.)

**If you cannot get the test to genuinely pass and genuinely fail, do not open a PR.**
Stop and report why. Shipping unproven tests is the exact failure this section exists to
prevent — an unverified generated test is worse than none, because it looks like coverage.

### If you are the cloud routine (no credentials)

You cannot run authenticated or browser-login tests at all. That does not lower the bar,
it narrows what you may write:

- **Prefer coverage you can actually prove.** An unauthenticated check you ran red and
  green beats an authenticated one you only reasoned about.
- If a test genuinely needs credentials, you may still include it — but label it
  **`UNVERIFIED — not executed, no credentials in this environment`** in the PR body,
  next to that specific test, and say what a human must run to confirm it. Never present
  it alongside proven ones as though it passed.
- Never weaken an assertion so it passes without credentials, never fake output, and
  never claim a run you did not perform. A PR that says plainly "I could not execute
  these two" is doing its job; one that quietly implies it did is worse than useless.

## 7. Open the draft PR

Branch: `test-sync/<source-repo>-pr<N>`.

**Base: the branch where test work actually lands — which is often NOT the default
branch.** Do not guess. Resolve it from where recent merges went:

```bash
gh pr list --repo CivicDataLab/$TEST_REPO --state merged --limit 8 \
  --json number,baseRefName,title,mergedAt \
  --jq '.[] | "#\(.number) -> \(.baseRefName)  \(.mergedAt[:10])  \(.title[:50])"'
gh repo view CivicDataLab/$TEST_REPO --json defaultBranchRef --jq .defaultBranchRef.name
```

(The field is `defaultBranchRef`, not `defaultBranch` — the latter is not a valid field
and errors out.)

`CivicDataSpace-test` is the cautionary case: default branch is `main`, but `main` only
takes docs, `dev` runs days behind, and every recent test PR merged into **`CI`** —
which is also the only branch whose workflows execute. Basing on the default there would
put the tests somewhere they'd never run.

```bash
gh pr create --repo CivicDataLab/$TEST_REPO --draft --title "..." --body-file body.md
```

Body must contain:

- The source PR (link) and merge commit that triggered this.
- What behaviour changed, from the diff — not from the PR title.
- Which categories were added, and **why those and not the others**.
- The red→green proof from §6, pasted.
- Every gap: missing Page Object, category with no home in this repo, CI filter that
  needed updating.
- Anything deliberately not covered, and why.

**Draft only. Never `--ready`, never merge, never enable auto-merge.**

## 8. Don't duplicate

Before any of the above:

```bash
git ls-remote --heads origin "test-sync/$SRC-pr$N"
gh pr list --repo CivicDataLab/$TEST_REPO --search "test-sync/$SRC-pr$N" --state all
```

If either exists, stop and report it. Re-running against the same source PR must
no-op, not open a second PR.

## How this gets triggered

**Daily cron (live today).** The routine "Test-coverage sync: merged dev PRs → product
test repos" runs weekdays at 03:30 and sweeps for merges in the last 24h (72h if none).
This is currently the only automatic path, so worst-case latency is about a day.

**On merge (not wired yet).** A `RemoteTrigger` webhook trigger per source repo firing
the same routine. Blocked on the Claude GitHub App being installed on the org/repos
(https://github.com/apps/claude/installations/select_target) — until then
`create_webhook_trigger` returns `github_app_not_installed`. Schema, once unblocked:
`{routine_trigger_id, hook_type:"app", source:"github", scope_id:"<owner/repo>",
events:["pull_request"]}`. Roll out in waves (DataSpace → ParakhAI → Keycloak/analytics
→ IDS-DRR), proving each mapping before adding the next.

Because both paths write into the same test repos, §8's duplicate check is what keeps
them from fighting each other. Do not skip it.

## Gotchas

- Default branches are **not uniform** across this org. Always resolve, never assume.
- `--strict-markers` in two of three repos turns a typo'd marker into a total collection
  failure, not a warning.
- `ParakhAI_test`'s path-filtered CI silently skips tests in unrouted directories — a
  green CI run does not mean your new test executed.
- `CivicDataSpace-test` executes from its `CI` branch. Its default branch (`main`) and
  `dev` do not run the workflows — see §7. Flag in the PR body which branch you targeted.
- Suites share one dev backend with known concurrency limits. Never add a test that
  hammers it in parallel; the existing serialization in each repo's CI exists for a
  reason. This also means **concurrency/pool-exhaustion bugs are not reproducible here** —
  a perf fix's *mechanism* is usually untestable; cover the correctness risk the fix
  introduced instead, and name the rest as a gap.
- A 401 from Keycloak becomes a **skip**, not a failure — see §6. Always check for
  `N passed`.
- When a fix is motivated by performance, the thing worth testing is rarely the
  performance. Ask what the change could silently break: #136 was a concurrency fix, but
  the real risk it introduced was a conditional write that might stop persisting user
  state. That's what got covered.
