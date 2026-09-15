#!/usr/bin/env python3
"""Generate the four SEO landing pages (2026-09-15) by cloning faq.html chrome
(head scripts, ads, nav, footer, widgets) so look/behavior match the site
exactly. Only meta, styles-extension, and container content differ.
Run AFTER seo_20260915.py (expects clean-URL internal links in faq.html).
"""
import re, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://immilane.com"

chrome = (ROOT / "faq.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "data" / "dashboard_data.json").read_text())

# --- baked baseline values (JS refreshes them on load) ---
dol = data["dol"]
yr = "20" + re.search(r"'(\d\d)", dol["label"]).group(1)
FRONTIER = f"{dol['monthFull']} {yr}"                    # November 2025
PCT = f"{dol['pctProcessed']}%"
REMAIN = f"{dol['casesRemaining']:,}"
AVG = f"{data['avgDays']['current']}"
AVG_CERT = f"{data['avgDays']['certified']}"
PENDING = f"{data['backlog']['total']:,}"
TODAY_TOTAL = f"{data['today']['total']:,}"
MOVE = f"{dol['movementPerWeek']}"
# frontier-month status distribution (tabKey "next" == month DOL is working)
nxt = next((t for t in data["statusDistribution"] if t["tabKey"] == "next"), None)
NX = {k: f"{nxt[k]:,}" for k in ("certified", "review", "withdrawn", "rfi", "denied")} if nxt else {}
NX_MONTH = FRONTIER

EXTRA_CSS = """
  /* landing-page components (SEO pages, 2026-09-15) */
  .hero .eyebrow { font-size: 14px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
  .hero h1 { font-size: 28px; font-weight: 700; letter-spacing: -0.5px; text-transform: none; background: linear-gradient(135deg, var(--text-primary), var(--text-secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .lede { font-size: 15px; color: var(--text-secondary); line-height: 1.7; margin: 4px 0 22px; max-width: 740px; }
  .lede a, .live-note a { color: #3b82f6; text-decoration: none; }
  .lede a:hover, .live-note a:hover { text-decoration: underline; }
  .live-strip { display: flex; flex-wrap: wrap; gap: 12px; margin: 4px 0 10px; }
  .live-stat { flex: 1 1 150px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; padding: 14px 16px; }
  .live-stat .v { font-size: 21px; font-weight: 700; letter-spacing: -0.5px; }
  .live-stat .l { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; margin-top: 4px; }
  .live-note { font-size: 11.5px; color: var(--text-dim); margin: 0 0 28px; }
  .content { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 32px; margin: 0 0 32px; line-height: 1.8; }
  .content h3 { font-size: 18px; font-weight: 600; margin: 28px 0 12px; color: var(--text-primary); }
  .content h3:first-child { margin-top: 0; }
  .content p { font-size: 14px; color: var(--text-secondary); margin-bottom: 12px; }
  .content ul, .content ol { padding-left: 24px; margin-bottom: 12px; }
  .content li { font-size: 14px; color: var(--text-secondary); margin-bottom: 6px; }
  .content a { color: #3b82f6; text-decoration: none; }
  .content a:hover { text-decoration: underline; }
  .content strong { color: var(--text-primary); }
  .step-list { counter-reset: step; list-style: none; padding-left: 0; }
  .step-list li { counter-increment: step; position: relative; padding-left: 36px; margin-bottom: 14px; }
  .step-list li::before { content: counter(step); position: absolute; left: 0; top: 1px; width: 24px; height: 24px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: #fff; border-radius: 50%; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
  .cta-box { background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.08)); border: 1px solid rgba(59,130,246,0.2); border-radius: 12px; padding: 20px 24px; margin: 0 0 40px; }
  .cta-box p { margin-bottom: 0; font-size: 14px; color: var(--text-secondary); line-height: 1.8; }
  .cta-box a { color: #3b82f6; font-weight: 600; text-decoration: none; }
  .cta-box a:hover { text-decoration: underline; }
  .section-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin: 0 0 12px; }
  @media (max-width: 768px) {
    .hero .eyebrow { font-size: 12px; letter-spacing: 1px; }
    .hero h1 { font-size: 21px; letter-spacing: -0.5px; }
    .content { padding: 24px 18px; }
    .live-stat .v { font-size: 18px; }
  }
"""

LIVE_JS = """
<script>
/* Fill live DOL numbers from the same data file the dashboard uses.
   Static baked values remain if the fetch fails. */
(function () {
  fetch('data/dashboard_data.json').then(function (r) { return r.json(); }).then(function (d) {
    function set(k, v) {
      document.querySelectorAll('[data-live="' + k + '"]').forEach(function (el) { el.textContent = v; });
    }
    var m = (d.dol.label || '').match(/'(\\d\\d)/);
    var yr = m ? '20' + m[1] : '';
    set('frontier', d.dol.monthFull + (yr ? ' ' + yr : ''));
    set('pct', d.dol.pctProcessed + '%');
    set('remain', Number(d.dol.casesRemaining).toLocaleString());
    set('avg', d.avgDays.current);
    set('avgCert', d.avgDays.certified);
    set('pending', Number(d.backlog.total).toLocaleString());
    set('todayTotal', Number(d.today.total).toLocaleString());
    set('move', d.dol.movementPerWeek);
    var nx = (d.statusDistribution || []).filter(function (t) { return t.tabKey === 'next'; })[0];
    if (nx) {
      ['certified', 'review', 'withdrawn', 'rfi', 'denied'].forEach(function (k) {
        set('nx-' + k, Number(nx[k]).toLocaleString());
      });
    }
    if (d.updatedAt) {
      var dt = new Date(d.updatedAt);
      if (!isNaN(dt)) set('updated', dt.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York' }) + ' ET');
    }
  }).catch(function () {});
})();
</script>
"""

def faq_ld(qas):
    return json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]
    }, ensure_ascii=False, separators=(",", ":"))

def faq_html(qas_html):
    items = []
    for i, (q, a) in enumerate(qas_html):
        items.append(
            f'<div class="faq-item{" open" if i == 0 else ""}">\n'
            f'      <div class="faq-question">{q}</div>\n'
            f'      <div class="faq-answer">{a}</div>\n    </div>')
    return '<div class="section-label">Frequently asked</div>\n  <div class="faq-list">\n    ' + "\n\n    ".join(items) + "\n  </div>"

PAGES = {}

# ─────────────────────────── /perm-status-check ───────────────────────────
PAGES["perm-status-check"] = dict(
    title="PERM Status Check — How to Check Your DOL Case | ImmiLane",
    desc="Check your PERM status: what FLAG shows your employer, what you can track yourself, and live DOL processing data covering 207,000+ cases.",
    eyebrow="Live DOL Data", h1="PERM Status Check",
    lede=('There is no public DOL portal where applicants can look up an individual PERM case — '
          'only the sponsoring employer or their attorney can see the official status in FLAG. '
          'What you <em>can</em> do is track exactly where the DOL is in its queue and get alerted '
          'the moment your own case changes. ImmiLane follows 207,000+ PERM cases from the DOL '
          'FLAG system, refreshed throughout the day.'),
    strip=[("frontier", FRONTIER, "DOL now processing"), ("pct", PCT, "Through that month"),
           ("avg", AVG, "Avg days to decision"), ("pending", PENDING, "Cases pending")],
    body=f"""
  <div class="content">
    <h3>How to check your PERM status, step by step</h3>
    <ol class="step-list">
      <li><strong>Find your filing date and case number.</strong> Your employer or attorney received a confirmation when the ETA Form 9089 was filed; the case number looks like G-100-XXXXX-XXXXXX. The filing date is what determines your place in line.</li>
      <li><strong>See which filing month the DOL is working on.</strong> The <a href="./">live dashboard</a> shows the current processing frontier — right now the DOL is adjudicating <strong data-live="frontier">{FRONTIER}</strong> filings and is about <strong data-live="pct">{PCT}</strong> of the way through that month.</li>
      <li><strong>Compare your filing date to the frontier.</strong> Cases are processed roughly in filing-month order (<a href="guide-how-dol-processes-perm">how DOL ordering works</a>), so the gap between your month and the frontier is your queue position.</li>
      <li><strong>Get a date estimate.</strong> The <a href="estimate">estimate tool</a> projects your decision window from your filing date or case number using the DOL&rsquo;s measured pace.</li>
      <li><strong>Watch your specific case.</strong> <a href="subscribe">Case Watch</a> monitors your case number and emails you when the official DOL status changes, so you don&rsquo;t have to keep asking your employer.</li>
    </ol>
    <h3>Who can see the official status</h3>
    <p>The DOL&rsquo;s FLAG system only shows PERM case status to the account that filed it — the employer or the law firm. As the beneficiary, you are not a party to the application, so there is no login for you. Most applicants get updates in one of three ways: periodic checks by their attorney, HR updates, or a tracking service like ImmiLane&rsquo;s <a href="subscribe">Case Watch</a> that watches the public DOL data for their case number.</p>
    <p>Wondering what a status like &ldquo;Analyst Review&rdquo; actually means? See <a href="perm-case-status">what each PERM case status means</a>.</p>
  </div>
  {faq_html([
      ("Can I check my PERM status online myself?",
       'There is no DOL portal for applicants. Your employer or attorney can check FLAG, and ImmiLane&rsquo;s <a href="subscribe">Case Watch</a> can watch your case number and email you when the status changes. The <a href="./">dashboard</a> shows where the DOL queue stands overall.'),
      ("How do I know if my PERM case is close to a decision?",
       f'Compare your filing month to the processing frontier. The DOL is currently working through <span data-live="frontier">{FRONTIER}</span> filings, moving about <span data-live="move">{MOVE}</span>% of a month per week. If your month is next, a decision is typically weeks away, not months.'),
      ("What information do I need to track my case?",
       "Just your filing date, and ideally the G-100 case number from the ETA-9089 filing confirmation. The filing date alone is enough to place you in the queue; the case number lets Case Watch follow your specific case."),
      ("How often does ImmiLane's data update?",
       "ImmiLane scans the DOL FLAG data multiple times every day. Dashboard figures, estimates, and Case Watch alerts all come from the same live dataset."),
  ])}
  <div class="cta-box"><p><strong>Shortcut:</strong> put your filing date into the <a href="estimate">estimate tool</a> for a projected decision window, or turn on <a href="subscribe">Case Watch</a> to get an email the moment your status changes. Also see <a href="perm-processing-time">current PERM processing times</a>.</p></div>
""",
    ld=faq_ld([
        ("Can I check my PERM status online myself?",
         "There is no DOL portal for applicants to look up an individual PERM case. Your employer or attorney can check FLAG, and ImmiLane's Case Watch can monitor your case number and email you when the status changes."),
        ("How do I know if my PERM case is close to a decision?",
         "Compare your filing month to the DOL's processing frontier on ImmiLane's live dashboard. If the DOL is adjudicating the month you filed in, a decision is typically weeks away."),
        ("What information do I need to track my PERM case?",
         "Your filing date, and ideally the G-100 case number from the ETA-9089 filing confirmation. The filing date places you in the queue; the case number allows case-specific tracking."),
        ("How often does ImmiLane's data update?",
         "ImmiLane scans the DOL FLAG data multiple times every day, so dashboard figures, estimates, and Case Watch alerts reflect near real-time DOL processing."),
    ]),
)

# ─────────────────────────── /perm-case-status ────────────────────────────
PAGES["perm-case-status"] = dict(
    title="PERM Case Status — What Each DOL Status Means | ImmiLane",
    desc="PERM case status meanings — certified, analyst review, audit, denied, withdrawn — with live counts from DOL data and what each means for you.",
    eyebrow="Status Guide", h1="PERM Case Status: What Each Status Means",
    lede=(f'Every PERM application in the DOL system carries one status at a time. Here is what each one '
          f'means, what usually happens next, and how many cases hold each status right now among '
          f'<strong data-live="frontier">{FRONTIER}</strong> filings — the month the DOL is currently adjudicating.'),
    strip=[("nx-certified", NX.get("certified", "—"), "Certified"), ("nx-review", NX.get("review", "—"), "Analyst review"),
           ("nx-rfi", NX.get("rfi", "—"), "RFI / audit"), ("nx-denied", NX.get("denied", "—"), "Denied"),
           ("nx-withdrawn", NX.get("withdrawn", "—"), "Withdrawn")],
    body=f"""
  <div class="content">
    <h3>Certified</h3>
    <p>The DOL approved the labor certification — the big green light. The employer has <strong>180 days</strong> to file the I-140 immigrant petition with USCIS before the certification expires. If your case shows Certified, the PERM stage is done.</p>
    <h3>Analyst Review</h3>
    <p>The case is in the DOL&rsquo;s working queue: either waiting for a Certifying Officer or actively being adjudicated. This is the normal state for every case that hasn&rsquo;t been decided yet, and for cases in the current processing month it usually means a decision is close. See <a href="perm-processing-time">how fast the queue is moving</a>.</p>
    <h3>Audit</h3>
    <p>The DOL asked for supporting documentation before deciding — recruitment records, the signed ETA-9089, prevailing wage evidence. Audits add months to the timeline because audited cases sit in a separate, slower queue. Our <a href="guide-perm-audits-rfis">audit and RFI guide</a> covers triggers and typical delays.</p>
    <h3>Denied</h3>
    <p>The application was rejected. The employer can request reconsideration or appeal to BALCA, or simply re-file — many denials are corrected on a second, cleaner filing. A PERM denial attaches to the application, not to you personally.</p>
    <h3>Withdrawn</h3>
    <p>The employer pulled the application before a decision — common after job changes, layoffs, or when a filing error is easier to re-file than to fix.</p>
    <h3>Where these numbers come from</h3>
    <p>The live counts above are the status mix for <strong data-live="frontier">{FRONTIER}</strong> filings in the DOL FLAG data ImmiLane tracks (updated <span data-live="updated">daily</span>). The <a href="./">dashboard</a> shows the same breakdown for every filing month, and <a href="perm-status-check">this guide</a> explains how to check where your own case stands.</p>
  </div>
  {faq_html([
      ("What does Analyst Review mean on a PERM case?",
       'It means your case is in the DOL&rsquo;s active queue — waiting for or under review by a Certifying Officer. It is the default status before a decision and not a sign of a problem.'),
      ("How long does Analyst Review take?",
       f'It depends on where the DOL queue stands relative to your filing month. The DOL is averaging about <span data-live="avg">{AVG}</span> days from filing to decision for current cases. Use the <a href="estimate">estimate tool</a> for your specific date.'),
      ("My PERM was certified — what happens next?",
       'The employer files the I-140 petition with USCIS within 180 days. After I-140 approval, your green card timeline depends on visa number availability — see the <a href="visa-bulletin">Visa Bulletin tracker</a>.'),
      ("Does a denied PERM hurt future applications?",
       "A denial applies to that application, not to you. Employers often re-file with corrected recruitment or forms; the new filing gets a new place in the queue."),
  ])}
  <div class="cta-box"><p><strong>Keep watch automatically:</strong> <a href="subscribe">Case Watch</a> emails you when your case&rsquo;s official status changes, with your position in the queue and an updated estimate. Or check <a href="perm-status-check">how to look up your status</a> anytime.</p></div>
""",
    ld=faq_ld([
        ("What does Analyst Review mean on a PERM case?",
         "Analyst Review means the case is in the DOL's active queue — waiting for or under review by a Certifying Officer. It is the normal pre-decision status, not a sign of a problem."),
        ("How long does Analyst Review take?",
         "It depends on the DOL queue position relative to your filing month. Current cases average roughly 396 days from filing to decision; ImmiLane's estimate tool projects your specific window."),
        ("My PERM was certified — what happens next?",
         "The employer files the I-140 petition with USCIS within 180 days of certification. After I-140 approval, timing depends on visa number availability in the monthly Visa Bulletin."),
        ("Does a denied PERM hurt future applications?",
         "A denial applies to that application, not to the worker. Employers often re-file with corrected recruitment or forms, and the new filing receives its own place in the queue."),
    ]),
)

# ─────────────────────────── /dol-case-status ─────────────────────────────
PAGES["dol-case-status"] = dict(
    title="DOL Case Status — PERM and FLAG Lookup Explained | ImmiLane",
    desc="DOL case status explained: how PERM cases move through the FLAG system, who can look up a case, and live processing data updated daily.",
    eyebrow="FLAG System", h1="DOL Case Status: How PERM Cases Move Through FLAG",
    lede=('The Department of Labor runs foreign-labor programs — PERM, LCA, prevailing wage — through '
          'its FLAG system (Foreign Labor Application Gateway). For PERM, FLAG is where a case&rsquo;s '
          'official status lives from filing to decision. Here is how that status works, who can see it, '
          'and the live state of the DOL&rsquo;s PERM queue.'),
    strip=[("todayTotal", TODAY_TOTAL, "DOL decisions today"), ("frontier", FRONTIER, "Month being processed"),
           ("remain", REMAIN, "Cases left in that month"), ("pending", PENDING, "Total pending")],
    body=f"""
  <div class="content">
    <h3>What a DOL case status is</h3>
    <p>When an employer files a PERM application (ETA Form 9089), the DOL assigns a case number — the familiar <strong>G-100-XXXXX-XXXXXX</strong> format — and the case enters FLAG with a status that updates as it moves: Analyst Review while queued and under adjudication, Audit if documentation is requested, then Certified, Denied, or Withdrawn.</p>
    <h3>Who can look up a DOL case</h3>
    <p>FLAG accounts belong to the filer. The employer and its attorney can log in at flag.dol.gov and see the case; the sponsored worker cannot. The DOL publishes aggregate processing data and quarterly disclosure files, which is the public trail ImmiLane uses — our scanner follows the DOL&rsquo;s PERM data throughout the day and mirrors status movement across 207,000+ cases on the <a href="./">live dashboard</a>.</p>
    <h3>How the DOL works through its queue</h3>
    <p>PERM cases are adjudicated roughly in filing-month order. The DOL is currently deciding <strong data-live="frontier">{FRONTIER}</strong> filings, with <strong data-live="remain">{REMAIN}</strong> cases still open in that month. Decisions land every business day — <strong data-live="todayTotal">{TODAY_TOTAL}</strong> so far today. The full ordering logic is in <a href="guide-how-dol-processes-perm">this guide</a>.</p>
    <h3>Tracking a specific case</h3>
    <p>If you know the case number or the filing date, you can follow your place in the queue with the <a href="estimate">estimate tool</a>, and <a href="subscribe">Case Watch</a> will email you when the DOL status for your case number changes. For what each status label actually means, see <a href="perm-case-status">PERM case status meanings</a>.</p>
  </div>
  {faq_html([
      ("Can I log into FLAG to check my case?",
       "Only the filing employer or attorney has FLAG access for a PERM case. Applicants track progress through their employer, their attorney, or a monitoring service like Case Watch."),
      ("What does a G-100 case number mean?",
       "It's the DOL's PERM case identifier: G marks the PERM program, and the digits encode the fiscal-year filing sequence. You'll find it on the ETA-9089 filing confirmation."),
      ("Does the DOL publish case statuses publicly?",
       "Not as an individual lookup. The DOL releases aggregate performance data and periodic disclosure files; ImmiLane combines these public trails into a live picture of the queue."),
      ("How current is ImmiLane's DOL data?",
       f'The scanner runs multiple times daily; figures on this page were last refreshed <span data-live="updated">today</span>. The <a href="./">dashboard</a> always shows the newest scan.'),
  ])}
  <div class="cta-box"><p><strong>See the whole queue:</strong> the <a href="./">PERM dashboard</a> shows every filing month&rsquo;s status mix, daily decision counts, and the processing frontier — or check <a href="perm-processing-time">current processing times</a>.</p></div>
""",
    ld=faq_ld([
        ("Can I log into FLAG to check my PERM case?",
         "Only the filing employer or their attorney has FLAG access for a PERM case. Applicants track progress through their employer, their attorney, or a case-monitoring service."),
        ("What does a G-100 case number mean?",
         "It is the DOL's PERM case identifier: G marks the PERM program and the digits encode the fiscal-year filing sequence. It appears on the ETA-9089 filing confirmation."),
        ("Does the DOL publish case statuses publicly?",
         "Not as an individual lookup. The DOL releases aggregate performance data and periodic disclosure files, which ImmiLane combines into a live view of the PERM queue."),
        ("How current is ImmiLane's DOL data?",
         "ImmiLane's scanner follows DOL PERM data multiple times daily, so the dashboard and alerts reflect near real-time queue movement."),
    ]),
)

# ────────────────────────── /perm-processing-time ─────────────────────────
PAGES["perm-processing-time"] = dict(
    title="PERM Processing Time 2026 — Live DOL Data | ImmiLane",
    desc="Current PERM processing time: which filing month the DOL is working on now, average days to a decision, and how the pace is trending.",
    eyebrow="Live DOL Data", h1="PERM Processing Time: Where the DOL Is Right Now",
    lede=(f'PERM processing time is best read from the DOL&rsquo;s own queue, not from anecdotes. '
          f'ImmiLane measures it directly from live DOL data across 207,000+ cases: the month being '
          f'adjudicated, the pace of movement, and the average days from filing to decision — updated '
          f'<span data-live="updated">multiple times daily</span>.'),
    strip=[("frontier", FRONTIER, "Filing month in process"), ("pct", PCT, "Through that month"),
           ("avg", AVG, "Avg days, all decisions"), ("avgCert", AVG_CERT, "Avg days, certified"),
           ("move", MOVE, "% of month cleared/week")],
    body=f"""
  <div class="content">
    <h3>Current PERM processing time</h3>
    <p>The DOL is adjudicating <strong data-live="frontier">{FRONTIER}</strong> filings — about <strong data-live="pct">{PCT}</strong> of the way through that month, clearing roughly <strong data-live="move">{MOVE}</strong>% of a filing month per week. Decisions are averaging <strong data-live="avg">{AVG}</strong> days from filing (<strong data-live="avgCert">{AVG_CERT}</strong> days for certified cases). In practical terms: a non-audited case filed today should expect a decision in roughly 13&ndash;14 months at the current pace.</p>
    <h3>Why your case may take more or less time</h3>
    <ul>
      <li><strong>Filing-month order.</strong> The DOL processes PERM in rough filing-month order, so your wait is mostly the distance between your month and the frontier — details in <a href="guide-how-dol-processes-perm">how the DOL processes PERM</a>.</li>
      <li><strong>Audits.</strong> Audited cases leave the main queue and typically add many months — see <a href="guide-perm-audits-rfis">audits and RFIs</a>.</li>
      <li><strong>Volume surges.</strong> Heavy filing months (often Q4) take longer to clear than light ones.</li>
      <li><strong>DOL throughput.</strong> Staffing and budget changes move the weekly pace; the dashboard&rsquo;s trend shows whether the pace is accelerating or slowing.</li>
    </ul>
    <h3>Reading it for your own case</h3>
    <p>Find your filing month, compare it to the frontier above, and divide the gap by the weekly pace — or let the <a href="estimate">estimate tool</a> do exactly that from your filing date or case number. To see where the queue stands the day anything changes, <a href="subscribe">Case Watch</a> emails you on status movement. Understanding your current label? See <a href="perm-case-status">what each case status means</a>.</p>
  </div>
  {faq_html([
      ("How long does PERM take in 2026?",
       f'Measured from live DOL data, decisions are averaging about <span data-live="avg">{AVG}</span> days (roughly 13 months) from filing for non-audited cases. Audited cases take substantially longer.'),
      ("Which PERM filing month is the DOL processing now?",
       f'Right now the DOL is working through <span data-live="frontier">{FRONTIER}</span> filings, about <span data-live="pct">{PCT}</span> complete, with <span data-live="remain">{REMAIN}</span> cases remaining in that month.'),
      ("Is PERM processing getting faster or slower?",
       f'The queue is currently moving at about <span data-live="move">{MOVE}</span>% of a filing month per week. The <a href="./">dashboard</a> charts the pace over time so you can see the trend rather than a single snapshot.'),
      ("Does premium processing exist for PERM?",
       "No. Unlike some USCIS petitions, PERM has no premium processing — every case waits in the DOL queue, which is why tracking the frontier is the only reliable timeline signal."),
  ])}
  <div class="cta-box"><p><strong>Get your date:</strong> the <a href="estimate">estimate tool</a> converts today&rsquo;s pace into a projected decision window for your filing date — and <a href="perm-status-check">here&rsquo;s how to check your status</a> along the way.</p></div>
""",
    ld=faq_ld([
        ("How long does PERM take in 2026?",
         "Measured from live DOL data, PERM decisions are averaging roughly 396 days (about 13 months) from filing for non-audited cases. Audited cases take substantially longer."),
        ("Which PERM filing month is the DOL processing now?",
         "ImmiLane's live tracker shows the DOL's current processing frontier — the filing month being adjudicated, percent complete, and cases remaining — updated multiple times daily."),
        ("Is PERM processing getting faster or slower?",
         "ImmiLane measures the DOL's weekly pace through each filing month and charts it over time, showing whether processing is accelerating or slowing."),
        ("Does premium processing exist for PERM?",
         "No. PERM has no premium processing option — every case waits in the DOL queue, so the processing frontier is the only reliable timeline signal."),
    ]),
)

# ───────────────────────────── assembly ───────────────────────────────────
m_title = re.search(r"<title>.*?</title>", chrome, re.S)
m_ga = re.search(r'<script async src="https://www\.googletagmanager\.com', chrome)
head_top = chrome[:m_title.start()]
head_rest = chrome[m_ga.start():]              # GA .. </head> .. body .. </html>

m_style_end = re.search(r"</style>\s*</head>", head_rest)
head_rest_a = head_rest[:m_style_end.start()]  # GA + fonts + <style> content
head_rest_b = head_rest[m_style_end.start():]  # </style></head><body>...

m_container = re.search(r'<div class="container">.*?</div>\s*\n\s*<footer>', head_rest_b, re.S)
body_pre = head_rest_b[:m_container.start()]   # </style></head><body> ads + nav
tail = head_rest_b[m_container.end() - len("<footer>"):]  # <footer>...</html>

body_pre = body_pre.replace(' class="active"', "")  # no nav item active

for slug, P in PAGES.items():
    assert len(P["title"]) <= 60, (slug, len(P["title"]))
    assert len(P["desc"]) <= 155, (slug, len(P["desc"]))
    strip_html = "\n    ".join(
        f'<div class="live-stat"><div class="v" data-live="{k}">{v}</div><div class="l">{l}</div></div>'
        for k, v, l in P["strip"])
    meta = f"""<title>{P['title']}</title>
<meta name="description" content="{P['desc']}">
<link rel="canonical" href="{SITE}/{slug}">
<meta property="og:type" content="website">
<meta property="og:title" content="{P['title']}">
<meta property="og:description" content="{P['desc']}">
<meta property="og:url" content="{SITE}/{slug}">
<meta property="og:site_name" content="ImmiLane">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{P['title']}">
<meta name="twitter:description" content="{P['desc']}">
<script type="application/ld+json">{P['ld']}</script>
"""
    container = f"""<div class="container">
  <div class="hero">
    <div class="eyebrow">{P['eyebrow']}</div>
    <h1>{P['h1']}</h1>
  </div>
  <p class="lede">{P['lede']}</p>
  <div class="live-strip">
    {strip_html}
  </div>
  <p class="live-note">Live from DOL FLAG data tracked by ImmiLane &middot; last updated <span data-live="updated">Sep 15, 2026</span> &middot; <a href="./">open the full dashboard</a></p>
{P['body']}
{LIVE_JS.strip()}
</div>

"""
    page = head_top + meta + head_rest_a + EXTRA_CSS + body_pre + container + tail
    (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
    print(f"wrote {slug}.html ({len(page.splitlines())} lines)")

print("OK")
