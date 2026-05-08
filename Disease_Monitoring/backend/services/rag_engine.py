"""
RAG Engine — Retrieval Augmented Generation
Activated ONLY when treatment verdict = FAILURE
Recommends alternative DOA-approved treatment
"""

# Simple knowledge base of DOA Sri Lanka approved medicines
# In production this would be a vector database (FAISS)
MEDICINE_KB = [
    {
        "name":          "Mancozeb 75WP",
        "chemical_class": "Dithiocarbamate",
        "type":          "Systemic",
        "diseases":      ["Early_Blight", "Late_Blight",
                          "Septoria", "Leaf_Mold"],
        "dosage":        "2g/L water, 300ml per 15 plants",
        "rain_resistant": True,
        "notes":         "Works inside leaf tissue, rain resistant"
    },
    {
        "name":          "Chlorothalonil 75WP",
        "chemical_class": "Chloronitrile",
        "type":          "Contact",
        "diseases":      ["Early_Blight", "Late_Blight",
                          "Bacterial_Spot"],
        "dosage":        "2.5g/L water",
        "rain_resistant": False,
        "notes":         "Apply in dry weather only"
    },
    {
        "name":          "Copper Oxychloride 50WP",
        "chemical_class": "Inorganic_Copper",
        "type":          "Contact",
        "diseases":      ["Bacterial_Spot", "Late_Blight"],
        "dosage":        "3g/L water",
        "rain_resistant": False,
        "notes":         "Effective against bacterial diseases"
    },
    {
        "name":          "Propiconazole 25EC",
        "chemical_class": "Triazole",
        "type":          "Systemic",
        "diseases":      ["Early_Blight", "Leaf_Mold",
                          "Target_Spot"],
        "dosage":        "1ml/L water",
        "rain_resistant": True,
        "notes":         "Systemic, absorbed quickly"
    },
    {
        "name":          "Azoxystrobin 23SC",
        "chemical_class": "Strobilurin",
        "type":          "Systemic",
        "diseases":      ["Early_Blight", "Late_Blight",
                          "Septoria", "Target_Spot"],
        "dosage":        "1ml/L water",
        "rain_resistant": True,
        "notes":         "Broad spectrum, DOA approved"
    },
    {
        "name":          "Metalaxyl + Mancozeb",
        "chemical_class": "Phenylamide_Dithiocarbamate",
        "type":          "Systemic",
        "diseases":      ["Late_Blight"],
        "dosage":        "2.5g/L water",
        "rain_resistant": True,
        "notes":         "Specifically effective for Late Blight"
    }
]


def get_alternative_treatment(
    failed_medicine:    str,
    failed_class:       str,
    disease_name:       str,
    weather:            dict
) -> dict:
    """
    Find alternative treatment when current one fails.
    
    1. Remove medicines from same chemical class (resistance risk)
    2. Filter by disease match
    3. Consider weather (rain = prefer systemic)
    4. Return best alternative
    """
    rainfall   = weather.get("details", {}).get("rainfall_1h", 0)
    high_rain  = rainfall > 5

    candidates = []

    for medicine in MEDICINE_KB:
        # Skip same chemical class (resistance prevention)
        if medicine["chemical_class"].lower() == failed_class.lower():
            continue

        # Skip if same medicine name
        if medicine["name"].lower() == failed_medicine.lower():
            continue

        # Check disease match
        disease_match = any(
            d.lower() in disease_name.lower()
            for d in medicine["diseases"]
        )
        if not disease_match:
            continue

        # Score based on conditions
        score = 1.0

        # Prefer systemic in rain (contact gets washed away)
        if high_rain and medicine["rain_resistant"]:
            score += 2.0

        if high_rain and not medicine["rain_resistant"]:
            score -= 1.0

        candidates.append({
            "medicine": medicine,
            "score":    score
        })

    if not candidates:
        # Fallback: return any suitable medicine
        return {
            "medicine_name":   "Mancozeb 75WP",
            "chemical_class":  "Dithiocarbamate",
            "dosage":          "2g/L water",
            "application":     "Spray evenly on all leaf surfaces",
            "reason":          "Broad spectrum DOA approved alternative",
            "rain_advice":     "Apply in dry weather" if high_rain
                               else "Weather suitable for application"
        }

    # Sort by score and pick best
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]["medicine"]

    rain_advice = (
        "Apply in dry period. This medicine absorbs "
        "into leaf tissue and is rain resistant."
        if best["rain_resistant"]
        else "Wait for dry weather before applying. "
             "This is a contact fungicide."
    )

    return {
        "medicine_name":   best["name"],
        "chemical_class":  best["chemical_class"],
        "type":            best["type"],
        "dosage":          best["dosage"],
        "application":     "Spray evenly covering all leaf surfaces",
        "notes":           best["notes"],
        "rain_advice":     rain_advice,
        "doa_approved":    True,
        "reason":          (
            f"Alternative to failed treatment. "
            f"Different chemical class prevents resistance. "
            f"Suitable for {disease_name}."
        )
    }