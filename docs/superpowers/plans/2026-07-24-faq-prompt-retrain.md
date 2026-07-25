# FAQ & Conversation Flow Retrain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the bot's system prompt with accurate FAQ answers and improved conversation flows extracted from the WhatsApp/Meta AI export data.

**Architecture:** Single-file change to `ai/prompts.py` (the system prompt) plus creation of a reference `data/faqs.json` from the exported `settings.txt`. No new dependencies, no new infrastructure.

**Tech Stack:** Python 3.10+, pytest

## Global Constraints

- All factual answers in the system prompt must match the corresponding entries in `settings.txt` verbatim where possible
- No new Python dependencies beyond what's in `requirements.txt`
- The `data/faqs.json` file is a reference artifact, not loaded at runtime
- All changes are to `ai/prompts.py` and `data/faqs.json` only

---

### Task 1: Create structured FAQ dataset from settings.txt

**Files:**
- Create: `data/faqs.json`
- Read: `C:\Users\PC\Downloads\file enc\settings.txt`
- Read: `ai/prompts.py` (for current pricing/packages to cross-reference)

**Interfaces:**
- Produces: `data/faqs.json` — categorized JSON with all FAQ Q&A pairs, business info, packages, policies

- [ ] **Step 1: Create `data/faqs.json`**

```json
{
  "business_info": {
    "name": "Lavish Living LTD / Lavish Apartments",
    "address": "5 M.M Alkali Street, Citec Villa, 4th Avenue, Gwarimpa",
    "hours": "Open 24 hours, 7 days a week",
    "timezone": "Africa/Lagos (West Africa Time)",
    "website": "https://lavishliving.ng",
    "google_maps": "Find us as 'Lavish Apartment' on Google Maps",
    "location_notes": "Behind Hmedix 4th avenue. ~20 minutes from the stadium, ~10-15 minutes from Efab Metropolis."
  },
  "payment_accounts": [
    { "account_number": "1219550382", "bank": "Zenith Bank", "account_name": "Lavish Living LTD" },
    { "account_number": "6397001960", "bank": "Moniepoint MFB", "account_name": "Lavish Apartments" }
  ],
  "payment_policies": {
    "cinema": "Full payment required. No deposits accepted.",
    "apartment": "50% non-refundable deposit accepted to secure. Full payment preferred.",
    "receipt_verification": "Customer must send screenshot showing both sender and receiver names.",
    "refunds": "Not offered generally. If applicable, takes 3-5 working days to process.",
    "reschedule_fee_naira": 15000,
    "reschedule_conditions": "Must reschedule within 1 week of original date. Fee must be paid ahead of time, not on visit day. Must confirm availability for new date first."
  },
  "apartment_pricing": {
    "2_bedroom_per_night": 80000,
    "3_bedroom_per_night": 90000,
    "special_event_per_night": 200000,
    "monthly_rate": 2100000,
    "discount": "For stays of 4 nights or more",
    "max_guests_standard": 10,
    "special_event_trigger": "More than 10 guests at any time, or bringing a DJ"
  },
  "apartment_policies": {
    "check_in": "2:00 PM",
    "check_out": "12:00 PM (11:59 AM)",
    "early_check_in": "Generally not possible — housekeepers need time to clean",
    "booking_lead_time": "Up to 1 month in advance",
    "payment_validates_reservation": true,
    "units": ["2-bedroom", "3-bedroom"],
    "note_no_studio": "We do not have 1-bedroom or studio apartments",
    "special_event_details": "Parties allowed when discussed in advance. For >10 guests or DJ: hosted in 3-bedroom apartments only at special event rate.",
    "caution_fee": false
  },
  "apartment_house_rules": [
    {"rule": "Check-in/out", "detail": "Check-in after 2:00 PM, check-out before 11:59 AM"},
    {"rule": "Maximum occupancy", "detail": "Maximum 10 guests. Only registered guests can stay overnight."},
    {"rule": "Visitors", "detail": "Welcome but must be accompanied by a registered guest. Must not exceed max occupancy."},
    {"rule": "Quiet hours", "detail": "11:00 PM to 8:00 AM"},
    {"rule": "Smoking", "detail": "Strictly prohibited inside. Use balcony at back of building."},
    {"rule": "Pets", "detail": "Not allowed"},
    {"rule": "Kitchen", "detail": "Fully functional kitchen available. Clean up after use or request on-site cleaner."},
    {"rule": "Parties/events", "detail": "Only if discussed in advance. Provide event details and guest count."},
    {"rule": "Damages", "detail": "Report immediately. Guest responsible for repair/replacement cost."},
    {"rule": "Waste disposal", "detail": "Dispose of trash in designated kitchen bin."},
    {"rule": "Energy", "detail": "Turn off lights, AC, and appliances when not in use."},
    {"rule": "Physical altercations", "detail": "Strictly prohibited"}
  ],
  "cinema_packages": [
    {"name": "Crunch and Drink", "price_naira": 25000, "includes": "Pet Drink + Pop Corn", "capacity": "1-6 people"},
    {"name": "Crunch and Wine", "price_naira": 30000, "includes": "Pop Corn + Wine", "capacity": "1-6 people"},
    {"name": "Slice and Drink", "price_naira": 40000, "includes": "1.5L Juice + Pizza + Pop Corn", "capacity": "1-6 people"},
    {"name": "Slice and Wine", "price_naira": 45000, "includes": "Wine + Pizza + Pop Corn + 75cl Juice", "capacity": "1-6 people"},
    {"name": "Executive", "price_naira": 55000, "includes": "Blanket + Wine + Pizza + Pop Corn + Wings + 75cl Juice. Also allows bringing own food.", "capacity": "1-6 people"},
    {"name": "BYOF (Bring Your Own Food)", "price_naira": 27000, "includes": "Bring your own food and drinks. Popcorn available for purchase separately.", "capacity": "1-6 people"}
  ],
  "cinema_sessions": [
    {"index": 0, "label": "9:30am - 11:50am"},
    {"index": 1, "label": "12:00pm - 2:20pm"},
    {"index": 2, "label": "2:30pm - 4:50pm"},
    {"index": 3, "label": "5:00pm - 7:20pm"},
    {"index": 4, "label": "7:30pm - 9:50pm"},
    {"index": 5, "label": "10:00pm - 12:00 midnight"}
  ],
  "cinema_extras": {
    "extra_time_2hrs_naira": 20000,
    "double_session_available": true,
    "special_event_upgrade": "Decorate hall, play custom movie/video, double session (5 hours)"
  },
  "cinema_rules": [
    {"rule": "Capacity", "detail": "Hall 1: max 4 people. Hall 2: max 6 people. Strictly enforced."},
    {"rule": "Outside food", "detail": "Only allowed for BYOF and Executive packages. Prohibited for all other packages."},
    {"rule": "Smoking", "detail": "Strictly prohibited inside cinema hall. Results in immediate removal and ban."},
    {"rule": "Alcohol", "detail": "Allowed to bring own alcohol only with BYOF package."},
    {"rule": "Conduct", "detail": "Sex strictly prohibited. Maintain quiet/calm atmosphere during screening."},
    {"rule": "Movie selection", "detail": "Choose from current showing list at lavishliving.ng/now-showing/. Custom movies only with Special Event upgrade."},
    {"rule": "Recording", "detail": "Video/audio recording of screening not permitted."},
    {"rule": "Age restrictions", "detail": "Must comply with movie rating age restrictions. Minors accompanied by adult."},
    {"rule": "Equipment", "detail": "Handle with care. Tampering with AV equipment prohibited."}
  ],
  "faqs": [
    {"question": "How do I confirm my private cinema booking and receive my ticket?", "answer": "Kindly make payment to confirm your reservation. A movie ticket will be issued to you afterwards."},
    {"question": "Are refunds available for bookings?", "answer": "Please note that we don't offer refunds. Kindly review our policy documents for more information."},
    {"question": "What is the process after making a payment for a booking?", "answer": "Please wait for our confirmation of payment before your booking is finalized."},
    {"question": "How do I confirm my private cinema reservation?", "answer": "Kindly choose your package and make payment to confirm your reservation. A movie ticket will be issued to you afterwards."},
    {"question": "What is the policy for extending a booking and what time does the cinema close?", "answer": "The hall closes by 12. Extra time is not available for the 10pm slot as it is the final slot of the day."},
    {"question": "What are the available timeslots for a private cinema session?", "answer": "9:30am-11:50am, 12:00pm-2:20pm, 2:30pm-4:50pm, 5:00pm-7:20pm, 7:30pm-9:50pm, 10:00pm-12:00 midnight"},
    {"question": "Can I choose the movie for my private cinema session?", "answer": "Yes, you are welcome to choose the movie for your session. Kindly follow this link to see what's currently showing: https://lavishliving.ng/now-showing/"},
    {"question": "How do I confirm my payment for a private cinema booking?", "answer": "Kindly share your transaction receipt for confirmation."},
    {"question": "What are the standard check-in and check-out times for the apartments?", "answer": "Our standard check-in time is 2pm. Check-out is by 12pm."},
    {"question": "Which cinema packages allow me to bring my own food?", "answer": "You can bring your own food only if you book the BYOF (Bring Your Own Food) or Executive package."},
    {"question": "How far is the apartment from the stadium?", "answer": "The apartment is located about 20 minutes away from the stadium."},
    {"question": "What are the guest limits and party policies for the 3-bedroom apartment?", "answer": "A maximum of 10 guests are allowed for a standard stay. Any booking with more than 10 guests is classified as a special event."},
    {"question": "What types of apartments do you offer?", "answer": "We have standard two and three bedroom apartments located at Gwarimpa. We do not have one-bedroom or studio rooms."},
    {"question": "Do you offer discounts for apartment bookings?", "answer": "We offer discounts for stays of four days/nights or more."},
    {"question": "What are the policies regarding booking times and bringing outside items to the private cinema?", "answer": "The timeslots for private cinema bookings are fixed and cannot be customized. Executive Package allows bringing own drinks and snacks."},
    {"question": "How do I receive my entry ticket for the private cinema?", "answer": "Once payment is confirmed, a movie ticket will be sent to you (to your email)."},
    {"question": "What is the maximum capacity for a private cinema session?", "answer": "The maximum number of people allowed is six. Hall 1 max 4, Hall 2 max 6."},
    {"question": "Can I reschedule my private cinema booking?", "answer": "Yes, you can reschedule your booking by paying a reschedule fee of ₦15,000."},
    {"question": "Can I play my own movie at the private cinema?", "answer": "You can play your own movie only after upgrading to the special event package."},
    {"question": "What is the refund policy for shortlet apartment bookings if the room is unavailable?", "answer": "If a shortlet apartment is unavailable due to scheduling conflicts, we will issue a full refund."},
    {"question": "What are the payment terms for a special event booking?", "answer": "For special event bookings, a deposit is required to secure the reservation, with the remaining balance to be paid before checking in on the day of the event."},
    {"question": "What is the difference between the BYOF, Executive, and Crunch and Drink packages?", "answer": "BYOF and Executive packages allow guests to bring their own snacks and food. Crunch and Drink does not permit outside food or drinks."},
    {"question": "How much is an apartment for a month?", "answer": "₦2.1m per month."}
  ]
}
```

- [ ] **Step 2: Verify the JSON is valid and complete**

```bash
python -c "import json; data = json.load(open('data/faqs.json')); print(f'FAQs: {len(data[\"faqs\"])}, Packages: {len(data[\"cinema_packages\"])}, House Rules: {len(data[\"apartment_house_rules\"])}, Cinema Rules: {len(data[\"cinema_rules\"])}')"
```

- [ ] **Step 3: Commit**

```bash
git add data/faqs.json
git commit -m "feat: add structured FAQ dataset from Meta AI export"
```

---

### Task 2: Rewrite system prompt with FAQ accuracy and flow improvements

**Files:**
- Modify: `ai/prompts.py` (full file)
- Read: `data/faqs.json` (reference)
- Read: `C:\Users\PC\Downloads\file enc\settings.txt` (source of truth)

**Interfaces:**
- Consumes: `build_full_system_prompt()` function signature (unchanged)
- Produces: Updated `SYSTEM_PROMPT` with new blocks and refined booking flows

- [ ] **Step 1: Update `ai/prompts.py` — add BUSINESS_INFO block after the PAYMENT_DETAILS block**

Current `PAYMENT_DETAILS` ends at line 12. Add the new block after it.

```python
BUSINESS_INFO = """BUSINESS INFO (for reference, answer factually):
Address: 5 M.M Alkali Street, Citec Villa, 4th Avenue, Gwarimpa (Behind Hmedix 4th avenue)
Google Maps: Search 'Lavish Apartment' on Google Maps
Hours: Open 24 hours, 7 days a week
Website: https://lavishliving.ng
Location proximity: ~20 minutes from stadium, ~10-15 minutes from Efab Metropolis
Timezone: West Africa Time (Lagos)

HOUSE RULES (apartments):
- Check-in: 2:00 PM | Check-out: 12:00 PM (11:59 AM). Early check-in generally not possible.
- Max 10 guests. Only registered guests stay overnight.
- Visitors welcome but must be accompanied, must not exceed max occupancy.
- Quiet hours: 11:00 PM - 8:00 AM.
- No smoking inside. Use balcony at back of building.
- No pets allowed.
- Fully functional kitchen available. Clean up after use.
- Report damages immediately. Guest responsible for repair/replacement.
- Dispose of trash in designated kitchen bin.
- Turn off lights, AC, and appliances when not in use.

CINEMA RULES:
- Hall 1: max 4 people | Hall 2: max 6 people. Strictly enforced.
- Outside food only allowed for BYOF and Executive packages.
- No smoking/vaping inside. Results in immediate removal and ban.
- No sex in cinema hall. Maintain quiet atmosphere during screening.
- Choose movie from current list at lavishliving.ng/now-showing/
- Custom movies only with Special Event upgrade.
- No video/audio recording of screening permitted.
- Age restrictions apply. Minors must be accompanied by adult."""
```

- [ ] **Step 2: Update existing APARTMENTS section with monthly rate and refined policies**

Find the APARTMENTS block (around line 22-23 in current SYSTEM_PROMPT) and update:

```python
APARTMENTS
2 Bedroom: 80,000 naira/night. 3 Bedroom: 90,000 naira/night.
Monthly rate (30 days): 2,100,000 naira.
Special Event/Party: 200,000 naira/night (triggered when >10 people present at any time, including visitors, or bringing a DJ).
Discounts: For stays of 4 nights or more in a single apartment.
Booking lead time: Up to 1 month in advance.
```

- [ ] **Step 3: Update CINEMA packages to match settings.txt exact wording**

Replace the existing CINEMA package list (around line 53-58):

```python
Packages (all 1-6 people, except Hall 1 max 4):
1. Crunch and Drink 25k (Pet Drink + Pop Corn)
2. Crunch and Wine 30k (Pop Corn + Wine)
3. Slice and Drink 40k (1.5L Juice + Pizza + Pop Corn)
4. Slice and Wine 45k (Wine + Pizza + Pop Corn + 75cl Juice)
5. Executive 55k (Blanket + Wine + Pizza + Pop Corn + Wings + 75cl Juice. Also allows bringing own food.)
6. BYOF 27k (Bring your own food and drinks. Popcorn available separately.)
Extras: Reschedule 15k, Extra 2hrs 20k
```

- [ ] **Step 4: Run the existing test to make sure the changes compile and the module loads**

```bash
cd C:\Users\PC\Downloads\lavish-booking-bot
python -c "from ai.prompts import build_full_system_prompt; prompt = build_full_system_prompt(); print('OK, prompt length:', len(prompt))"
```

- [ ] **Step 5: Commit**

```bash
git add ai/prompts.py
git commit -m "feat: update system prompt with FAQ accuracy and business info from Meta AI data"
```

---

### Task 3: Add tests for prompt content verification

**Files:**
- Create: `tests/test_prompts.py`
- Read: `ai/prompts.py`

**Interfaces:**
- Consumes: `build_full_system_prompt()` — returns the full system prompt string

- [ ] **Step 1: Write `tests/test_prompts.py`**

```python
from ai.prompts import build_full_system_prompt

PROMPT = build_full_system_prompt()


def test_business_info_present():
    assert "5 M.M Alkali Street" in PROMPT
    assert "Gwarimpa" in PROMPT
    assert "lavishliving.ng" in PROMPT


def test_payment_details_present():
    assert "1219550382" in PROMPT
    assert "Zenith" in PROMPT
    assert "Moniepoint" in PROMPT


def test_apartment_pricing_present():
    assert "80,000" in PROMPT
    assert "90,000" in PROMPT
    assert "200,000" in PROMPT
    assert "2,100,000" in PROMPT


def test_cinema_packages_present():
    assert "Crunch and Drink" in PROMPT
    assert "Slice and Wine" in PROMPT
    assert "Executive" in PROMPT
    assert "BYOF" in PROMPT


def test_house_rules_present():
    assert "Quiet hours" in PROMPT or "quiet hours" in PROMPT
    assert "no smoking" in PROMPT.lower() or "No smoking" in PROMPT
    assert "no pets" in PROMPT.lower() or "No pets" in PROMPT


def test_cinema_rules_present():
    assert "Hall 1" in PROMPT
    assert "Hall 2" in PROMPT
    assert "max 4" in PROMPT.lower() or "maximum of 4" in PROMPT.lower()


def test_date_context_present():
    assert "DATE CONTEXT" in PROMPT


def test_payment_flow_instructions():
    assert "receipt" in PROMPT.lower()
    assert "screenshot" in PROMPT.lower()


def test_reschedule_fee_present():
    assert "15,000" in PROMPT or "15000" in PROMPT or "15k" in PROMPT


def test_monthly_rate_present():
    assert "2,100,000" in PROMPT or "2.1m" in PROMPT.lower() or "2.1M" in PROMPT
```

- [ ] **Step 2: Run the tests to verify they pass**

```bash
cd C:\Users\PC\Downloads\lavish-booking-bot
pytest tests/test_prompts.py -v
```

Expected: All 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_prompts.py
git commit -m "test: add prompt content verification tests"
```

---

### Task 4: Conversation flow tuning — edge case handling

**Files:**
- Modify: `ai/prompts.py` — add flow rules for edge cases identified from conversation data

**Context from analysis:** The 404 conversations revealed these recurring scenarios that currently cause handoffs:
1. Monthly rate queries ("How much for a month?") — bot should answer directly
2. Walk-in queries ("I'm nearby", "Can I come now?") — bot should give address/hours instead of handing off
3. Combined apartment + cinema queries ("I want to book both") — bot should handle sequentially
4. Specific unit name references ("I want B2") — bot should redirect to availability-based assignment
5. Cinema capacity nuance — Hall 1 != Hall 2 capacity

- [ ] **Step 1: Add edge case handling rules to `ai/prompts.py`**

Add this block near the top of SYSTEM_PROMPT, after the RULES section:

```python
EDGE CASES:
- Monthly/long-stay: If customer asks about monthly or long-stay pricing, answer: "₦2.1m per month for a 2-bedroom or 3-bedroom apartment." Then ask for specific dates.
- Walk-in: If customer says "I'm nearby", "I want to come now", or similar: Provide the address (5 M.M Alkali Street, Citec Villa, Gwarimpa) and hours (24/7), and ask if they have a reservation. If yes, confirm details. If no, ask what they need.
- Combined queries: If customer asks about both apartment and cinema in the same conversation, handle apartment first, then cinema. Do NOT make them start over.
- Specific unit names: If customer mentions A1, B1, B2, C1, C2, or hall names: Respond with "An apartment/hall will be assigned based on availability. Let me check what's free for your dates."
- Cinema capacity: Hall 1 fits max 4 people. Hall 2 fits max 6. Both halls are similar in setup. If group > 6, they cannot be accommodated in a single session.
- Extra time: Only available for sessions 0-4 (not the 10pm slot). Extra 2hrs = 20k.
```

- [ ] **Step 2: Run the prompt tests to verify everything still loads correctly**

```bash
cd C:\Users\PC\Downloads\lavish-booking-bot
python -c "from ai.prompts import build_full_system_prompt; prompt = build_full_system_prompt(); print('OK, prompt length:', len(prompt))"
pytest tests/test_prompts.py -v
```

- [ ] **Step 3: Commit**

```bash
git add ai/prompts.py
git commit -m "feat: add edge case handling for monthly rates, walk-ins, combined queries, and capacity details"
```
