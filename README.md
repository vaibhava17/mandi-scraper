# 🌾 Mandi Scraper: Unified Market Intelligence Engine

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

An automated agricultural data pipeline that aggregates pan-India daily wholesale vegetable mandi prices, nursery seedling & sapling rates, and commercial hybrid seed costs into a single analytical engine.

The data is useful for price forecasting, nursery margin analysis, and grower advisory tools.

---

## 🏗️ System Architecture

```text
                               ┌─────────────────────────────────┐
                               │     Mandi Scraper       │
                               └────────────────┬────────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
      ┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
      │   Mandi Scraper    │         │  Nursery Scraper   │         │   Seeds Scraper    │
      │ (APMC / AGMARKNET) │         │ (Saplings & Trays) │         │(Hybrids & Packets) │
      └──────────┬─────────┘         └──────────┬─────────┘         └──────────┬─────────┘
                 │                              │                              │
                 └──────────────────────────────┼──────────────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │    MongoDB Storage    │
                                    │ (mandi_scraper)│
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Analytics & Brief    │
                                    │ (Daily 1:00 AM IST)   │
                                    └───────────────────────┘
```

---

## 🎯 What It Tracks ("All Three in One")

### 1. 🍅 Mandi Wholesale Vegetable Rates
- **Source:** Directorate of Marketing & Inspection (DMI), Ministry of Agriculture via **AGMARKNET** & **data.gov.in** OGD APIs.
- **Coverage:** All 28 Indian States & UTs across major APMC wholesale mandis (Azadpur, Vashi, Lasalgaon, Kolar, Agra, Pune, etc.).
- **Commodities:** Tomato, Onion, Potato, Green Chilli, Brinjal, Capsicum, Cabbage, Cauliflower, Cucumber, Peas, etc.
- **Metrics:** Min Price, Max Price, Modal Price (₹/quintal) and normalized ₹/kg.

### 2. 🌿 Nursery Plants & Sapling Rate Cards
- **Commercial Benchmarks:** 25–30 day pro-tray vegetable seedlings (104 & 126 cavity trays) including Syngenta Saaho/Abhinav Tomato saplings, wilt-resistant grafted saplings, VNR Chilli, and Papaya saplings.
- **Live Nursery Catalogs:** Scraped retail and wholesale pricing for potted plants, grafted fruit trees, and nursery propagation equipment.
- **Metrics:** Cost per seedling, grafted premium, unit pricing.

### 3. 🌾 Seed Catalog Prices & Input Costs
- **Source:** Major Indian seed distributors and marketplaces (AgriBegri, TrustBasket, leading seed houses like Syngenta, Bayer Seminis, Namdhari, VNR).
- **Varieties:** F1 Hybrid vegetable seeds and open-pollinated (OP/Desi) varieties.
- **Metrics:** Packet size (3,000 seeds / 10g), MRP, discounted farmgate price, seed rate per acre, and estimated yield potential.

---

## 💾 MongoDB Data Schema

The database `mandi_scraper` maintains four indexed collections:

| Collection | Key Fields | Indexes |
| :--- | :--- | :--- |
| `mandi_prices` | `state`, `district`, `market`, `commodity`, `variety`, `modal_price`, `price_per_kg`, `arrival_date` | Compound Unique: `(state, district, market, commodity, variety, arrival_date)` |
| `nursery_plants` | `name`, `category`, `variety`, `plant_stage`, `price`, `unit`, `vendor`, `scraped_date` | Compound Unique: `(name, vendor, scraped_date)` |
| `seed_prices` | `title`, `crop`, `variety`, `brand`, `pack_size`, `price`, `mrp`, `vendor`, `scraped_date` | Compound Unique: `(title, vendor, scraped_date)` |
| `daily_summaries`| `date`, `total_mandi_records`, `mandi_highlights`, `text_summary` | Unique: `date` |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- MongoDB 6.0+ (Local or Docker)

### Option A: Direct Local Run

1. **Clone & setup dependencies:**
   ```bash
   git clone https://github.com/vaibhava17/mandi-scraper.git
   cd mandi-scraper
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if using a custom MongoDB connection or OGD API Key
   ```

3. **Execute daily pipeline:**
   ```bash
   python src/main.py
   ```

### Option B: Docker Compose

```bash
docker compose up -d mongo
docker compose run --rm scraper
```

---

## ⏰ Automated Daily Run (Cron)

To run automatically at **1:00 AM IST every day** and log output:

```bash
0 1 * * * cd /path/to/mandi-scraper && python3 src/main.py >> /var/log/agri_pulse.log 2>&1
```

---

## 📊 Sample Output Brief

```text
🌱 Mandi Market Daily Brief (28 Sep 2026)
─────────────────────────────
📊 Ingestion: 200 Mandis | 42 Plant Rates | 78 Seeds

🍅 Mandi Wholesale Vegetable Rates (APMC Mandis):
• Tomato: Avg ₹28.4/kg (Range: ₹14.0 - ₹48.0/kg | 46 mandis)
• Onion: Avg ₹36.8/kg (Range: ₹18.0 - ₹55.0/kg)
• Potato: Avg ₹22.5/kg (Range: ₹12.0 - ₹32.0/kg)
• Green Chilli: Avg ₹42.0/kg (Range: ₹25.0 - ₹65.0/kg)
  Peak Mandi: APMC Azadpur (Delhi) at ₹48.0/kg

🌿 Nursery Plant & Sapling Benchmarks:
• Hybrid Tomato Sapling (25-30 Days): ₹0.85 – ₹1.60 / sapling (Syngenta Saaho / US 440)
• Grafted Tomato Sapling: ₹4.50 – ₹7.50 / sapling (Bacterial Wilt Resistant)
• Hybrid Green Chilli Sapling: ₹0.90 – ₹1.80 / sapling (VNR 332 / Sitara)
• Papaya Grafted / Taiwan 786: ₹25.00 – ₹45.00 / sapling (Red Lady 786)

🌾 Seed Input Cost Highlights:
• Syngenta Viraja (TO-7414) F1 Hybrid: ₹755 (3000 seeds) — Syngenta India Ltd.
• Syngenta Saaho (TO-3251) F1 Hybrid: ₹795 (3000 seeds) — Syngenta India Ltd.
• Seminis Abhinav F1 Hybrid Tomato: ₹820 (10g) — Bayer Seminis

💡 Unit Economics & Price Spread:
• Tomato Unit Economics:
  - Seed Cost/Seedling: ~₹0.22 – ₹0.26
  - 30-Day Pro-Tray Sapling Farmgate: ₹1.10 – ₹1.60 / sapling
  - Grafted Wilt-Resistant Sapling: ₹5.50 – ₹6.50 / sapling
  - Harvest Market Realization: ₹28.4/kg modal average
─────────────────────────────
✅ All records indexed in MongoDB collection mandi_scraper.
```

---

## 📄 License
MIT © [Vaibhav Agarwal](https://github.com/vaibhava17)
