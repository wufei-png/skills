---
name: review-tests
description: Review existing tests as a read-only, defect-first auditor and return prioritized findings about missing protection, false confidence, invalid oracles, redundancy, implementation coupling, isolation, and tests that endorse incorrect behavior. Use only when explicitly invoked; do not write or fix tests.
---

# Review Tests

Inspect the requested tests firsthand. Report every qualifying test-suite defect supported by the reviewed evidence. Stay read-only: never edit files, commit, update snapshots or fixtures, post comments, or hand the audit to another agent.

## Set the scope

1. Read applicable repository instructions and resolve the target. Default to the current project's test suite; honor a narrower path or subsystem when requested.
2. Inventory the scope structurally: locate test files, runners, configuration, fixtures, helpers, snapshots, and continuous-integration gates without deeply reading every test.
3. By default, map the full scope and deeply inspect the highest-risk or most suspicious surfaces. In `exhaustive` mode, deeply inspect every in-scope test. Never present a risk-first review as exhaustive.
4. Read enough relevant production code and readily available contracts, requirements, or regression evidence to understand what each deeply reviewed test should protect. Do not conduct open-ended history, issue, or incident searches.

Prioritize security, money, authorization, data integrity, destructive actions, public contracts, failure and recovery paths, complex domain rules, and high-change code. Treat mocks of the subject, shared expected-value helpers, snapshots, weak assertions, skips, retries, sleeps, shared state, and repeated scenarios as discovery signals, not automatic findings.

## Establish the test basis

Judge expected behavior from available explicit requirements, public contracts, domain invariants, user-visible outcomes, and confirmed regression evidence. Use production code to trace behavior, not as the default oracle for correctness.

When intended behavior is ambiguous or conflicting, do not declare the test wrong unless independent evidence resolves the ambiguity. Record unresolved uncertainty as residual risk.

## Challenge the evidence

For each deeply reviewed behavior, ask:

- What plausible production defect should this test catch, and would the current oracle fail for it?
- Is the expected value independent of the implementation, or does it repeat the same calculation, constants, branches, helper, generated output, or snapshot?
- Does the test prove the important observable outcome, including state preservation and side effects, rather than mere execution or mock wiring?
- Would it survive a behavior-preserving refactor, or is it coupled to private state, internal calls, incidental ordering, layout, or text?
- Do mocks, fakes, fixtures, and emulators preserve the real boundary contract and every field or side effect the behavior depends on?
- Does each neighboring test protect a distinct scenario or failure mode rather than repeat existing evidence?
- Are material negative, boundary, authorization, concurrency, timeout, retry, and recovery paths protected?
- Can tests run independently and deterministically without leaked state, uncontrolled time or randomness, fixed sleeps, or external availability assumptions?

Coverage proves execution, not defect detection. Counts, pass rates, level ratios, assertion counts, and mock counts are never findings by themselves. Several assertions may jointly prove one behavior, and a slow integration test may uniquely protect a critical boundary.

## Run only discriminating checks

Start with static inspection. Run only the smallest existing command needed to confirm a concrete concern about execution, isolation, order, time, randomness, or reproducibility.

Do not install dependencies, run destructive commands, accept changed output, update snapshots, golden files, or fixtures, or run the full suite, coverage, or mutation testing by default. Record each command, result, and cache or temporary artifact. If safe execution is unavailable, keep findings evidence-based and state the limitation.

## Admit findings

Report an issue only when:

- it materially weakens correctness, security, reliability, performance, or maintainability;
- it is discrete and actionable;
- a concrete missed defect, false-confidence path, unprotected behavior, or recurring maintenance cost can be demonstrated;
- the defect belongs to the test system rather than production code;
- the author would probably fix it.

For missing-test findings, identify the material production branch or contract. In risk-first mode, show that targeted search found no credible in-scope test protecting that failure; in `exhaustive` mode, show that complete in-scope inspection found none. If a correct existing test already exposes a production bug, the product bug is outside this review.

Do not report speculative risks, generic best practices, raw coverage gaps, intentional tradeoffs, style nits, or different but equally trustworthy test designs. Deduplicate findings with the same root cause.

## Write the result

Present findings first, ordered by severity. Use one entry per issue:

`[P1] Imperative finding title — path/to/file.py:line`

Follow with one short paragraph explaining the triggering scenario, why the current test evidence is untrustworthy or insufficient, and the resulting risk. Cite the narrowest useful test, fixture, configuration, or uncovered production location. Do not produce an implementation plan, portfolio action table, score, or mandatory external reference.

Base priority on the risk left unprotected, not the smell name:

- `P0`: catastrophic false assurance that universally blocks a safe release.
- `P1`: urgent loss of protection for critical behavior or another severe false-confidence path.
- `P2`: material test-suite defect that belongs in normal corrective work.
- `P3`: lower-impact defect whose concrete maintenance or confidence cost still justifies correction.

When no candidate passes the finding gate, begin with `No findings.` An empty review is preferable to a manufactured issue.

Then briefly report:

- **Overall assessment:** trustworthiness of the reviewed evidence.
- **Scope:** inventoried and deeply reviewed areas; risk-first or exhaustive.
- **Commands:** commands, results, and artifacts; `None` if purely static.
- **Residual risks:** unreviewed, ambiguous, or execution-unverified behavior.
