# Week 1 Research Notes: extracted architecture, cost and outcome data

Source IDs refer to `sources.md`. "Official" means PIB or Parliament; anything else is flagged.

## 1. Timeline

| Year | Event | Source |
|------|-------|--------|
| 1986 | PRS introduced (CRIS established the same year) | A2 |
| 1990s | PRS network expands across zones (CONCERT) | A2 |
| 2002 | Internet ticket booking begins | A2 |
| 2010 | Current PRS generation deployed on Itanium servers and OpenVMS | A2 |
| 2014 | Next Generation e-Ticketing (NGeT) launched; RHEL-based open-source infrastructure (Red Hat award) | A2, C2 |
| Jun 2025 | Aadhaar-authenticated Tatkal (1 Jul), OTP (15 Jul); PIB announces new PRS, 1.5 lakh/min, target "by December 2025" | A1, B5 |
| Jul 2025 | RailOne app launched | A2 |
| Dec 2025 | Lok Sabha reply: 3.02 crore IDs deactivated, +65% Tatkal availability time on 322 trains | B1 |
| 15 Jul 2026 | New IRCTC website beta | A2, B2 |
| Aug 2026 | Phased train migration to the new PRS begins (target date slipped from Dec 2025) | A2, B3 |

## 2. Architecture

**Legacy (until now).** Official: PRS deployed 2010 on Itanium servers and OpenVMS, built and run by CRIS, accessed by counters, IRCTC website and apps (A2). Secondary: three-tier client-server with regional centres (Delhi, Mumbai, Kolkata, Chennai, Secunderabad), HP Reliable Transaction Router middleware (grade D, verify). 2014 NGeT used Red Hat Enterprise Linux (C2).

**Edge and security (official).** Network firewalls, intrusion prevention, application delivery controllers, web application firewalls, Akamai anti-bot, CERT-In audits, RailTel threat intelligence (B1). Vendor view: AWS WAF, Shield, GuardDuty, Security Hub, EKS with Inspector, Control Tower multi-account (C1). Do not assume C1 describes the production booking path.

**New PRS.** "Agile, flexible and scalable", "cloud-enabled, next-generation", designed for ten times current load (A1, A2). Multilingual UI, seat-choice and fare calendar, simplified booking steps (A1, A2). Internal design is **not publicly documented** in what we found.

**Our modelling assumption (for Week 2 diagram, labelled as our design, not IRCTC's):** CDN and WAF -> load balancer -> stateless booking API instances (autoscaled) -> cache (seat availability) -> database; optional waiting-room queue in front for the Tatkal burst.

## 3. Problem data
- Tatkal windows: 10:00 AC, 11:00 non-AC; agents blocked for 30 minutes after each opens (B5).
- Legacy capacity: 32,000 bookings/min, 4 lakh enquiries/min (A1, A2).
- Scale: 65.08 crore reserved tickets (Jun 2025-Jun 2026), 57.90 crore online (89%), 73% cashless, about 20.5 lakh passengers/day (A2). RailOne about 9.65 lakh bookings/day (A2).
- Bots: 3.02 crore suspicious IDs deactivated since Jan 2025 (B1).
- Caveat in B2/B3: more capacity does not add seats; demand for popular trains still sells out.

## 4. Solution data
- Demand shaping: Aadhaar/OTP authentication, agent blackout, ARP 120 -> 60 days, charting 8 hours before departure (A1, A2, B5).
- Capacity: bookings 1.5 lakh+/min (about 5x), enquiries 40 lakh+/min (10x) (A1, A2).
- Rollout: beta site 15 Jul 2026; migration in phases with load tests; no public cutover date (B2, B3).

## 5. Cost data
| Item | Figure | Status |
|------|--------|--------|
| New PRS programme cost | Rs 1,000 cr | One news source (B7), unconfirmed |
| PRS Modernisation Phase-2 allocation | Rs 183 cr (2022) | B7 only |
| Convenience fee (fee is the funding for website upkeep per IRCTC) | Rs 802 / 863 / 954 cr (FY23 / FY24 / FY25) | RTI via B6; Rs 15+GST non-AC, Rs 30+GST AC |
| E-tickets booked FY25 | 5,065 lakh | B8 |
| Cloud hosting cost | **Not disclosed** | Week 3: estimate with provider pricing calculators |

## 6. Outcome data
| Measure | Result | Status |
|---------|--------|--------|
| Tatkal confirmed-availability time | +65% on 322 trains (online Aadhaar-OTP) | Official reply (B1) |
| Counter OTP trains | 211 (as of 4 Dec 2025); availability time up on about 95% of 96 popular trains | B1 |
| Beta Tatkal completion | >5% more within 3 min; about 3% within 5 min | News, Aug 2026 (B2) |
| 1.5 lakh/min capacity | Target, not yet demonstrated | A1, A2 |

## 7. Open questions for Week 2
1. Is the new PRS on public cloud, MeitY-empanelled cloud, or CRIS data centres?
2. Read Lok Sabha Q2787 (A3) and find the 11 Dec 2025 reply.
3. Find the PIB PRID 2295409 backgrounder and any CRIS tender/publication describing the platform.
4. Get a real observed peak (tickets/min at a Tatkal window) from an official source.
