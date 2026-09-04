# Methodology — why the roster looks like this

The bot is the easy half. The hard half is deciding *who* votes, because a crowd only outperforms its best member under conditions that have to be engineered deliberately.

---

## The theory being tested

James Surowiecki's *The Wisdom of Crowds* argues that a group produces a better estimate than its smartest member when four conditions hold:

1. **Diversity** — members hold genuinely different private information and different models of the problem.
2. **Independence** — nobody's answer is influenced by anybody else's.
3. **Decentralisation** — members draw on local, specialised knowledge.
4. **Aggregation** — some mechanism turns the individual judgements into a collective one.

The mathematical backbone is Scott Page's **Diversity Trumps Ability** theorem: under realistic conditions, a diverse group of mixed-ability problem solvers outperforms a group made up of the highest-ability solvers alone. The proof rests on **error cancellation** — independent, unbiased errors average toward zero, while correlated errors do not.

That last clause is the whole design constraint. Twenty excellent traders from the same school are not a diverse crowd; they are one opinion with twenty votes, and their shared blind spot survives averaging intact.

---

## Consequences for roster composition

- **All professionals is mathematically suboptimal.** Professionals within a school cluster around the same priors. Their disagreement is correlated noise wearing the costume of diversity.
- **All beginners is worse.** Random guesses converge on the prior — 25% per option across four choices — which is pure noise with no signal to extract.
- **A mix maximises error cancellation.** Professionals anchor the signal, intermediates supply the diversity, and a small number of newer members contribute genuinely uncorrelated reads.

The target composition is roughly **35% professional / 55% intermediate / 10% newer**, spread across eleven schools.

---

## The twenty slots

| # | School | Slots | Pro | Intermediate | Newer |
|---|---|---|---|---|---|
| 1 | ICT | 3 | 1 | 1 | 1 |
| 2 | SMC | 2 | 1 | 1 | 0 |
| 3 | Wyckoff | 2 | 1 | 1 | 0 |
| 4 | Volume Profile / Auction Market Theory | 2 | 0 | 2 | 0 |
| 5 | Order Flow / DOM / footprint | 2 | 1 | 1 | 0 |
| 6 | Classical TA (S/R, indicators) | 2 | 0 | 1 | 1 |
| 7 | Supply & Demand zones | 1 | 0 | 1 | 0 |
| 8 | Quant / mean-reversion / stat-arb | 2 | 1 | 1 | 0 |
| 9 | Macro / news / fundamental | 2 | 1 | 1 | 0 |
| 10 | Elliott Wave | 1 | 0 | 1 | 0 |
| 11 | Tape reader (experience, no formal system) | 1 | 1 | 0 | 0 |
| | **Total** | **20** | **7** | **11** | **2** |

### Why the professionals sit where they do

Schools where a bad read produces *catastrophic* noise get a professional: ICT, SMC, Wyckoff, order flow, quant, macro, tape. Schools where an intermediate read is nearly as good as an expert one do not: Volume Profile, classical TA, supply and demand, Elliott.

This is variance management rather than gatekeeping. A Wyckoff phase misread by an amateur is wrong by ninety degrees; a Volume Profile misread by an amateur is a point of control that's slightly off. The penalty for noise differs by school, so the experience budget is spent where noise is most expensive.

### Why two newer members rather than none

Both newer slots (ICT and classical TA) sit in schools with large, active communities of recent entrants who have absorbed the framework without years of confirmation bias in the same instrument. Their votes correlate *less* with their own school's consensus than the professionals' do — they are the diversity engine inside their own row. That is Page's insight applied at the row level rather than the roster level.

### Schools deliberately excluded

- **Harmonic patterns** (Gartley, Bat, Crab). A real forecasting school, but its votes correlate heavily with classical chart reading. Including it would double-count one school's opinion.
- **VWAP / algo flow as a standalone slot.** Real, but its read merges into order flow. Rather than add a correlated slot, order flow was given two slots — better signal density for the same headcount.

Order flow and macro both carry two slots because the four options being voted on encode two latent dimensions — direction *and* range-versus-expansion. Most schools speak mainly to direction. These two speak to both, so they earn extra weight.

The tape reader is the closest analogue to Galton's drunken fairgoer: no formal system, an opinion formed from experience alone, uncorrelated with everyone else's framework. That independence is the contribution.

---

## Recruiting difficulty

| Slot | Difficulty | Where these people are |
|---|---|---|
| ICT, SMC | Easy | Twitter, ICT-focused Discords |
| Classical TA | Easy | TradingView, retail forums |
| Supply & Demand | Easy | Supply-and-demand trading communities |
| Volume Profile | Medium | Volume-profile educators' audiences |
| Wyckoff | Medium-hard | Wyckoff method groups, smaller niche |
| Macro | Medium-hard | FinTwit macro circles |
| Order Flow | Hard | Order-flow forums, prop-firm circles |
| Quant | Hard | r/algotrading, QuantConnect — they don't hang out in retail spaces |
| Elliott Wave | Hard | Small but vocal community |
| Tape reader | Hardest | Long-tenure discretionary traders; word of mouth only |

Most of the recruiting effort goes to order flow, quant, macro, Elliott and tape. The easy rows fill themselves.

---

## How the software protects the conditions

Composition is only half of it. Independence has to be defended at runtime, and that is what the implementation does:

| Threat to independence | Mitigation in code |
|---|---|
| Seeing the crowd before voting | The question is a private DM. No count is exposed anywhere before 09:29. |
| Changing a vote after sensing the lean | `UNIQUE(date, member_id)` on `predictions`; the UI refuses and the database refuses. |
| Discussing it first | An eight-minute window (09:20–09:28 ET), enforced on every button callback. |
| Late voters with more information | Submissions after 09:28 are rejected outright. |
| Social pressure after the fact | Individual votes and per-member accuracy are never published. |

---

## What would falsify the premise

The accuracy ledger exists to be able to say the bot doesn't work. Recording the actual outcome each day and scoring only HIGH and MODERATE signals produces a number that can go the wrong way:

- Council accuracy at or below 25% across a few hundred signal days would say the aggregation adds nothing over a coin flip across four options.
- Accuracy on HIGH days no better than on MODERATE days would say the confidence gate isn't measuring anything.
- Accuracy tracking the single best member rather than exceeding the group would say diversity isn't paying for itself.

None of these questions can be answered on a small sample, which is precisely why the bot logs every day rather than announcing a conclusion.

---

### Reference

- James Surowiecki, *The Wisdom of Crowds* (2004) — particularly Ch. 2 on diversity and independence.
- Scott E. Page, *The Difference* (2007) — the Diversity Trumps Ability theorem.
