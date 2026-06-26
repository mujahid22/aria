"""Golden dataset for ARIA's orchestrator (extraction + splitting) evaluation.

Each example is raw input text plus reference labels used by the evaluators in
evaluators.py - not a fixed "correct answer" to match verbatim (phrasing
legitimately varies), but enough ground truth to grade split count, entity
correctness, and fidelity against the source.

Categories, deliberately weighted toward what's actually broken before:
- single: one clear, unambiguous requirement
- multi: bundled requirements (meeting-notes style), varying separator style
- vague: underspecified asks where a good extraction has to make reasonable
  judgment calls without inventing unstated scope
- entity_confusion: two distinct subjects mentioned close together - this
  project's own history includes a real case (Net Sales formatting vs GMROI
  removal, two different dashboards, submitted in the same batch) where this
  class of mixup is the realistic risk, not a hypothetical one
- edge: long dumps, contradictions, non-feature asks, minimal input
"""

from __future__ import annotations

from typing import TypedDict


class GoldenRequirement(TypedDict):
    key_entity: str  # subject/feature the requirement is about - for entity-correctness checks
    title_keywords: list[str]  # at least one should appear in the extracted title (case-insensitive)


class GoldenExample(TypedDict):
    id: str
    category: str
    input: str
    expected_split_count: int
    expected_requirements: list[GoldenRequirement]
    notes: str


GOLDEN_DATASET: list[GoldenExample] = [
    # --- single: clear, unambiguous ---
    {
        "id": "single-01",
        "category": "single",
        "input": "Add a quick filter to the orders table so support reps can search by order status.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "orders table", "title_keywords": ["filter", "orders"]}
        ],
        "notes": "Baseline single-requirement case, should never fail.",
    },
    {
        "id": "single-02",
        "category": "single",
        "input": "We need CSV export on the sales report page so finance can pull numbers into Excel.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "sales report page", "title_keywords": ["csv", "export"]}
        ],
        "notes": "Baseline single-requirement case with a clear motivation clause.",
    },
    {
        "id": "single-03",
        "category": "single",
        "input": "Add a dark mode toggle to the settings page.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "settings page", "title_keywords": ["dark mode"]}
        ],
        "notes": "Minimal, very clear - tests that extraction doesn't over-elaborate.",
    },
    {
        "id": "single-04",
        "category": "single",
        "input": (
            "Customers keep asking for a way to see their past orders again with one click, "
            "so let's add a 'reorder' button on the order history page that adds those same "
            "items back to the cart."
        ),
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "order history page", "title_keywords": ["reorder"]}
        ],
        "notes": "Longer single requirement with embedded rationale - extraction must not split the rationale out as a second item.",
    },
    {
        "id": "single-05",
        "category": "single",
        "input": "This is urgent: production checkout is broken for users with saved gift cards, need a fix ASAP.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "checkout", "title_keywords": ["checkout", "gift card"]}
        ],
        "notes": "Explicit urgency language - priority should land on high/critical, not default medium.",
    },
    # --- multi: bundled, varying separator style ---
    {
        "id": "multi-01",
        "category": "multi",
        "input": (
            "1. Net sales formatting needs a change in sales dashboard\n"
            "2. GMROI needs to be removed from INV dashboard\n"
            "3. Comp Store to be added in Sales dashboard"
        ),
        "expected_split_count": 3,
        "expected_requirements": [
            {"key_entity": "sales dashboard", "title_keywords": ["net sales", "formatting"]},
            {"key_entity": "inventory dashboard", "title_keywords": ["gmroi"]},
            {"key_entity": "sales dashboard", "title_keywords": ["comp store"]},
        ],
        "notes": (
            "Real production input from this project's own history - numbered list, "
            "but two of the three items are about the SAME dashboard (Sales) and the "
            "third is about a DIFFERENT one (Inventory). Tests entity correctness, not "
            "just split count."
        ),
    },
    {
        "id": "multi-02",
        "category": "multi",
        "input": (
            "Add a wishlist heart icon to product cards for saving items. "
            "Also, implement a comment section for blog posts. "
            "And one more thing - add a loyalty points balance widget on the customer account page."
        ),
        "expected_split_count": 3,
        "expected_requirements": [
            {"key_entity": "product cards", "title_keywords": ["wishlist"]},
            {"key_entity": "blog posts", "title_keywords": ["comment"]},
            {"key_entity": "customer account page", "title_keywords": ["loyalty"]},
        ],
        "notes": "Prose-style, comma/conjunction separated rather than a list - harder split boundary detection.",
    },
    {
        "id": "multi-03",
        "category": "multi",
        "input": (
            "Bug bash notes:\n"
            "- Dealer name field missing from inventory report, add it\n"
            "- Sales report should show individual product names, not just SKUs\n"
        ),
        "expected_split_count": 2,
        "expected_requirements": [
            {"key_entity": "inventory report", "title_keywords": ["dealer name"]},
            {"key_entity": "sales report", "title_keywords": ["product name"]},
        ],
        "notes": "Bullet list framed as 'bug bash notes' - tests that framing-as-bugs doesn't confuse extraction.",
    },
    {
        "id": "multi-04",
        "category": "multi",
        "input": (
            "Three things from today's planning meeting: first, we should add SMS-based "
            "two-factor authentication for customer login since security flagged it as a risk. "
            "Second, the print-friendly view for invoices is missing - customers have been "
            "complaining they can't print a clean copy. Third, can we get a weekly digest "
            "email summarizing account activity sent out automatically?"
        ),
        "expected_split_count": 3,
        "expected_requirements": [
            {"key_entity": "customer login", "title_keywords": ["two-factor", "2fa", "sms"]},
            {"key_entity": "invoices", "title_keywords": ["print"]},
            {"key_entity": "account activity", "title_keywords": ["digest", "email"]},
        ],
        "notes": "Meeting-notes narration style with 'first/second/third' instead of a literal list - realistic transcription-style input.",
    },
    {
        "id": "multi-05",
        "category": "multi",
        "input": (
            "Add multiple shipping address storage and selection at checkout.\n"
            "Add order history filtering by date range and status."
        ),
        "expected_split_count": 2,
        "expected_requirements": [
            {"key_entity": "checkout", "title_keywords": ["shipping address"]},
            {"key_entity": "order history", "title_keywords": ["filter", "date range"]},
        ],
        "notes": "Two newline-separated, both starting with 'Add' - tests it doesn't merge them because of similar phrasing.",
    },
    {
        "id": "multi-06",
        "category": "multi",
        "input": (
            "Mobile app: let managers approve or reject expense reports from their phone. "
            "Also bulk-deactivate inactive user accounts after 90 days of no login."
        ),
        "expected_split_count": 2,
        "expected_requirements": [
            {"key_entity": "expense reports", "title_keywords": ["approve", "expense"]},
            {"key_entity": "user accounts", "title_keywords": ["deactivate", "inactive"]},
        ],
        "notes": "Two unrelated requirements from different product areas in one note.",
    },
    {
        "id": "multi-07",
        "category": "multi",
        "input": (
            "Inventory KPIs need a Power BI dashboard. Sub-category filter needed on the "
            "inventory dashboard too. And low stock alert badges should show on the product list."
        ),
        "expected_split_count": 3,
        "expected_requirements": [
            {"key_entity": "inventory KPIs", "title_keywords": ["power bi", "dashboard"]},
            {"key_entity": "inventory dashboard", "title_keywords": ["sub-category", "filter"]},
            {"key_entity": "product list", "title_keywords": ["low stock", "alert"]},
        ],
        "notes": "All three items mention 'inventory' in some form - tests it doesn't collapse them into one because of topical overlap.",
    },
    {
        "id": "multi-08",
        "category": "multi",
        "input": (
            "Add a time-series analysis view to the sales dashboard, and separately, "
            "add a time-series analysis view to the inventory dashboard."
        ),
        "expected_split_count": 2,
        "expected_requirements": [
            {"key_entity": "sales dashboard", "title_keywords": ["time-series", "sales"]},
            {"key_entity": "inventory dashboard", "title_keywords": ["time-series", "inventory"]},
        ],
        "notes": (
            "Adversarial: nearly identical wording for two requirements that differ only in "
            "the target dashboard. Tests whether extraction preserves the distinguishing "
            "entity instead of producing two near-duplicate, ambiguous titles."
        ),
    },
    # --- vague: underspecified ---
    {
        "id": "vague-01",
        "category": "vague",
        "input": "The reports page feels slow, can we look into that.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "reports page", "title_keywords": ["performance", "slow", "speed"]}
        ],
        "notes": "No concrete acceptance criteria given - tests that the model writes reasonable, testable criteria without inventing a specific unstated fix.",
    },
    {
        "id": "vague-02",
        "category": "vague",
        "input": "Make the homepage better for new users.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "homepage", "title_keywords": ["homepage", "onboarding", "new user"]}
        ],
        "notes": "Extremely vague goal - good extraction should stay generic/faithful rather than hallucinating specific features.",
    },
    {
        "id": "vague-03",
        "category": "vague",
        "input": "Search isn't great, people can't find what they want.",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "search", "title_keywords": ["search"]}
        ],
        "notes": "Vague complaint with no proposed solution - tests restraint against inventing a specific search algorithm or UI.",
    },
    {
        "id": "vague-04",
        "category": "vague",
        "input": "Can we add some kind of recently viewed products thing on the homepage carousel?",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "homepage", "title_keywords": ["recently viewed", "carousel"]}
        ],
        "notes": "Casual phrasing ('some kind of', 'thing') - tests robustness to informal language.",
    },
    # --- entity_confusion ---
    {
        "id": "entity-01",
        "category": "entity_confusion",
        "input": (
            "Remove GMROI metric and visualizations from the Inventory dashboard - "
            "it's not needed there anymore."
        ),
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "inventory dashboard", "title_keywords": ["gmroi"]}
        ],
        "notes": "Single requirement but with a metric name (GMROI) that's specifically an inventory concept - tests it isn't misfiled as a Sales dashboard change.",
    },
    {
        "id": "entity-02",
        "category": "entity_confusion",
        "input": (
            "Update net sales formatting in the sales dashboard, and also display gross "
            "margin percentage (GM%) in the same sales dashboard."
        ),
        "expected_split_count": 2,
        "expected_requirements": [
            {"key_entity": "sales dashboard", "title_keywords": ["net sales", "formatting"]},
            {"key_entity": "sales dashboard", "title_keywords": ["gross margin", "gm%"]},
        ],
        "notes": "Two distinct requirements about the SAME dashboard - tests it doesn't merge them just because the entity is identical.",
    },
    {
        "id": "entity-03",
        "category": "entity_confusion",
        "input": (
            "Add a dealer name column to the inventory report, not the sales report - "
            "we already have it on sales."
        ),
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "inventory report", "title_keywords": ["dealer name"]}
        ],
        "notes": "Explicit negative constraint naming the WRONG entity - tests it correctly picks inventory report, not sales report, despite both being mentioned.",
    },
    # --- edge cases ---
    {
        "id": "edge-01",
        "category": "edge",
        "input": (
            "Notes from Q3 planning - lots to cover. First up, customers want multiple "
            "shipping addresses saved at checkout so they don't re-enter them every time. "
            "Next, support wants order history filterable by date range and status, that's "
            "been a recurring complaint. Then there's the invoice printing issue - no clean "
            "print view exists right now. Marketing also asked for a weekly digest email of "
            "account activity. And finally, security wants SMS 2FA added to the login flow "
            "before the next compliance audit."
        ),
        "expected_split_count": 5,
        "expected_requirements": [
            {"key_entity": "checkout", "title_keywords": ["shipping address"]},
            {"key_entity": "order history", "title_keywords": ["filter", "date range"]},
            {"key_entity": "invoices", "title_keywords": ["print"]},
            {"key_entity": "account activity", "title_keywords": ["digest", "email"]},
            {"key_entity": "login", "title_keywords": ["2fa", "sms", "two-factor"]},
        ],
        "notes": "Long, narrative meeting-notes dump with 5 distinct asks woven into paragraph prose - stress test for split recall.",
    },
    {
        "id": "edge-02",
        "category": "edge",
        "input": (
            "Some people want the export button to default to CSV, others want it to "
            "default to PDF - we need to just pick one and ship it, can't support both as default."
        ),
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "export button", "title_keywords": ["export", "default"]}
        ],
        "notes": "Internally contradictory stakeholder asks within one requirement - tests that extraction captures the decision-needed nature rather than picking a side or splitting into two conflicting requirements.",
    },
    {
        "id": "edge-03",
        "category": "edge",
        "input": "checkout button doesn't work on Safari, nothing happens when you click it",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "checkout button", "title_keywords": ["checkout", "safari"]}
        ],
        "notes": "A bug report, not a feature request, framed as a requirement - tests the pipeline handles this gracefully rather than failing to extract anything.",
    },
    {
        "id": "edge-04",
        "category": "edge",
        "input": "dark mode",
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "application", "title_keywords": ["dark mode"]}
        ],
        "notes": "Minimal two-word input - tests graceful handling of underspecified input rather than a crash or empty extraction.",
    },
    {
        "id": "edge-05",
        "category": "edge",
        "input": (
            "ok so basically what happened is um, a few of us were talking after the demo "
            "yesterday and someone mentioned it would be cool if, you know, the dashboard had "
            "some kind of export thing, like maybe CSV, for the sales numbers specifically"
        ),
        "expected_split_count": 1,
        "expected_requirements": [
            {"key_entity": "sales dashboard", "title_keywords": ["csv", "export"]}
        ],
        "notes": "Heavily filled with verbal disfluency ('um', 'basically', 'you know') - tests extraction isn't thrown off by transcription-style filler.",
    },
]
