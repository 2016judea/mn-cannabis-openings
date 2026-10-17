# Twin Cities Cannabis Openings

**Live:** https://mn-cannabis-openings.vercel.app

Every cannabis business on Minnesota's state license list in the seven-county Twin Cities metro,
plus every Minneapolis dispensary and grow building out right now, staged by how close it is to
opening, with the state's named site contact and email for each licensee.

Built for security, transport and service firms. First prospect: a Craigslist security post
(10/03) *"Specializing in: ... Marijuana Dispensaries, Marijuana transport ..."*.

## Free and paid

| | what | why |
|---|---|---|
| free | the count, the map of every business, counts by kind, and 10 real rows with stage, city and license date | shows the stage join on real businesses |
| **$5** | all 211 rows; each site contact's name and email and legal entity; the builder on Minneapolis permits; the **closest to opening** sort; the spreadsheet | a security firm acts by calling the person opening the store, before the opening; that is the contact plus the stage sort |

## Price

$5 once. Set by Aidan on 2026-10-17 for all three products in this round. **A hypothesis:**
one dispensary guard contract runs to thousands a month, so one meeting pays for it many times
over. Revise on checkout-vs-payment evidence.

## The paywall

Same as `mpls-new-rentals` (ported from `msp-house-index` via `salon-rates`, `product-paywall`
skill): `site/` ships only the free slice; `private/bundle/full.json.gz` (gitignored) is uploaded
as `api/_full/` and served by `/api/data` behind an HMAC password minted at Stripe embedded
Checkout and emailed by the webhook. Comp: `python3 scripts/issue_password.py "comp:<label>"`.

## Run it

    # 1. download the newest OCM list into private/cache/ocm_licensed_<MMDDYY>.xlsx
    #    (link on https://mn.gov/ocm/businesses/licensing/application-data.jsp)
    python3 pipeline/pull_permits.py private/permits_raw.json
    python3 pipeline/build.py
    cd scripts && python3 publish.py && python3 deploy.py   # VERCEL_TOKEN in env

See `DATA_MODEL.md` for each field and the ones that could not be filled. MIT licence.
