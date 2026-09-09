"""
Phase 14 — analytical report generation.

IMPORTANT: this is a template/rules-based generator over the structured
analysis results, NOT an LLM-authored narrative. No language-model API key
is available in this backend, and the project's own engineering rules
forbid inventing AI capabilities — so this is built, and labeled, as what
it actually is: deterministic natural-language generation (NLG) from data.

It still satisfies the spec's structural requirement (section 17): an
executive summary, key findings, significant areas, and possible
explanations that are explicitly tagged as observation / inference /
hypothesis so nothing is presented as fact beyond what the pipeline
actually measured.
"""
from __future__ import annotations

CAUSE_HYPOTHESES = {
    "Vegetation loss": [
        "land clearing or deforestation",
        "seasonal variation in crop/vegetation cycles",
        "drought or water stress",
        "fire damage",
    ],
    "Vegetation growth": [
        "seasonal regrowth or crop growth cycle",
        "reforestation or afforestation efforts",
        "increased rainfall",
    ],
    "Urban expansion": [
        "new construction or infrastructure development",
        "land-use conversion from agricultural/vegetated to built-up",
    ],
    "Water decrease": [
        "drought or reduced rainfall",
        "water extraction/diversion",
        "seasonal water body fluctuation",
    ],
    "Water increase": [
        "flooding or heavy rainfall",
        "new reservoir/water body construction",
        "seasonal water body fluctuation",
    ],
    "Other/unknown": [
        "mixed or ambiguous spectral change not matching a single category",
    ],
}


def generate_report(analysis: dict, region_name: str = "the selected region") -> dict:
    veg = analysis["vegetation"]
    water = analysis["water"]
    urban = analysis["urban"]
    regions = analysis["regions"]
    severity = analysis["overall_severity"]

    # --- Executive summary (observed facts only) ---
    n_significant = len(regions)
    summary = (
        f"Between the analyzed dates, {n_significant} significant change "
        f"region{'s were' if n_significant != 1 else ' was'} detected in {region_name}, "
        f"with an overall change severity rated {severity}. "
        f"{analysis['total_changed_fraction']*100:.1f}% of the analyzed area showed "
        f"spectral change above the detection threshold."
    )

    # --- Key findings (observed, quantified) ---
    findings = []
    if abs(veg["change_pct"]) > 1:
        direction = "decreased" if veg["change_pct"] < 0 else "increased"
        findings.append(
            f"Vegetation coverage {direction} by {abs(veg['change_pct']):.1f}% "
            f"({veg['before_pct']:.1f}% \u2192 {veg['after_pct']:.1f}%)."
        )
    if abs(water["change_pct"]) > 1:
        direction = "decreased" if water["change_pct"] < 0 else "increased"
        findings.append(
            f"Water coverage {direction} by {abs(water['change_pct']):.1f}% "
            f"({water['before_area_km2']:.2f} km\u00b2 \u2192 {water['after_area_km2']:.2f} km\u00b2)."
        )
    if abs(urban["change_pct"]) > 1:
        direction = "decreased" if urban["change_pct"] < 0 else "increased"
        findings.append(
            f"Built-up area {direction} by {abs(urban['change_pct']):.1f}% "
            f"({urban['before_area_km2']:.2f} km\u00b2 \u2192 {urban['after_area_km2']:.2f} km\u00b2)."
        )
    findings.append(f"{n_significant} discrete significant change zone{'s' if n_significant != 1 else ''} identified by the change-detection pipeline.")

    # --- Significant areas (observed, ranked) ---
    top_regions = sorted(regions, key=lambda r: r["area_km2"], reverse=True)[:5]
    significant_areas = [
        {
            "region_id": r["id"],
            "observation": (
                f"Change #{r['id']}: {r['change_type']}, {r['area_km2']:.2f} km\u00b2, "
                f"severity {r['severity']}, model confidence {r['confidence']*100:.0f}%. "
                f"Index value moved {r['before_value']:.2f} \u2192 {r['after_value']:.2f}."
            ),
        }
        for r in top_regions
    ]

    # --- Possible explanations (explicitly labeled as hypothesis, never fact) ---
    explanations = []
    for r in top_regions:
        hyps = CAUSE_HYPOTHESES.get(r["change_type"], CAUSE_HYPOTHESES["Other/unknown"])
        explanations.append(
            {
                "region_id": r["id"],
                "observed_change": f"{r['change_type']} covering {r['area_km2']:.2f} km\u00b2 (observed, measured from spectral indices).",
                "model_inference": f"Classified as '{r['change_type']}' by the change-detection pipeline with {r['confidence']*100:.0f}% heuristic confidence (model inference, not verified on the ground).",
                "hypotheses": [
                    f"Possible cause (unverified hypothesis): {h}." for h in hyps
                ],
                "caveat": "Ground-level data or higher-resolution/multi-temporal imagery would be required to confirm the actual cause.",
            }
        )

    # --- Recommendations (generic, reasonable, non-committal) ---
    recommendations = [
        "Validate high-confidence change regions against higher-resolution imagery or ground survey where feasible.",
        "Re-run analysis at additional intermediate dates to distinguish gradual trends from abrupt events (see time-series module).",
        "For CRITICAL or HIGH severity regions, prioritize field verification before any policy or resource-allocation decision.",
    ]
    if abs(veg["change_pct"]) > 20:
        recommendations.append("Large vegetation change detected — consider cross-referencing with regional rainfall/drought records.")
    if abs(urban["change_pct"]) > 20:
        recommendations.append("Large built-up area change detected — consider cross-referencing with local planning/permit records.")

    return {
        "region_name": region_name,
        "executive_summary": summary,
        "key_findings": findings,
        "significant_areas": significant_areas,
        "possible_explanations": explanations,
        "recommendations": recommendations,
        "generation_method": "rules_based_template_nlg",
        "disclaimer": (
            "This report is generated by a deterministic, template-based summarizer "
            "over structured analysis data — it is not an LLM-authored narrative. "
            "Statements under 'possible_explanations' are explicitly hypotheses, not "
            "confirmed causes."
        ),
    }
