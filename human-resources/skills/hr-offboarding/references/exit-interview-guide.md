# Exit Interview Guide (Voluntary Departures)

A structured guide for the exit interview held when an employee **resigns or retires**. Its purpose is to learn — surface patterns the company can act on (management, culture, comp, growth, workload) — while treating the departing person with respect and candor. **Do not run a voluntary-style exit interview for a termination or layoff.**

Run it consistently: same core questions for every voluntary departure, ideally by someone neutral (HR, not the direct manager). Keep it a conversation, not an interrogation. Make clear how their input will be used and who will see it.

> **Confidentiality:** the raw interview and any named specifics are sensitive PII — keep them in the confidential zone (`confidentiality.records_dir`), never in shareable templates. Only **aggregated, anonymized themes** roll up into `reports/analytics/` (see the bottom of this guide). Never paste interview content into an external service, web search, or MCP call.

## Framing (say this up front)
- Thank them; the goal is to improve the workplace, not to change their decision.
- Explain confidentiality: individual responses are kept confidential; themes are reported in aggregate.
- It's optional and they can skip any question.

## Core questions

### Reasons for leaving
- What prompted you to start looking / to decide to leave?
- What was the primary factor in your decision? Were there others?
- Was there anything that, if different, might have changed your decision?
- (Retirement) What's driving the timing, and how can we make the transition smooth?

### The role & the work
- What did you enjoy most about your role? Least?
- Did the job match what you expected when you joined?
- Were your workload and expectations reasonable and sustainable?
- Did you have the tools, resources, and information to do your job well?

### Management & team
- How would you describe your relationship with your manager?
- Did you get useful feedback and recognition?
- How was collaboration and communication within the team?

### Growth, comp & culture
- Did you have opportunities to grow and develop here?
- How do you feel about your compensation and benefits relative to the market? *(record perception; do not promise or assert market figures)*
- How would you describe the company culture? Did you feel included and respected?
- Did you feel safe raising concerns? Were they addressed?

### Closing
- What are the top one or two things we should change?
- What did we do well that we should keep?
- Would you consider returning in the future, or recommending us to others? Why / why not?
- Anything else you'd like us to know?

## Logistics
- Prefer a live conversation (in person or video) over a form-only survey; a short written survey can supplement.
- Take notes on substance, not verbatim attribution of others; avoid recording third-party accusations as fact — route any allegation of misconduct/harassment to `employee-relations/` for proper handling.
- File the raw notes in the confidential zone.

## Summarizing themes into `reports/analytics/` (no individual PII)

Roll findings up so the company can act without exposing any one person:

1. **Aggregate, don't attribute.** Report patterns across multiple departures ("3 of the last 6 leavers cited limited growth paths"), not single-person quotes tied to a role/team small enough to identify them.
2. **Anonymize.** Strip names, exact titles, dates, and any detail that re-identifies someone in a small team. If a team is so small that a theme points to one person, aggregate at a higher level or omit it.
3. **Categorize.** Bucket reasons (compensation, management, growth, workload, culture, relocation, retirement, better offer) and track trends over time.
4. **Separate fact from perception.** Departure reasons are the employee's perception — label them as such; don't restate a market-pay or manager claim as company fact.
5. **Route, don't publish, allegations.** Any harassment/discrimination/safety/legal concern goes to `employee-relations/` and/or `legal-compliance/` for handling — never into the shareable analytics report.
6. **Output.** Write the anonymized theme summary to `reports/analytics/YYYY-mm-dd-exit-interview-themes.md` with counts/trends and recommended actions. Keep the raw interview in the confidential zone only.
