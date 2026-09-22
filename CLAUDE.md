# Market Dashboard — refresh instructions

This repo builds a 4-part public-markets dashboard, each part a standalone
Claude Artifact linked from a hub. This file is what a fresh session (including
the scheduled daily routine) needs to refresh the data correctly — read this
before touching anything.

## Artifact URLs (always update in place via `url=`, never re-publish blank)

- Hub: https://claude.ai/code/artifact/984f7869-6d78-4b90-bf73-86d17366b757
- Point 1, Market Signal (macro/rates): https://claude.ai/code/artifact/6818c422-24bf-4bed-b914-28e7fc61bae2
- Point 2, Frontier Watch (frontier tech sectors): https://claude.ai/code/artifact/1e42265a-b79c-4fb4-8878-89ba05056f33
- Point 3, Equities Desk (indices/movers/earnings/portfolio): https://claude.ai/code/artifact/e1f164db-5c0e-4f08-b0c0-09099ef51017
- Point 4, Credit Desk (structured credit / private credit): https://claude.ai/code/artifact/e9fca780-0efa-4261-a995-79ad28386593

## Standing constraints (do not violate)

- Free-tier data only — no paid Bloomberg/FactSet/LSEG access. See WISHLIST.md
  for every gap this causes.
- Every deferred/paid-data gap encountered gets logged in WISHLIST.md.
- Visual system, tokens, fonts (Fraunces/Public Sans/IBM Plex Mono) are already
  built into each `pipeline/render_point*_html.py` — do not redesign, only
  refresh data.

## The citation-date discipline (critical — this is the whole point of automating this)

The user's explicit instruction, which governs every refresh forever:

> "Want to make sure it's very clear how the information is dated and that a
> refresh of the dashboard doesn't actually pull old data in an attempt to
> find new information. I would rather you tell me that there isn't much more
> relevant, newer news for the time being rather than finding old data and
> presenting it as new."

Concretely, on every refresh:

1. Every citation object is `{"title", "url", "date"}` — `date` is the actual
   publish date of the source (YYYY-MM-DD, or YYYY-MM / YYYY if the exact day
   isn't known, or `"n/d"` for an undated reference page). Never copy today's
   date onto an old source.
2. Before rewriting any narrative field (sector sentiment, company
   performance, mover narrative, asset-class commentary), do a real search for
   that specific item. If nothing genuinely newer turns up, leave the existing
   text as-is — do not reword it to look fresh.
3. If something genuinely newer is found, prepend `"UPDATE (this pull, <date>): ..."`
   to the field rather than deleting the prior context, and add the new dated
   citation alongside the old one(s).
4. Point 1 and Point 4 already carry a `freshness_note` / `since_last_pull`
   field at the top level explaining this to the reader — Point 2 and Point 3
   now have the same `freshness_note` field (see `data/point2/sectors.json`
   and the `point3_freshness_note` override / default in
   `pipeline/build_final_payloads.py`). Keep these notes accurate — if a pull
   genuinely found nothing new anywhere, say so plainly in the note rather than
   leaving last pull's wording in place unchanged and looking stale.
5. Never delete or fabricate a citation. An honest "no clean source found" /
   "N/A" entry (see Point 4's student-loan-ABS private pick, or Point 3's
   `"citations": []` movers) is correct and better than forcing a weak fit.
6. Point 1's `point1_synthesis` (the lede paragraph) is two paragraphs
   separated by a blank line (`\n\n`), not one growing blob — `pipeline/
   render_point1_html.py`'s `render_lede()` splits on that blank line and
   renders each half as its own `<p class="lede">`. Paragraph 1 leads with
   this pull's own events (prepend the usual `UPDATE (this pull, <date>): ...`
   there). Paragraph 2 holds everything older — prior UPDATE text and the
   original framing — under a `"Previously (...): ..."` lead-in, so a reader
   gets today's story first without wading through history to find it. When
   a pull adds genuinely new context, prepend within paragraph 1 as usual;
   when paragraph 1's story fully supersedes what's in paragraph 2, fold the
   superseded bit into paragraph 2's "Previously" summary rather than
   letting paragraph 1 grow indefinitely.

## Pipeline (run in this order)

```
pipeline/fetch_indices.py
pipeline/fetch_universe.py
pipeline/fetch_market_caps_cache.py   # weekly is enough, market cap is slow-moving
pipeline/fetch_price_history.py       # must run after fetch_indices.py - see below
pipeline/fetch_earnings_calendar.py
pipeline/fetch_macro.py
pipeline/build_point1_materiality.py
pipeline/build_point3_aggregates.py
pipeline/build_recommendations.py
# --- manual/research step happens here: update data/content_overrides.json
#     (Point 1 + Point 3 narrative/citations) and data/point2/sectors.json
#     and data/point4/asset_classes.json following the discipline above ---
pipeline/build_final_payloads.py      # assembles data/point1 + data/point3 final_payload.json
pipeline/render_point1_html.py        # -> artifacts/point1.html
pipeline/render_point2_html.py        # -> artifacts/point2.html
pipeline/render_point3_html.py        # -> artifacts/point3.html
pipeline/render_point4_html.py        # -> artifacts/point4.html
```

Then publish each changed `artifacts/point*.html` via the Artifact tool with
`url=` set to the matching URL above (never omit `url` — that creates a
duplicate artifact instead of updating).

### Equity-data freshness self-check (added after the 2026-09-22 lag)

Yahoo's free bulk `yf.download` endpoint (`fetch_price_history.py`) can lag a
full trading day behind the individual index tickers `fetch_indices.py`
pulls separately — e.g. still serving Friday's close hours after Monday's
close for the ~1,500-name universe. `fetch_price_history.py` now detects
this itself: it compares the most common last-bar date across tickers
against `data/point3/indices.json`'s latest date, retries once after 90s,
and — if still stale — writes the data anyway but sets `_meta.stale: true`
and prints a loud stderr warning. That flag propagates through
`aggregates.json` → `final_payload.json` (`equity_data_as_of` /
`equity_data_stale`) and, when no hand-written `point3_freshness_note`
override is set, `build_final_payloads.py` auto-appends a plain-language
data-lag caveat to Point 3's freshness note instead of silently presenting
stale movers as current.

Check `data/point3/aggregates.json`'s `equity_data_stale` after running
`fetch_price_history.py` (or just read the script's own stderr). If it's
`true`, re-run `pipeline/fetch_price_history.py` (and the build steps after
it) later in the session — Yahoo has sometimes taken a couple of hours to
catch up — before doing the Point 3 mover research pass, so the research
matches the tickers that actually moved instead of a stale list.

## Daily routine scope

A scheduled 5pm run should, in order:
1. Run the fetch/build scripts above for mechanical data (always safe to
   refresh — prices, indices, macro series).
2. For Point 1 and Point 3: re-check the current top movers / material-events
   list against `data/content_overrides.json`; research any ticker/flag that's
   new or whose narrative is now stale, following the citation-date discipline.
3. For Point 2: spot-check the fastest-moving 2-3 sectors (quantum, robotics,
   defense-adjacent, whatever moved this week) rather than exhaustively
   re-researching all 9 every day.
4. For Point 4: spot-check 2-3 asset classes likely to have moved (Fed
   decision days, CLO/ABS issuance reports, etc.).
5. Render + publish every artifact that actually changed. Skip publishing
   an artifact with zero substantive changes.
6. Commit and push with a commit message summarizing what was actually
   updated (not "daily refresh" boilerplate).
7. If truly nothing changed anywhere, it's fine to skip publishing entirely —
   just say so in the commit-adjacent notes; don't force a no-op publish.

See WISHLIST.md for known data gaps and their reasoning.
