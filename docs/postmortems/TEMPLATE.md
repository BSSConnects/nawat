# Postmortem — <short title>

**Date:** YYYY-MM-DD · **Duration:** Xh Ym · **Severity:** SEV1 | SEV2 | SEV3
**Author:** <name> · **Reviewers:** <names>
**Status:** draft | reviewed | actions tracked

> **Blameless.** The output of this document is a **changed system**, not a changed person.
> "Someone ran the wrong command" is never a root cause. "The command was destructive, had no
> confirmation and no dry-run" is.

## Impact

Who was affected, for how long, and what they could not do. Customer-visible impact first; internal
impact second. Numbers, not adjectives.

## Timeline

All times UTC. Include when we *detected* it, not only when it started — the gap between those two
is usually the most actionable finding in the document.

| Time | Event |
|---|---|
| 09:14 | change X merged |
| 10:02 | first failed module install (undetected) |
| 11:30 | customer reported |
| 11:45 | mitigated |

## What happened

The mechanism. Enough detail that someone who was not there can follow it.

## Why it was not caught sooner

Which test, alert or review should have caught this, and why it did not. If nothing existed, say so
plainly — that is the finding.

## What went well

Genuinely include this. It identifies what to protect when changing things.

## Action items

Every item has an owner and an issue. Items without both are wishes.

| # | Action | Type | Owner | Issue |
|---|---|---|---|---|
| 1 | | prevent / detect / mitigate | | #123 |

Prefer **prevent** over **detect**, and **detect** over **mitigate**. A faster recovery is worth
less than the incident not happening.

## Lessons

Two or three sentences someone would benefit from reading in a year.
