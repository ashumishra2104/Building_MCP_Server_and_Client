"""
Backfill STAR Achievement Bank v2 — 25 stories from Ashu_Story_Bank_22_Stories.pdf
Clears all existing stories for demo@nomail.com and inserts the full updated set.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import clear_star_stories, save_star_stories

USER_EMAIL = "demo@nomail.com"
SOURCE_FILE = "Ashu_Story_Bank_22_Stories.pdf"

STORIES = [
    # ── ELASTICRUN ──────────────────────────────────────────────────────────────
    {
        "company": "ElasticRun",
        "project_name": "P&L Ecosystem — 180 Warehouses",
        "situation": (
            "ElasticRun had 180 warehouses with no P&L visibility. Everything tracked manually "
            "on Excel — 4-5 day lag, editable by anyone. Leadership had no real-time view of "
            "which warehouses were profitable."
        ),
        "task": (
            "Two responsibilities: First, build the P&L framework from scratch — no template "
            "existed. Second, once built, drive profitability at warehouses."
        ),
        "action": (
            "Built P&L from scratch. Analyzed all cost types per warehouse — used only costs "
            "directly attributable (not apportioned). Worked with finance to identify cost centres "
            "(logistics, manpower, rent). Worked with engineering to digitize and create real-time "
            "dashboard. Presented to leadership. Then analyzed which 10 WHs had highest profitability "
            "potential. Worked with WH managers on levers — cost reduction, revenue increase, SKU mix. "
            "Tracked weekly with leadership."
        ),
        "result": (
            "Within 3 months — P&L dashboard live for all 180 WHs. Real-time visibility for "
            "leadership and investors. 10 warehouses turned profitable in same period."
        ),
    },
    {
        "company": "ElasticRun",
        "project_name": "Brand/Focus/Value — Medal Framework",
        "situation": (
            "Salespeople hit volume targets but margin stuck at 4.5-5%. No SKU-level guidance, "
            "no margin KPI. FMCG price-sensitive — can't raise prices. Salespeople selling "
            "low-margin SKUs because no system told them otherwise."
        ),
        "task": "Increase margin 4.5%→7.5% by changing basket composition in 6 months without changing prices.",
        "action": (
            "Field visits with salespeople. Analyzed margin levers. Built Medal Framework — Brand "
            "(high margin), Focus (liquidation), Value (revenue). Medal targets per SKU category. "
            "Tied medals to margin and SKU composition variety. Caught vanity metric mid-launch — "
            "salespeople gaming the system by selling only Brand SKUs. Fixed with backend threshold "
            "guardrail: minimum threshold of Value SKUs required before medal unlocks."
        ),
        "result": (
            "Margin 4.5%→7.5%. Items per invoice 7→12. 80-90% adoption in 6 months. "
            "Incentives streamlined."
        ),
    },
    {
        "company": "ElasticRun",
        "project_name": "SKU-Warehouse Bulk Mapping",
        "situation": (
            "SKU tagging across warehouses took 1+ day with 3 team members. Manual, slow, "
            "causing sales delays across the network."
        ),
        "task": "Automate mapping — reduce from 1 day to under 3 hours.",
        "action": (
            "Analyzed SKU distribution patterns. Category-based clubbing logic. Worked with "
            "engineering to build one-to-many bulk upload — one bouquet of SKUs mapped to "
            "multiple warehouses simultaneously."
        ),
        "result": "1 day → 2-3 hours. 3 team members freed from repetitive work. Sales delays eliminated.",
    },
    {
        "company": "ElasticRun",
        "project_name": "Sales Manager App — WhatsApp to Mobile",
        "situation": (
            "Salespeople had mobile app for order taking and metrics. Managers had no mobile "
            "visibility — relied on laptops. Managers on field could only see reports by evening "
            "— too late to act. They managed via WhatsApp groups — 7-8 salespeople × 10 shops "
            "= 70-80 photos/day to scroll through."
        ),
        "task": "Build a manager-facing app giving real-time team visibility on field.",
        "action": (
            "Went on sales beat with managers. Understood daily KPIs and how they tracked team. "
            "Discovered WhatsApp chaos. Designed wireframes. Got feedback from managers. "
            "Documented and handed to engineering."
        ),
        "result": (
            "App delivered in 2 months. Same as sales app but different login. 90-95% manager "
            "adoption within 2 weeks — managers were involved from day one."
        ),
    },
    {
        "company": "ElasticRun",
        "project_name": "STR Bulk Upload",
        "situation": (
            "55Cr inventory across 35 warehouses needed reverse pickup. Ops team max 500 STRs/day "
            "but 700 needed — gap of 200."
        ),
        "task": "Close the 200 STR/day gap. NOT my direct charter — I owned product, not ops workflow.",
        "action": (
            "Sat with ops team. Documented process end-to-end. Brought engineering in. "
            "Identified bulk upload as solution. Personally drove the build."
        ),
        "result": "Shipped in 1 week. Team hit 700 STRs/day. Reverse logistics unblocked. 55Cr capital protected.",
    },
    {
        "company": "ElasticRun",
        "project_name": "55Cr Reverse Supply Chain",
        "situation": (
            "55Cr near-expiry FMCG across 150 spokes. Expiring in 6 months. Spoke liquidation "
            "= 10-20% MRP. Hub = 50% MRP. No reverse logistics existed."
        ),
        "task": "Move inventory to hubs and liquidate at hub rates within 6 months. No playbook.",
        "action": (
            "Pareto: 50 spokes had 90% of problem. Used backhaul trucks (going empty) as free "
            "reverse logistics. Built vehicle return rate KPI on daily scorecard. Transparency "
            "dashboard. Dynamic discount engine (expiry-based, margin floor guardrail)."
        ),
        "result": "55Cr liquidated in 4 months. Failure rate 20%→5%. Zero write-off. Capital reinvested.",
    },
    {
        "company": "ElasticRun",
        "project_name": "SMART Basket — Recommendation Engine",
        "situation": (
            "Salespeople carried paper slips with previous retailer SKUs. 80% retailers within "
            "5km buy 90% same SKUs. AUV stuck at 1000. All traditional levers exhausted."
        ),
        "task": "Grow AUV 1000→1200 in 6 months.",
        "action": (
            "Field observation. Paper slip insight. Data validation (80-85% SKU similarity across "
            "nearby retailers). Simulation. Built recommendation engine. Piloted. National rollout "
            "in 4 months."
        ),
        "result": (
            "AUV 1000→1200 (20% uplift). Margin 5%→7.5%. 97% adoption. "
            "9% actual MoM growth vs 7.5% forecast."
        ),
    },

    # ── MEDIKABAZAAR ────────────────────────────────────────────────────────────
    {
        "company": "Medikabazaar",
        "project_name": "Procurement Platform — USD 130M",
        "situation": (
            "300Cr procurement/month, no guardrails. 65L/month leaking silently. "
            "Excess inventory piling up."
        ),
        "task": "Introduce controls without slowing procurement speed.",
        "action": (
            "1.5 days with procurement officers. Built unified dashboard. L1/L2 approval "
            "thresholds. Auto-vendor selection. Sat with team daily to drive adoption."
        ),
        "result": "65L→10-15L/month loss. USD 130M WC unlocked. 7-8→12-14 POs/day. 90% adoption.",
    },
    {
        "company": "Medikabazaar",
        "project_name": "Seller Portal Interest Form Pushback",
        "situation": "3P portal launching Dec 31. First design came back with only name + phone. I rejected it.",
        "task": "Needed SKU type, catalog size, business stage for procurement to evaluate sellers properly.",
        "action": (
            "Explicitly rejected design. Told team: does not meet standards. Willing to delay "
            "launch. Design iterated in 3 days."
        ),
        "result": "Launched on time Dec 31. Procurement evaluation 3x more efficient.",
    },
    {
        "company": "Medikabazaar",
        "project_name": "3P Seller Portal",
        "situation": "Shifting to 3P model. No platform existed for sellers to view orders, accept, invoice.",
        "task": "Build seller portal from scratch in 6 months.",
        "action": (
            "Seller interviews. Competitive research. 3 MVP modules. PRD. Tested 1000 invoices. "
            "Admin revert feature post-launch."
        ),
        "result": "Launched Dec 31. 0→20Cr GMV in 3 months. 99.5% invoice accuracy.",
    },
    {
        "company": "Medikabazaar",
        "project_name": "Payment Orchestration — Success Rate 99.5%",
        "situation": (
            "E-commerce goal: scale 5Cr to 18Cr/quarter. Funnel data showed 40% drop-off from "
            "cart to completion. Two technical blockers: high latency in JusPay and lack of "
            "acceptance for doctor-exclusive IMA cards."
        ),
        "task": "Eliminate payment friction by solving latency and gateway incompatibility in parallel within one month.",
        "action": (
            "Conducted qualitative interviews with 20+ users. Fixed JusPay timeout issues by "
            "implementing retry logic and gateway failovers with engineering. Analyzed spikes "
            "exceeding 2 seconds causing user timeouts. Deployed automated retry logic and fallback "
            "routing to alternative gateways. Sourced and integrated a specialized bank API to "
            "support IMA-issued cards — specialized doctor cards were failing on standard rails. "
            "Rapidly integrated IMA-specific bank APIs within 2 weeks to unblock doctor transactions."
        ),
        "result": (
            "Success rate hit 99.5%. Revenue target of 18Cr achieved. "
            "Integration expanded to 100+ banking partners."
        ),
    },
    {
        "company": "Medikabazaar",
        "project_name": "Catalog Quality — Image Overhaul",
        "situation": (
            "3 lakh SKUs, 1.5 lakh with only 1 image. 90% users scroll images first (Mixpanel). "
            "Leadership said: fix descriptions first (3 months)."
        ),
        "task": "Increase scorecard 50%→80%. Leadership's plan = 90 days. I believed images were the real problem.",
        "action": (
            "Showed Mixpanel data to leadership. Pushed back knowing it risked delay. Ran both "
            "in parallel. Found image enhancement API. Deployed without A/B testing — bias for action."
        ),
        "result": "Scorecard 50%→80% in 1 month vs 90 days. 2 lakh SKUs improved. 18Cr revenue hit.",
    },
    {
        "company": "Medikabazaar",
        "project_name": "Lead Management and SKU Visibility",
        "situation": (
            "Medikabazaar had no lead tracking system. Field teams had no method to prioritize "
            "retailer revisits. Product pitches relied on memory — limiting sales to handful "
            "of remembered SKUs."
        ),
        "task": "Build system to systematize lead management and expose full catalog — right prospects, right products.",
        "action": (
            "Built mobile app with two modules. First — lead capture with location and type "
            "(Hot/Warm/Cold) for strategic beat planning. Second — full SKU pipeline. Prioritized "
            "top 1000 SKUs with enhanced images and descriptions."
        ),
        "result": (
            "80% adoption across 200 salespeople within 14 days. Teams shifted to systematic "
            "high-priority lead engagement. Order values increased as salespeople started pitching "
            "the full catalog instead of 5-6 remembered SKUs."
        ),
    },
    {
        "company": "Medikabazaar",
        "project_name": "Order Management Automation",
        "situation": (
            "Orders arrived via manual emails. 5-person ops team manually searched SKUs, verified "
            "UOMs, made 3+ calls per order. Latency 48 hours. Completely unscalable."
        ),
        "task": "Automate order lifecycle — reduce processing from 2 days to under 3 hours.",
        "action": (
            "Integrated requisition logic into SKU listing page. Salespeople input quantity/price "
            "directly — system auto-fetches UOM, GST, SKU metadata. Ops team received complete "
            "structured orders."
        ),
        "result": "Cycle time 1 day → 2 hours. Full ops team freed from manual overhead. 100% clarification calls eliminated.",
    },
    {
        "company": "Medikabazaar",
        "project_name": "Seller Onboarding Platform",
        "situation": (
            "Medikabazaar onboarding 10-15 sellers daily in manual fashion. GST, PAN, bank details "
            "not being validated — vendor payments got delayed. Manual onboarding was not just an "
            "efficiency problem — it was a trust problem. Sellers didn't get paid on time because "
            "their details weren't validated."
        ),
        "task": (
            "Create a seller onboarding platform for in-house sellers from scratch to improve "
            "cash payment and provide visibility."
        ),
        "action": (
            "Understood the whole flow, identified 60% of columns were never used but only present — "
            "eliminated them. Analysed necessary documents and authentication methods. Researched and "
            "integrated APIs to authenticate GST, PAN, and bank details in real time along with OCR."
        ),
        "result": "Onboarding time reduced from 1-2 days to 2-3 hours. Vendor payments improved significantly.",
    },

    # ── ZIGRAM ──────────────────────────────────────────────────────────────────
    {
        "company": "Zigram",
        "project_name": "Multilingual NLP Pipeline — 4 Months",
        "situation": (
            "Zigram English-only. GCC and Philippines required multilingual — make-or-break for "
            "banks and insurance clients. Timeline: 4 months. English pipeline took 3 years."
        ),
        "task": "Build multilingual in 4 months or lose market opportunity.",
        "action": (
            "Deep dive: 95% of target market speaks 3 languages. Reuse vs rebuild — reuse 6 of "
            "7 modules. 1 module genuinely new. Set expectation with leadership and sales team."
        ),
        "result": "3 languages delivered on time. USD 300K revenue in first quarter. 100 clients in pursuit.",
    },
    {
        "company": "Zigram",
        "project_name": "3M USD Contract Rescue",
        "situation": (
            "3M USD US client contract at risk. 2 engineers left abruptly. Code machine deleted "
            "by DevOps mistake. 80% of work due Nov-Dec."
        ),
        "task": "Deliver 50 sources in 45 days with 2 engineers or lose contract renewal.",
        "action": (
            "Communicated to leadership immediately. Prioritized 30 sources (>5% change). "
            "Transparent scope change to client. Daily micro-tasks: script→process→push→validate. "
            "Worked through Christmas."
        ),
        "result": "30 sources delivered by Dec 31. Contract renewed with higher confidence. Leadership recognition.",
    },
    {
        "company": "Zigram",
        "project_name": "LLM News Search Enhancement",
        "situation": (
            "Client needed deeper news coverage in Dubai/GCC. System bottlenecked. "
            "10-15 complaints/day. Traditional fix = months of new scraping infrastructure."
        ),
        "task": "Find faster solution without infrastructure overhaul.",
        "action": (
            "Explored LLM as alternative. Built entire prompt from scratch. Created golden dataset "
            "(100+ cases). Validated accuracy >95%, response time <10 seconds. Deployed to production."
        ),
        "result": "Deployed in weeks vs months. Complaints 10-15→2-3/day. More value without new infrastructure.",
    },
    {
        "company": "Zigram",
        "project_name": "Profile Builder Failure — PEP Dataset",
        "situation": (
            "Task: expand PEP database 5.3M→6.3M using Wikipedia/Wikidata. Relied on AML team "
            "requirements without validating independently."
        ),
        "task": "Deliver 1M new PEP profiles for compliance database.",
        "action": (
            "Scraped 5.5M records over 2 months. At delivery: 4 critical data fields missing. "
            "Entire dataset unusable. My mistake — didn't probe the why behind requirements."
        ),
        "result": (
            "2 months of work wasted. Changed behavior: requirements alignment doc now mandatory "
            "— every field probed, signed off by ops + engineering + end user before any code written."
        ),
    },
    {
        "company": "Zigram",
        "project_name": "Document Fetcher UX — 40 to 80 Percent Adoption",
        "situation": (
            "5.3M profiles for financial client. 400 people across time zones. Target: 45→60 "
            "profiles/day. Only 40% using document fetcher."
        ),
        "task": "Increase adoption without waiting 3 months for analytics pipeline.",
        "action": (
            "Chose qualitative research over waiting for data. Interviewed 15 users — high (>80%) "
            "and low (<35%) adopters. Root cause: multiple screens = lost attention. Built wireframes. "
            "Stakeholder buy-in. 2 sprints to deliver."
        ),
        "result": "Adoption 40%→80%. Profiles 45→50/day. Bottleneck shifted to data availability (external, not tool).",
    },
    {
        "company": "Zigram",
        "project_name": "Google News Article Ingestion Tool",
        "situation": (
            "Adverse news pipeline missing recent articles (published 3-4 hrs ago). "
            "Sales/implementation teams got client complaints: 'Why is this not showing?' Trust at risk."
        ),
        "task": "Fix recent article gap without waiting for full pipeline cycle.",
        "action": (
            "Mapped manual process — 7 APIs called sequentially, 1-2 hours per article. Was "
            "learning Claude Code at this time. Applied learning in real time — built single "
            "dashboard: paste URL → all 7 APIs + LLM → database automatically."
        ),
        "result": "Ingestion time 1-2 hours → under 30 seconds. Teams fully self-serve. Client complaints dropped significantly.",
    },
    {
        "company": "Zigram",
        "project_name": "Profile Builder UX Overhaul",
        "situation": (
            "Profile Builder ML platform promised 33% efficiency. Only 20-25 of 100 users "
            "adopting (25%). Tool existed, value existed, adoption stuck."
        ),
        "task": "Understand why 75% not using it and fix it.",
        "action": (
            "Interviewed high adopters (>80%) and low adopters (<20%). Root cause: multiple "
            "screens = lost attention span. Built universal workflow platform — all utilities on "
            "one screen. Working prototype shown to users. Got buy-in. Delivered in 2 months."
        ),
        "result": "Adoption 25%→70%. Profile creation 45→60/day. 33% efficiency target on track.",
    },
    {
        "company": "Zigram",
        "project_name": "News Pipeline Stability — Failure Rate Fix",
        "situation": (
            "News search pipeline failing at high load. RPS>10, 2 lakh daily requests. "
            "Failure rate >10% at 3-4 instances. Client confidence at risk."
        ),
        "task": "Reduce failure rate from >10% to <1% within 4 weeks to prevent SLA breach.",
        "action": (
            "Mapped every failure instance. Dissected to component level. Found database as "
            "bottleneck. Presented findings with data to engineering leadership. Drove database "
            "architecture changes."
        ),
        "result": ">10%→<0.2% failure rate in 3-4 weeks. System resilient. SLA maintained. Client confidence restored.",
    },
    {
        "company": "Zigram",
        "project_name": "Compliance Automation — 1 to 10 Lists per Day",
        "situation": (
            "1200 compliance lists. 5-person ops team validating 1 list/day manually. "
            "6-month target missed. Engineering blocked."
        ),
        "task": "Meet automation target without adding headcount.",
        "action": (
            "Sat with ops for 3-4 days. Understood process end-to-end. Performed task myself. "
            "Built automated reports matching manual checks 100%. Showed ops team side-by-side "
            "(15-20 files)."
        ),
        "result": "1→10 lists/day. 90% effort reduction. 100% accuracy. Ops team trust earned.",
    },
    {
        "company": "Zigram",
        "project_name": "Watchlist Spacing Bug Fix",
        "situation": (
            "7-8 critical watchlists updated every 7 hours. Failure = unlimited liability. "
            "Spacing bug generating 50-60 fake alerts/day. Engineering patching row by row "
            "(2 lakh rows) — never fixing root cause."
        ),
        "task": "Permanently fix spacing issue. Not my charter — I took it on myself.",
        "action": (
            "Mapped all spacing edge cases (space before, after, between>2). Built Python space "
            "analyzer using Claude Code. Ingested raw data — all errors visible across all fields "
            "at once. Showed engineering team AND manager full scope — systemic, not isolated. "
            "They fixed all databases and root code immediately."
        ),
        "result": (
            "False positives 50-60/day → zero. Ops team freed. Unlimited liability eliminated. "
            "Engineering started including me in technical reviews."
        ),
    },
]


if __name__ == "__main__":
    print(f"Clearing existing stories for {USER_EMAIL}...")
    clear_star_stories(USER_EMAIL)
    print("Cleared.")

    print(f"Saving {len(STORIES)} stories...")
    saved = save_star_stories(USER_EMAIL, STORIES, source_file=SOURCE_FILE)
    print(f"Done — {saved}/{len(STORIES)} stories saved.")
