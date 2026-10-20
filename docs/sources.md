# Week 1: Sources Found (IRCTC / PRS cloud scaling case study)

Accessed 2026-10-20. Grade: **A** = official government or Parliament record (read directly), **B** = news report quoting an official statement, **C** = vendor or partner marketing, **D** = blog or hypothetical design (context only).

## Primary / official sources (grade A)

| ID | Source | Date | Used for |
|----|--------|------|----------|
| A1 | [PIB, Ministry of Railways: "New Passenger Reservation System capable of generating over 1.5 lakh rail tickets per minute..."](https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2140614&reg=3&lang=2) (PRID 2140614) | 29 Jun 2025 | Current vs target capacity (32,000 -> 1.5 lakh bookings/min; 4 lakh -> 40 lakh enquiries/min), "ten times the current load" design goal, CRIS as executor, Tatkal authentication, advance charting |
| A2 | [PIB backgrounder: "Four Decades of Passenger Reservation in Indian Railways"](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=159450&ModuleId=3&reg=48&lang=1) | 6 Aug 2026 | PRS history and milestones, legacy platform (2010, Itanium + OpenVMS), usage stats, "cloud-enabled next-generation" PRS, Aug 2026 phased migration, new IRCTC beta site (Jul 2026), CRIS profile |
| A3 | [Lok Sabha Unstarred Question 2787, answered 6 Aug 2025 (eparlib.sansad.in)](https://eparlib.sansad.in/bitstream/123456789/2994533/1/AU2787_Ak5anh.pdf) | 6 Aug 2025 | Official reply on Aadhaar authentication for Tatkal (found but **not yet read in full**; read it in Week 2) |

## Reports quoting official statements (grade B)

| ID | Source | Date | Used for |
|----|--------|------|----------|
| B1 | [Free Press Journal / IANS: Lok Sabha reply on Aadhaar-OTP and fake IDs](https://www.freepressjournal.in/tech/aadhaar-otp-boosts-tatkal-fairness-irctc-blocks-302-cr-fake-ids-availability-jumps-65) (also [All India Radio](https://www.newsonair.gov.in/government-deactivates-over-3-crore-suspicious-railway-user-ids/)) | 11-12 Dec 2025 | 3.02 crore suspicious IDs deactivated since Jan 2025; Tatkal confirmed-availability time +65% on 322 trains; Akamai, WAF, ADC, IPS, CERT-In audits |
| B2 | [Business Today: new ticket booking system 5x faster](https://www.businesstoday.in/latest/trends/photo/indian-railways-new-ticket-booking-system-will-be-5x-faster-heres-whats-changing-for-irctc-users-548374-2026-08-11) | 11 Aug 2026 | Beta site live 15 Jul 2026; early beta Tatkal results (+5% within 3 min, +3% within 5 min); phased, load-tested migration |
| B3 | [Deep Arrival: upgraded PRS migration](https://deeparrival.com/news/indian-railways-upgraded-prs-migration-august-2026/) | 11 Aug 2026 | Layer-by-layer migration with load testing before the old PRS is retired; no public train-by-train calendar |
| B4 | [NewKerala / ANI: new IRCTC website](https://www.newkerala.com/news/a/will-significantly-improve-ticket-booking-efficiency-zrucc-southern-223.htm) | 14 Jun 2026 | Minister's announcement of new website; "cloud-based" PRS |
| B5 | [Scroll](https://scroll.in/latest/1083421/scroll_in), [Deccan Chronicle](https://www.deccanchronicle.com/amp/nation/only-aadhar-authenticated-users-can-book-tatkal-tickets-from-july-1-railway-ministry-1884659), [Mobile ID World](https://mobileidworld.com/irctc-mandates-aadhaar-otp-authentication-for-tatkal-train-bookings-from-july-2025/) | Jun 2025 | Aadhaar auth from 1 Jul 2025, OTP from 15 Jul 2025, agent blackout windows (10:00-10:30 AC, 11:00-11:30 non-AC) |
| B6 | [Punekar News: RTI on convenience fees](https://www.punekarnews.in/irctc-website-revamp-announced-after-rti-exposes-rs-2619-crore-convenience-fee-earnings/) | 17 Jun 2026 | Cost/revenue side: convenience fee Rs 802 cr (FY23), 863 cr (FY24), 954 cr (FY25) from an RTI response |
| B7 | [Zee News: Rs 1,000 cr revamp](https://zeenews.india.com/photos/mobility/end-of-tatkal-ticketing-booking-woes-indian-railways-spends-rs-1000-cr-to-revamp-40-year-old-irctc-reservation-system-increases-capacity-to-handle-1-25-lakh-tickets-per-minute-3027416) | 16 Mar 2026 | Only source for the Rs 1,000 cr figure, Rs 183 cr PRS Phase-2 (2022), open-source Red Hat stack. **Cost figures not corroborated by PIB.** |
| B8 | [IRCTC Internet Ticketing page](https://irctc.com/internet-ticketing.php), via [Medianama Q4 FY25 call](https://www.medianama.com/2025/06/223-earnings-call-irctc-q4fy25-segment-wise-revenue-analysis-rs-358-crore-profit/) | 2025 | 5,065 lakh e-tickets in FY25; ~87% of tickets booked via IRCTC portal (Q3 FY25) |

## Vendor / partner (grade C)

| ID | Source | Used for |
|----|--------|----------|
| C1 | [CloudThat case study: AWS security services for IRCTC](https://www.cloudthat.com/resources/case-study/strengthening-defenses-against-common-web-exploits-and-malicious-ips-with-aws-security-services-for-irctc) (undated, no figures) | Bot defense, DDoS, EKS, WAF, Shield, GuardDuty, Control Tower. Security-focused, not capacity-focused. |
| C2 | [Red Hat Innovation Award for CRIS (2014)](https://indianrlynews.wordpress.com/2014/05/04/indian-railways-online-services-more-reliable-and-scalable-with-open-source-standards/) | RHEL used under mission-critical booking systems; NGeT-era architecture |

## Context only (grade D, do not cite as fact about IRCTC)

- [Medium: IRCTC Tatkal High-Level System Design](https://shubhamshrii.medium.com/irctc-tatkal-ticket-booking-high-level-system-design-9a78eb4b0afd), [SystemDesign Academy](https://www.systemdesign.academy/interview/design-irctc), [Medium: How IRCTC handles crores of users](https://medium.com/thesystemdesign/how-irctc-handles-crores-of-users-during-tatkal-booking-f5209531c5cd): hypothetical designs (waiting room, queue tokens, autoscaling). Useful for our own exercise design.
- [PubAdmin Institute: Evolution of PRS](https://pubadmin.institute/electronic-governance/evolution-indian-railways-passenger-reservation-system): legacy three-tier design, regional centres (Delhi, Mumbai, Kolkata, Chennai, Secunderabad). Verify before citing.
- [CIO.com: IRCTC's new servers](https://www.cio.com/article/218286/how-irctc-s-new-servers-make-bookings-and-enquiries-easier.html): old (about 2019) figures, e.g. ~7,000 tickets/min then. Historical only.
- [Samachar News](https://thesamacharnews.com/irctc-new-booking-system-2026-tatkal-upgrade/): claims 2 crore simultaneous users and 3 crore load test. **Unverified. Do not use.**

## Gaps to close in Week 2
1. Read Lok Sabha Q2787 (A3) and find the 11 Dec 2025 reply on sansad.in.
2. Still **no official document** on the new PRS's internal architecture (containers, database, cloud provider). PIB says only "cloud-enabled". Check CRIS (cris.org.in) tenders/publications and PRID 2295409.
3. Confirm whether the new PRS runs on public cloud or government/MeitY cloud. Not stated anywhere official found so far.
