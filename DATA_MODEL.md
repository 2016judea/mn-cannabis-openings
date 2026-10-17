# Data model: Twin Cities Cannabis Openings

Written from the need alone (BUSINESS.md rule 5), then checked against what exists, 2026-10-17.

**The need.** A security firm (first prospect: a Craigslist post, 10/03: *"Specializing in: ...
Marijuana Dispensaries, Marijuana transport ..."*) wants the cannabis businesses that are about to
need guards or transport, before a competitor has the contract, and who decides.

## Ideal model

**Cannabis business** (one per licensed site, or per build-out not yet licensed)

| field | answers |
|---|---|
| business name (DBA), legal entity | who it is, what to search |
| kind: dispensary / grow-manufacturing / transport-wholesale-delivery / testing-events | guards at a door, or product to move |
| site address, city, lat/lon | is it in my area |
| stage: opening soon / newly licensed / licensed / built out unlicensed | how close to the moment a security plan is due |
| state license issued + expires | how fresh |
| build-out permit stage + date + builder | how close to opening |
| site contact name + email | who to call |
| security plan on file, current security vendor | is there an incumbent (ideal; unpublished) |

## Reality, field by field

| field | source | filled? |
|---|---|---|
| name, entity, kind, address, dates, contact, email | MN Office of Cannabis Management licensed-business list (xlsx, file dated 10/12/26; the page is bot-walled to curl, fetched via its direct asset URL) | yes: 183 metro licensees, all with contact + email |
| build-out stage, builder | Minneapolis permit register (comments naming cannabis/dispensary) | Minneapolis only: 42 permits, 14 joined to a license, the rest listed as their own rows |
| suburbs + Saint Paul build-out stage | Saint Paul stopped publishing permits 2025-06-30; suburbs publish none | **no**: those rows carry the state license alone |
| preliminarily approved (not yet licensed) applicants | OCM publishes counts only | **no** |
| incumbent security vendor | unpublished | **no** |
| lat/lon for non-retail licensees with no site address | none | placed at the middle of their city (45 rows), or left off the map (18) |

Verdict: build. The list a security firm acts on (who, where, how new, who to email) fills;
"opening soon" is precise only inside Minneapolis, and the page says so.
