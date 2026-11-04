# IT457 Task 1: IRCTC Cloud Scaling for Tatkal Booking

**Group Number: 40**

**Team Members:** Aarya Shah (202301036) · Visha Sitapara (202301414) · Krish Dhola (202301189)

## 1. Case Study Overview

Our assigned case examines how Indian Railways is upgrading its Passenger Reservation System (PRS) to handle high online booking demand, especially Tatkal booking peaks. The PRS is built and maintained by the Centre for Railway Information Systems (CRIS); IRCTC provides the online booking website and app. The system handled 65.08 crore reserved tickets between June 2025 and June 2026, with about 89% booked online. [1]

## 2. Problem and Motivation

Tatkal booking opens at 10:00 for AC classes and 11:00 for non-AC classes, creating short, concentrated traffic bursts. The legacy PRS generation was deployed in 2010 on Itanium servers running OpenVMS. Official figures report current capacity of about 32,000 bookings and 4 lakh enquiries per minute. Peak demand strains infrastructure designed for an earlier era. [1, 2]

## 3. Architecture and Modernization Approach

CRIS is developing a new PRS described by the Ministry of Railways as “cloud-enabled” and designed for ten times the current load. Published targets are more than 1.5 lakh bookings and 40 lakh enquiries per minute. A redesigned IRCTC website entered beta in July 2026; phased train migration began in August 2026, with load testing. Public sources reviewed do not identify the cloud provider or disclose the new PRS’s internal architecture. [1, 2]

Demand-shaping measures include Aadhaar authentication for Tatkal from July 2025, OTP verification, and a 30-minute restriction on agent bookings after each window opens. Reports quoting official replies say over 3.02 crore suspicious accounts were deactivated. [3, 4]

## 4. Reported Outcomes

- Tatkal confirmed-availability time increased on about 65% of the 322 trains with Aadhaar-OTP (and about 95% of 96 popular trains), per the Ministry of Railways release of 11 Dec 2025. [3]
- Early beta reporting showed over 5% more Tatkal bookings completed within three minutes and about 3% more within five minutes. [4]
- The full new-system capacity target remains a target; it has not yet been publicly demonstrated at peak Tatkal load. [1, 2]

## 5. Cost and Business Impact

No official cost for the new PRS or its cloud hosting was found in the sources reviewed. A Rs 1,000 crore programme estimate appears in one news report and is not corroborated by the official sources. RTI-based reporting lists convenience-fee revenue of Rs 954 crore in FY25 and Rs 2,619 crore over FY23–FY25. A verified total-cost or savings comparison is not possible from the available information. [5, 6]

## 6. Key Lessons and Practical Exercise

The case shows that scaling involves both adding system capacity and shaping demand. Our proof-of-concept will model a Tatkal-like burst using a simple booking API behind a load balancer with autoscaling. We plan to generate traffic with Locust or k6, record response time against instance count, and explore rate limiting or a waiting queue. This is our proposed exercise architecture, not a claim about IRCTC’s production design.

## Sources

[1] Ministry of Railways, PIB, [“Four Decades of Passenger Reservation in Indian Railways”](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=159450&ModuleId=3&reg=48&lang=1) (6 Aug 2026).

[2] Ministry of Railways, PIB, [“New Passenger Reservation System capable of generating over 1.5 lakh rail tickets per minute”](https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2140614&reg=3&lang=2) (29 Jun 2025).

[3] Free Press Journal / IANS, [Lok Sabha reply on Aadhaar-OTP and suspicious IDs](https://www.freepressjournal.in/tech/aadhaar-otp-boosts-tatkal-fairness-irctc-blocks-302-cr-fake-ids-availability-jumps-65) (Dec 2025).

[4] Business Today, [new booking system beta and early results](https://www.businesstoday.in/latest/trends/photo/indian-railways-new-ticket-booking-system-will-be-5x-faster-heres-whats-changing-for-irctc-users-548374-2026-08-11) (11 Aug 2026).

[5] Punekar News, [RTI-based convenience-fee figures](https://www.punekarnews.in/irctc-website-revamp-announced-after-rti-exposes-rs-2619-crore-convenience-fee-earnings/) (17 Jun 2026).

[6] Zee News, [reported Rs 1,000 crore estimate](https://zeenews.india.com/photos/mobility/end-of-tatkal-ticketing-booking-woes-indian-railways-spends-rs-1000-cr-to-revamp-40-year-old-irctc-reservation-system-increases-capacity-to-handle-1-25-lakh-tickets-per-minute-3027416) (16 Mar 2026).

**Evidence note:** Official sources establish system history and announced capacity targets. Outcomes and cost figures attributed to news reports are secondary reporting and are not independently audited here. A vendor case study mentioning AWS is not evidence that IRCTC’s production booking system runs on AWS.
