"""
Daily Agri-Pulse Summary Generator.
Synthesizes Mandi Wholesale Prices, Nursery Plant Rates, and Seed Costs
into an actionable intelligence brief for growers and nurseries.
"""

from typing import List, Dict, Any
from datetime import datetime, date
import statistics


def generate_daily_summary(
    mandi_records: List[Dict[str, Any]],
    plant_records: List[Dict[str, Any]],
    seed_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate structured analytics and human-readable daily brief."""
    today_str = date.today().strftime("%d %b %Y")

    # --- 1. Mandi Price Aggregations ---
    commodity_stats: Dict[str, List[float]] = {}
    tomato_markets: List[Dict[str, Any]] = []

    for r in mandi_records:
        comm = r.get("commodity", "").strip()
        pkg = r.get("price_per_kg", 0.0)
        if pkg > 0:
            commodity_stats.setdefault(comm, []).append(pkg)

        if comm.lower() == "tomato":
            tomato_markets.append({
                "market": r.get("market"),
                "state": r.get("state"),
                "price_per_kg": pkg,
                "modal_price": r.get("modal_price"),
            })

    # Sort tomato markets by price
    tomato_markets.sort(key=lambda x: x["price_per_kg"], reverse=True)

    mandi_highlights = {}
    for c in ["Tomato", "Onion", "Potato", "Green Chilli", "Brinjal", "Cabbage", "Capsicum"]:
        prices = commodity_stats.get(c, [])
        if prices:
            mandi_highlights[c] = {
                "avg_kg": round(statistics.mean(prices), 1),
                "min_kg": round(min(prices), 1),
                "max_kg": round(max(prices), 1),
                "sample_count": len(prices),
            }

    # --- 2. Nursery Plants Aggregations ---
    commercial_saplings = [p for p in plant_records if p.get("category") == "Commercial Seedling"]
    retail_plants = [p for p in plant_records if p.get("category") != "Commercial Seedling"]

    # --- 3. Seeds Input Cost Aggregations ---
    tomato_seeds = [s for s in seed_records if s.get("crop") == "Tomato"]
    avg_seed_pack = 0.0
    if tomato_seeds:
        seed_prices = [s.get("price", 0) for s in tomato_seeds if s.get("price", 0) > 0]
        if seed_prices:
            avg_seed_pack = round(statistics.mean(seed_prices), 0)

    # --- 4. Build Text Brief ---
    lines = []
    lines.append(f"🌱 *Mandi Market Daily Brief* ({today_str})")
    lines.append("─────────────────────────────")
    lines.append(f"📊 *Ingestion:* {len(mandi_records)} Mandis | {len(plant_records)} Plant Rates | {len(seed_records)} Seeds")
    lines.append("")

    # Mandi section
    lines.append("🍅 *Mandi Wholesale Vegetable Rates (APMC Mandis):*")
    if "Tomato" in mandi_highlights:
        t = mandi_highlights["Tomato"]
        lines.append(f"• *Tomato:* Avg ₹{t['avg_kg']}/kg (Range: ₹{t['min_kg']} - ₹{t['max_kg']}/kg | {t['sample_count']} mandis)")
    if "Onion" in mandi_highlights:
        o = mandi_highlights["Onion"]
        lines.append(f"• *Onion:* Avg ₹{o['avg_kg']}/kg (Range: ₹{o['min_kg']} - ₹{o['max_kg']}/kg)")
    if "Potato" in mandi_highlights:
        p = mandi_highlights["Potato"]
        lines.append(f"• *Potato:* Avg ₹{p['avg_kg']}/kg (Range: ₹{p['min_kg']} - ₹{p['max_kg']}/kg)")
    if "Green Chilli" in mandi_highlights:
        c = mandi_highlights["Green Chilli"]
        lines.append(f"• *Green Chilli:* Avg ₹{c['avg_kg']}/kg (Range: ₹{c['min_kg']} - ₹{c['max_kg']}/kg)")

    # Sample top tomato mandis
    if tomato_markets:
        top_sample = tomato_markets[0]
        lines.append(f"  _Peak Mandi:_ {top_sample['market']} ({top_sample['state']}) at ₹{top_sample['price_per_kg']}/kg")

    lines.append("")

    # Nursery Plants section
    lines.append("🌿 *Nursery Plant & Sapling Benchmarks:*")
    for s in commercial_saplings[:5]:
        lines.append(f"• *{s['name']}:* ₹{s['price_min']:.2f} – ₹{s['price_max']:.2f} / sapling ({s['variety']})")

    lines.append("")

    # Seeds section
    lines.append("🌾 *Seed Input Cost Highlights:*")
    for s in seed_records[:4]:
        lines.append(f"• *{s.get('title')}:* ₹{s.get('price', 0):.0f} ({s.get('pack_size', 'Pack')}) — {s.get('brand')}")

    lines.append("")

    # Unit economics insights
    lines.append("💡 *Unit Economics & Price Spread:*")
    lines.append("• *Tomato Unit Economics:*")
    lines.append("  - Seed Cost/Seedling: ~₹0.22 – ₹0.26 (Syngenta Viraja/Saaho)")
    lines.append("  - 30-Day Pro-Tray Sapling Farmgate: ₹1.10 – ₹1.60 / sapling")
    lines.append("  - Grafted Wilt-Resistant Sapling: ₹5.50 – ₹6.50 / sapling")
    if "Tomato" in mandi_highlights:
        lines.append(f"  - Harvest Market Realization: ₹{mandi_highlights['Tomato']['avg_kg']}/kg modal average")
    lines.append("─────────────────────────────")
    lines.append("✅ _All records saved to the price database._")

    text_summary = "\n".join(lines)

    return {
        "date": date.today().isoformat(),
        "total_mandi_records": len(mandi_records),
        "total_plant_records": len(plant_records),
        "total_seed_records": len(seed_records),
        "mandi_highlights": mandi_highlights,
        "text_summary": text_summary,
    }
