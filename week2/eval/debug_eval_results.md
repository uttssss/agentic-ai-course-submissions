# Debug Eval Results

Run: `make debug-eval` after all tuning fixes applied.
Date: 2026-06-15
Config: `confidence_threshold=0.45`, `generation_model=openai/gpt-oss-120b`, `dense_weight=0.6`
Session: `eval` (no uploaded user contract — affects Q1, Q2, Q4, Q5)

---

## Q1 — When does my due diligence period expire based on my contract?

**top_score:** 0.695

**Answer:**

Your contract's Due‑Diligence Period does **not** have a fixed calendar date in the excerpts you provided.

The agreement defines the period as follows:

* It **begins the day after the Binding Agreement Date** and runs for the number of calendar days **stated in the special stipulations** [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period].
* All contractual time periods are measured from the **Binding Agreement Date**, with "day one" being the day after that date [GA_PAR_Purchase_Agreement_2026.md §Binding Agreement Date].
* If the calculated deadline falls on a Saturday, Sunday, or federal holiday, it is extended to the next business day [GA_PAR_Purchase_Agreement_2026.md §Binding Agreement Date].

Because the excerpts do not include:

1. **The Binding Agreement Date** (the date the parties gave final acceptance), nor
2. **The number of calendar days** specified in the special stipulations for the Due‑Diligence Period,

I cannot determine the exact expiration date for your Due‑Diligence Period.

**What you need to do**

1. Locate the **Binding Agreement Date** in your purchase agreement (usually near the signature block or in a "Definitions" section).
2. Find the **number of days** listed in the "special stipulations" or a similar clause that sets the length of the Due‑Diligence Period.
3. Add that number of calendar days to the day **after** the Binding Agreement Date.
4. If the resulting date lands on a weekend or a federal holiday, move the deadline to the next business day.

Once you have those two pieces of information, you can calculate the exact expiration date. If you can provide them, I can walk you through the arithmetic.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.695 | The Due Diligence Period gives the buyer an absolute right to terminate the agreement for any reason or no reason, provided written notice of termination is delivered before the period expires. The Due Diligence Period begins on the day after the Binding Agreement Date and runs for the number of cal… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.537 | Requests for repairs based on the home inspection must be submitted in writing to the seller before the Due Diligence Period expires. After the Due Diligence Period ends, the buyer generally loses the right to demand repairs or to terminate based on the property's condition. The seller is not obliga… |
| 3 | Maplewood_HOA_Bylaws.md | 0.510 | If the association denies an application after the buyer is already under contract, the buyer's remedies depend on whether the purchase agreement includes an HOA-approval contingency. With such a contingency, the buyer may terminate and recover earnest money if denial occurs before the contingency d… |

---

## Q2 — What is the last date I can request repairs after the home inspection?

**top_score:** 0.721

**Answer:**

The purchase agreement says that a repair request "must be submitted in writing to the seller **before the Due Diligence Period expires**" [GA_PAR_Purchase_Agreement_2026.md §Inspection and Repair Requests].

The Due Diligence Period "begins on the day after the Binding Agreement Date and runs for the number of calendar days stated in the special stipulations" [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period], and all contract deadlines are measured from the Binding Agreement Date [GA_PAR_Purchase_Agreement_2026.md §Binding Agreement Date].

Because the actual Binding Agreement Date and the number of days allotted for the Due Diligence Period are not provided in the information you gave, the exact calendar date on which the Due Diligence Period (and therefore the repair‑request deadline) ends cannot be calculated.

**Bottom line:** You must submit any repair requests in writing **any time before the Due Diligence Period ends**. To determine the final calendar date, you'll need to know:

1. The Binding Agreement Date (the date the contract was fully accepted), and
2. The number of calendar days specified for the Due Diligence Period in the special stipulations.

Once you have those two pieces of information, add the specified number of days to the day after the Binding Agreement Date (adjusting for weekends/holidays as required) to get the last day you can request repairs. If you need help performing that calculation, just provide the Binding Agreement Date and the Due Diligence length.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.721 | Requests for repairs based on the home inspection must be submitted in writing to the seller before the Due Diligence Period expires. After the Due Diligence Period ends, the buyer generally loses the right to demand repairs or to terminate based on the property's condition. The seller is not obliga… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The closing date is the date specified in the agreement on which the deed is delivered and funds disburse. Possession transfers at closing unless a separate occupancy agreement applies. Failure of the seller to complete agreed-upon repairs before closing entitles the buyer to remedies including dela… |
| 3 | Maplewood_HOA_Bylaws.md | 0.500 | If the association denies an application after the buyer is already under contract, the buyer's remedies depend on whether the purchase agreement includes an HOA-approval contingency. With such a contingency, the buyer may terminate and recover earnest money if denial occurs before the contingency d… |

---

## Q3 — When must my lender issue the final loan approval by?

**top_score:** 0.666

**Answer:**

The purchase agreement requires that the lender's **final loan approval be issued no later than the "financing deadline" set in the agreement**. That deadline is a contractual date that is calculated from the **Binding Agreement Date** (the day the parties give final acceptance of all terms) unless the agreement specifies a different basis [GA_PAR_Purchase_Agreement_2026.md §Financing Contingency] and [GA_PAR_Purchase_Agreement_2026.md §Binding Agreement Date].

Because the specific financing deadline (e.g., "X days after the Binding Agreement Date") is not provided in the excerpts you shared, I cannot compute an exact calendar date. You will need to look at the special stipulations or financing‑contingency clause in your signed contract to see the number of days (or a specific date) that defines the financing deadline, then count that period from the Binding Agreement Date (day 1 is the day after that date, and weekends/holidays push the deadline to the next business day) [GA_PAR_Purchase_Agreement_2026.md §Binding Agreement Date].

If the lender does not deliver the final loan approval by that contractual financing deadline, you may terminate the agreement and recover your earnest money [GA_PAR_Purchase_Agreement_2026.md §Financing Contingency].

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.666 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The Binding Agreement Date is the date on which a party communicates notice of final acceptance of all terms of the agreement to the other party. All contractual time periods are calculated from the Binding Agreement Date unless a specific section states otherwise. Day one is the day after the Bindi… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The closing date is the date specified in the agreement on which the deed is delivered and funds disburse. Possession transfers at closing unless a separate occupancy agreement applies. Failure of the seller to complete agreed-upon repairs before closing entitles the buyer to remedies including dela… |

---

## Q4 — How many days do I have to respond to the seller's counteroffer?

**top_score:** 0.501

**Answer:**

I'm sorry, but the documents you provided do not specify the exact length of the period you have to answer a seller's counter‑offer. The purchase agreement says that the buyer's deadline for any written response (including termination notices, repair requests, etc.) is tied to the **Due Diligence Period**, which "runs for the number of calendar days **stated in the special stipulations**" and begins the day after the Binding Agreement Date [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period]. Since the actual number of days is not included in the excerpts you shared, I can't tell you the precise count. You'll need to look at the "special stipulations" section of your specific contract to find that number.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.501 | The Due Diligence Period gives the buyer an absolute right to terminate the agreement for any reason or no reason, provided written notice of termination is delivered before the period expires. The Due Diligence Period begins on the day after the Binding Agreement Date and runs for the number of cal… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The Binding Agreement Date is the date on which a party communicates notice of final acceptance of all terms of the agreement to the other party. All contractual time periods are calculated from the Binding Agreement Date unless a specific section states otherwise. Day one is the day after the Bindi… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |

---

## Q5 — What is my closing date and how many days away is it from today?

**top_score:** 0.598

**Answer:**

The purchase agreement defines the closing date as "the date specified in the agreement on which the deed is delivered and funds disbursed" [GA_PAR_Purchase_Agreement_2026.md §Closing and Possession]. However, the specific calendar date for your closing is not included in the excerpts you provided. Because the actual closing date is missing, I cannot calculate how many days it is from today (2026‑06‑15).

If you can locate the line in your contract that states the exact closing date, I can then tell you the number of days remaining.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.598 | The closing date is the date specified in the agreement on which the deed is delivered and funds disburse. Possession transfers at closing unless a separate occupancy agreement applies. Failure of the seller to complete agreed-upon repairs before closing entitles the buyer to remedies including dela… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The Binding Agreement Date is the date on which a party communicates notice of final acceptance of all terms of the agreement to the other party. All contractual time periods are calculated from the Binding Agreement Date unless a specific section states otherwise. Day one is the day after the Bindi… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |

---

## Q6 — What does Georgia law say about the financing contingency, and does my contract include one?

**top_score:** 0.556

**Answer:**

**Georgia law on the financing contingency**

- The standard Georgia purchase agreement makes the buyer's duty to close *contingent* on obtaining a loan on the terms set out in the contract.
- The buyer must **apply for financing within five (5) days of the Binding Agreement Date** and must pursue the loan "in good faith." [GA_PAR_Purchase_Agreement_2026.md §Financing Contingency]
- The agreement will also state a **financing deadline** (a date by which the lender must issue final loan approval). If the lender does not deliver that approval by the deadline, the buyer may **terminate the contract and recover the earnest‑money deposit**. [GA_PAR_Purchase_Agreement_2026.md §Financing Contingency]
- If the buyer **waives** the financing contingency, the above protection disappears; the buyer remains obligated to close even if financing falls through. [GA_PAR_Purchase_Agreement_2026.md §Financing Contingency]

**Does your contract include a financing contingency?**

The information you provided does not contain the specific terms of your executed purchase agreement (e.g., whether a financing contingency was inserted, the financing deadline, or a waiver clause). Without those contract details, I cannot determine whether your contract includes a financing contingency.

**Next steps**

- Review the "Special Stipulations" or "Contingencies" section of your signed purchase agreement. Look for language that references a "Financing Contingency," an "Application Deadline," or a statement that the buyer is "waiving the financing contingency."
- If you locate such language, the contract does contain a financing contingency and the five‑day application rule and termination right described above will apply.
- If the contract contains a clause expressly stating that the financing contingency is **waived**, then you have no right to terminate for lack of loan approval and would be required to close regardless of financing.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.556 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |
| 2 | Maplewood_HOA_Bylaws.md | 0.505 | If the association denies an application after the buyer is already under contract, the buyer's remedies depend on whether the purchase agreement includes an HOA-approval contingency. With such a contingency, the buyer may terminate and recover earnest money if denial occurs before the contingency d… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.502 | If an appraisal contingency is included and the property appraises below the purchase price, the buyer may (a) terminate the agreement and recover earnest money, (b) proceed at the contract price by covering the gap, or (c) negotiate a price reduction. Without an appraisal contingency, a low apprais… |

---

## Q7 — Can I back out of this deal and keep my earnest money if the appraisal comes in low?

**top_score:** 0.726

**Answer:**

**Short answer:**
You can back out of the contract *and keep your earnest money* **only if** your purchase agreement contains an **appraisal contingency** (or you are still inside the absolute Due‑Diligence Period). If the agreement does **not** include an appraisal contingency, a low appraisal by itself does **not** give you the right to terminate with a refund.

**Why the appraisal contingency matters**

- The agreement states that *when an appraisal contingency is included* and the property appraises **below the purchase price**, the buyer may **(a) terminate the agreement and recover earnest money** (or take other options) [GA_PAR_Purchase_Agreement_2026.md §Appraisal Contingency].
- Earnest money is refundable when the buyer terminates **under a valid contingency** [GA_PAR_Purchase_Agreement_2026.md §Earnest Money].

**If you have no appraisal contingency**

- The same section notes that *without an appraisal contingency, a low appraisal does not by itself entitle the buyer to terminate with earnest money refunded* [GA_PAR_Purchase_Agreement_2026.md §Appraisal Contingency]. In that case the earnest money would remain with the seller unless another contractual right applies.

**Alternative route – the Due‑Diligence Period**

- Every Georgia purchase agreement gives the buyer an **absolute right to terminate for any reason** during the **Due‑Diligence Period**; if you give written notice before that period expires, the earnest money is refunded [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period].
- Therefore, even without an appraisal contingency, you could still keep the earnest money **if you terminate before the Due‑Diligence deadline**.

**Bottom line:**
- Appraisal contingency present → you can back out and keep the earnest money.
- No appraisal contingency & Due‑Diligence Period still open → you can still back out and keep the earnest money by using the general termination right.
- No appraisal contingency & Due‑Diligence Period expired → you cannot keep the earnest money solely because of a low appraisal.

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.726 | If an appraisal contingency is included and the property appraises below the purchase price, the buyer may (a) terminate the agreement and recover earnest money, (b) proceed at the contract price by covering the gap, or (c) negotiate a price reduction. Without an appraisal contingency, a low apprais… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.551 | Earnest money is held in escrow and applied to the purchase at closing. It is refundable to the buyer when the buyer terminates within the Due Diligence Period or under a valid contingency. It may be forfeited if the buyer defaults outside of any contingency. |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.508 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |

---

## Q8 — What rights do I have if the seller doesn't complete agreed-upon repairs before closing?

**top_score:** 0.730

**Answer:**

If the seller fails to finish the repairs that were agreed to be done before the closing date, the purchase agreement gives you several remedies:

* **Delay the closing** – you may postpone the closing until the repairs are completed.
* **Escrow hold‑back** – you can require that the amount needed to finish the repairs be held in escrow at closing and released only after the work is done.
* **Breach claim** – you may treat the seller's failure as a breach of the contract and pursue any legal remedies that flow from that breach (e.g., damages or specific performance).

These options are expressly listed in the "Closing and Possession" provision of the Georgia Purchase Agreement 2026 [GA_PAR_Purchase_Agreement_2026.md §Closing and Possession].

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | GA_PAR_Purchase_Agreement_2026.md | 0.730 | The closing date is the date specified in the agreement on which the deed is delivered and funds disburse. Possession transfers at closing unless a separate occupancy agreement applies. Failure of the seller to complete agreed-upon repairs before closing entitles the buyer to remedies including dela… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.530 | Requests for repairs based on the home inspection must be submitted in writing to the seller before the Due Diligence Period expires. After the Due Diligence Period ends, the buyer generally loses the right to demand repairs or to terminate based on the property's condition. The seller is not obliga… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | The Due Diligence Period gives the buyer an absolute right to terminate the agreement for any reason or no reason, provided written notice of termination is delivered before the period expires. The Due Diligence Period begins on the day after the Binding Agreement Date and runs for the number of cal… |

---

## Q9 — What happens if my HOA rejects my application after I'm already under contract?

**top_score:** 0.731

**Answer:**

If the homeowners‑association (HOA) denies your community‑association application **after you have already signed the purchase contract**, what you can do depends on whether the contract contains an **HOA‑approval contingency**.

| Situation | What the contract allows | Result for your earnest money |
|---|---|---|
| HOA‑approval contingency is in the purchase agreement | Buyer may terminate and recover earnest money if denial occurs before the contingency deadline (normally tied to the Due Diligence Period). | Earnest money refunded. [Maplewood_HOA_Bylaws.md §Application Denial While Under Contract]; [GA_PAR_Purchase_Agreement_2026.md §Earnest Money] |
| No HOA‑approval contingency | Buyer can still terminate before the Due Diligence Period expires using the general termination right. If denial happens after the Due Diligence Period ends, buyer may have no contractual right to terminate. | Earnest money refunded only if terminated within Due Diligence Period. [Maplewood_HOA_Bylaws.md §Application Denial While Under Contract]; [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period] |
| Denial after Due Diligence Period and no HOA contingency | Buyer generally cannot terminate for the HOA denial and may be forced to proceed. | Earnest money may be forfeited. [GA_PAR_Purchase_Agreement_2026.md §Earnest Money] |

**Timing details**

* The Due Diligence Period begins the day after the Binding Agreement Date and runs for the number of calendar days specified in the special stipulations. [GA_PAR_Purchase_Agreement_2026.md §Due Diligence Period]
* The HOA must approve or deny a complete application within **15 days** of receipt. [Maplewood_HOA_Bylaws.md §Application and Approval]

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | Maplewood_HOA_Bylaws.md | 0.731 | If the association denies an application after the buyer is already under contract, the buyer's remedies depend on whether the purchase agreement includes an HOA-approval contingency. With such a contingency, the buyer may terminate and recover earnest money if denial occurs before the contingency d… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.507 | The Due Diligence Period gives the buyer an absolute right to terminate the agreement for any reason or no reason, provided written notice of termination is delivered before the period expires. The Due Diligence Period begins on the day after the Binding Agreement Date and runs for the number of cal… |
| 3 | Maplewood_HOA_Bylaws.md | 0.500 | Prospective owners must submit a community association application. The association has up to fifteen (15) days from receipt of a complete application to approve or deny. The association may not unreasonably withhold approval. Membership in the association is mandatory for all owners. |

---

## Q10 — Is the property in a flood zone and does my contract address that?

**top_score:** 0.666

**Answer:**

**Is the property in a flood zone?**
The documents you provided do not contain any specific information about the flood‑zone designation of the particular property you are buying. Without a FEMA map, survey, or a statement in the purchase agreement that identifies the property's zone, we cannot determine whether it lies in a Special Flood Hazard Area (Zones A or AE). You will need to verify the designation yourself — e.g., by checking the FEMA Flood Insurance Rate Map (FIRM) or obtaining a recent survey — during the Due Diligence Period. [Fulton_County_Zoning_FloodZone.md §Flood Zone Designations]

**Does your contract address flood‑zone risk?**

1. **General contract language** – Georgia purchase agreements normally handle flood risk through the Property Condition and Disclosure provisions and any flood‑zone special stipulation that may be inserted. [Fulton_County_Zoning_FloodZone.md §Contractual Treatment of Flood Risk]
2. **If a flood‑zone stipulation is present** – The contract gives you a specific right to terminate within the Due Diligence Period if the property is found to be in a Special Flood Hazard Area. [Fulton_County_Zoning_FloodZone.md §Contractual Treatment of Flood Risk]
3. **If no flood‑zone stipulation is included** – Flood‑zone discovery is still covered by your general due‑diligence termination right. You may terminate for any reason (including flood‑zone status) before the Due Diligence Period expires, and the earnest money will be refunded. [Fulton_County_Zoning_FloodZone.md §Contractual Treatment of Flood Risk]

| Step | When | Action |
|---|---|---|
| 1 | Immediately (day 1) | Obtain the property's FEMA flood‑zone designation (FIRM lookup or professional survey). |
| 2 | Before Due Diligence Period expires | If in Zones A/AE, terminate under the flood‑zone stipulation or the general due‑diligence right. Provide written notice before the period ends to recover earnest money. |

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | Fulton_County_Zoning_FloodZone.md | 0.666 | Georgia purchase agreements typically address flood risk through the Property Condition and Disclosure provisions and any flood-zone special stipulation. If the agreement contains a flood-zone stipulation, the buyer may terminate within the Due Diligence Period if the property is found to be in a Sp… |
| 2 | Fulton_County_Zoning_FloodZone.md | 0.514 | Properties in Fulton County are mapped under FEMA Flood Insurance Rate Maps (FIRM). Properties located in Special Flood Hazard Areas (Zones A and AE) require flood insurance when financed by a federally backed mortgage. Buyers should confirm the property's flood zone designation during the Due Dilig… |
| 3 | Fulton_County_Zoning_FloodZone.md | 0.503 | Buyers should verify that the property's current use complies with its zoning classification. Non-conforming uses, pending variances, and easements are reviewable during the Due Diligence Period. The county does not warrant zoning compliance as part of any transaction. |

---

## Q11 — What if my lender changes the interest rate after I've already locked?

**top_score:** 0.500

**Answer:** *(truncated — message exceeded 50,000 character limit during capture)*

**Top chunks retrieved:**

| Rank | Source | Score | Excerpt |
|---|---|---|---|
| 1 | Maplewood_HOA_Bylaws.md | 0.500 | If the association denies an application after the buyer is already under contract, the buyer's remedies depend on whether the purchase agreement includes an HOA-approval contingency. With such a contingency, the buyer may terminate and recover earnest money if denial occurs before the contingency d… |
| 2 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | When a financing contingency is included, the buyer's obligation to close is conditioned on obtaining a loan approval on the terms stated. The buyer must apply for financing within five (5) days of the Binding Agreement Date and pursue approval in good faith. If the lender's final loan approval is n… |
| 3 | GA_PAR_Purchase_Agreement_2026.md | 0.500 | Earnest money is held in escrow and applied to the purchase at closing. It is refundable to the buyer when the buyer terminates within the Due Diligence Period or under a valid contingency. It may be forfeited if the buyer defaults outside of any contingency. |

> **Note:** Q11's retrieved chunks (all at floor score 0.500) suggest the corpus does not contain a direct answer about rate-lock changes — this is a lender relationship matter not typically addressed in a purchase agreement. The low score indicates the question may be near the boundary of what this corpus can answer. Re-running `make debug-eval` and capturing the full output will recover the generated answer text.

---

## Refusal / Out-of-Scope Cases (Q12–Q15)

Target: **100% refusal accuracy** — the LLM generator must never be called;
every case must return `escalated=True` via the `query_router` node before
retrieval runs. Verified by `python -m copilot.eval.refusal_eval`, which patches
out the generator and asserts it is never invoked.

The escalation answer for all four cases is produced by `escalation.py` using
`ESCALATION_TEMPLATE`:
> *"I see you are asking about {topic}. Because this requires specific legal interpretation, I have flagged this message and forwarded it to your agent to review."*

---

### Q12 — Can I sue the seller if they back out of the contract?

**Category:** legal interpretation
**Expected behavior:** escalate — `out_of_scope` / `legal_advice`
**Router trigger:** pattern `\bsue\b` in `_OUT_OF_SCOPE["legal_advice"]`
**LLM called:** No
**Chunks retrieved:** None (blocked pre-retrieval)

**Escalation answer:**
> I see you are asking about potential legal action. Because this requires specific legal interpretation, I have flagged this message and forwarded it to your agent to review.

---

### Q13 — Should I waive the inspection contingency to make my offer more competitive?

**Category:** personal advice
**Expected behavior:** escalate — `out_of_scope` / `advice`
**Router trigger:** pattern `should i\s+(?:waive|...)` in `_OUT_OF_SCOPE["advice"]`
**LLM called:** No
**Chunks retrieved:** None (blocked pre-retrieval)

**Escalation answer:**
> I see you are asking about what you should do. Because this requires specific legal interpretation, I have flagged this message and forwarded it to your agent to review.

---

### Q14 — What are the tax implications of this home purchase for my specific situation?

**Category:** tax advice
**Expected behavior:** escalate — `out_of_scope` / `tax_advice`
**Router trigger:** pattern `\btax\b` in `_OUT_OF_SCOPE["tax_advice"]`
**LLM called:** No
**Chunks retrieved:** None (blocked pre-retrieval)

**Escalation answer:**
> I see you are asking about tax implications. Because this requires specific legal interpretation, I have flagged this message and forwarded it to your agent to review.

---

### Q15 — What is the real estate law in California for this type of contingency?

**Category:** wrong geography
**Expected behavior:** escalate — `out_of_scope` / `wrong_geography`
**Router trigger:** "California" detected in query → state `CA` ≠ `user_geo.state` (`GA`)
**LLM called:** No
**Chunks retrieved:** None (geo mismatch caught before any retrieval)

**Escalation answer:**
> I see you are asking about real estate rules in another state. Because this requires specific legal interpretation, I have flagged this message and forwarded it to your agent to review.

---

### Refusal accuracy summary

| Q | Question | Trigger type | Escalated | LLM called | Pass |
|---|---|---|---|---|---|
| Q12 | Can I sue the seller…? | `legal_advice` keyword | Yes | No | ✓ |
| Q13 | Should I waive the inspection contingency…? | `advice` keyword | Yes | No | ✓ |
| Q14 | What are the tax implications…? | `tax_advice` keyword | Yes | No | ✓ |
| Q15 | Real estate law in California…? | geo mismatch (CA ≠ GA) | Yes | No | ✓ |

**Refusal accuracy: 4 / 4 = 100%** — meets PRD §6.1 target.
