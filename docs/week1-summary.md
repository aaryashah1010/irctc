# Week 1 Deliverable: IRCTC Cloud Scaling for Tatkal Booking

**Course:** IT457 Cloud Computing | **Case:** IRCTC, Scalability & High-Traffic Events | **Details:** `docs/sources.md`, `docs/week1-research-notes.md`

## 1. Sources found
13 source entries in 4 grades (full list in `sources.md`):
- **Official (3):** two PIB releases (29 Jun 2025 and 6 Aug 2026) and Lok Sabha Unstarred Question 2787 (6 Aug 2025).
- **News quoting officials (8):** Lok Sabha reply on Tatkal bots (Dec 2025), beta-launch and migration reports (Aug 2026), RTI on convenience fees (Jun 2026), and the Aadhaar/OTP circular coverage (Jun 2025).
- **Vendor (2):** CloudThat's AWS security case study for IRCTC; the Red Hat award for CRIS (2014).
- **Context only:** system-design blogs, used for our own design but not as facts about IRCTC.

## 2. Salient points
1. **Who runs what.** The Passenger Reservation System (PRS, since 1986) is built and maintained by CRIS. IRCTC is the online front-end (website and app) for booking on it. Booked from Jun 2025 to Jun 2026: 65.08 crore reserved tickets, 89% online; about 20.5 lakh passengers/day.
2. **Problem.** Tatkal opens at 10:00 (AC) and 11:00 (non-AC), producing a burst far above average load. PIB says peak Tatkal demand puts pressure on "infrastructure originally designed for a different era". The legacy PRS dates from 2010 on Itanium servers and OpenVMS.
3. **Capacity numbers.** Official figures: bookings 32,000/min now, over 1.5 lakh/min target (about 5x). Enquiries 4 lakh/min now, over 40 lakh/min target (10x). The design goal is "ten times the current load" (PIB, Jun 2025).
4. **Solution on the demand side (reduce bots, shape traffic).** Aadhaar-authenticated Tatkal from 1 Jul 2025, OTP from 15 Jul 2025, agents blocked for the first 30 minutes of each window, advance reservation period cut from 120 to 60 days. Over 3.02 crore suspicious IDs deactivated since Jan 2025. Akamai anti-bot filtering, WAF and application delivery controllers are in place.
5. **Solution on the supply side (scale the system).** A new "cloud-enabled, next-generation" PRS built by CRIS, with a redesigned IRCTC website (beta live 15 Jul 2026). Migration of trains began in Aug 2026, in phases, with load testing before the old PRS is retired.
6. **Outcome so far.** Tatkal confirmed-availability time up about 65% on 322 trains with Aadhaar-OTP (Dec 2025). Early beta: Tatkal bookings completed within 3 minutes up over 5% and within 5 minutes up about 3% (Aug 2026 reports). The full capacity target is a projection and is **not yet proven** at Tatkal peak.
7. **Cost.** No official cost for the new PRS found. Rs 1,000 cr appears in one news report only. Revenue side (RTI): convenience fees Rs 954 cr in FY25, Rs 2,619 cr over FY23-FY25.
8. **Evidence gap.** No official source gives the new PRS's internal architecture or cloud provider. The only AWS-specific item is a partner security case study with no numbers. Do not claim "IRCTC runs on AWS".
9. **Link to our exercise.** The Tatkal burst maps to the assigned exercise: a booking app behind a load balancer with autoscaling, a Locust/k6 load test, and response time plotted against instance count. We also add the demand-side lesson (rate limiting and queueing) as an experiment.

## 3. Not to be cited as fact
37,410 tickets in one minute (blog), 2 crore simultaneous users (unverified), Rs 1,000 cr / Rs 146 cr project cost, "23 million passengers/day" (PIB says 20.5 lakh), any claim that IRCTC runs on Kubernetes or AWS.
