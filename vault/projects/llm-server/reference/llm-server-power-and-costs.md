# LLM desktop server — power draw and rough electricity cost

Companion to [`llm-server-on-desktop.md`](vault/projects/llm-server/done/llm-server-on-desktop.md). This note records **order-of-magnitude** average power for the repurposed PC, converts it to **kWh/year**, and applies **variable energy (sprzedaż)** pricing from the attached Tauron tariff PDF. It is **not** a substitute for a watt-meter measurement or a full bill breakdown.

## Hardware (reference)

| Component | Spec |
|---|---|
| CPU | Intel Core i7-6700 (65 W TDP, 4C/8T) |
| GPU | NVIDIA GeForce RTX 3060 Ti LHR, **8 GB VRAM** |
| RAM | 24 GB DDR4 |
| Cooling | Corsair H110i |
| PSU | SilentiumPC VERO M1 600 W |
| OS | Ubuntu (typically Server or trimmed Desktop) |

All power figures below are **at the wall** (AC), not DC component sums.

***

## Scenario definitions

| Scenario | Description |
|---|---|
| **A — Light 24/7** | Machine mostly idle: Ollama up, minimal CPU, GPU near idle (rare tiny requests). |
| **B — Moderate, GPU sometimes** | Regular background load; embeddings bursts, occasional chat; GPU active only part of the time. **Average** power depends heavily on **duty cycle**. |
| **C — Moderate, LLM on GPU most of the time** | Steady inference / warm serving; GPU dominates average draw. |

***

## Estimated average power (at the wall)

Rough **W** bands for continuous operation:

| Scenario | Typical average power |
|---|---|
| A — Light | **~70–120 W** |
| B — Moderate + occasional GPU | **~110–170 W** (wider if GPU is busy often) |
| C — Moderate + GPU most of the time | **~160–260 W** (peaks during heavy prefill can exceed the average) |

**Sanity check:** These align with the ballpark already noted in `llm-server-on-desktop.md` (~80–100 W idle-ish, ~200–250 W under sustained GPU inference), expressed here as **ranges** and **scenarios**.

***

## Energy per year

For a **constant** average power (P) (watts):

[
\text{kWh/year} \approx \frac{P}{1000} \times 8760
]

**Quick scale:** 100 W average ≈ **876 kWh/year**; 200 W ≈ **1752 kWh/year**.

***

## Electricity cost (variable energy only — Tauron Sprzedaż)

### Source

Tariff document: [`taryfa-dla-energii-elektrycznej.PDF`](vault/projects/llm-server/reference/taryfa-dla-energii-elektrycznej.PDF) (TAURON Sprzedaż, grupy **G**, decyzja z 28.06.2024). The PDF states that **Tabela nr 1** (ceny maksymalne) applies when **lower** than **Tabela nr 2**.

### Rate used here (G11 — Dom Wygodny, całodobowa)

For **G11**, comparing **brutto** values from those tables:

| | zł/kWh brutto |
|---|---|
| Tabela nr 1 | **0,6212** |
| Tabela nr 2 | 0,7774 |

→ **Effective rate for this estimate:** **0,6212 zł/kWh** (commodity **energy** component including excise and VAT as presented in the tables).

**Important:** This applies to the **sprzedaż energii** line only. See **Caveats**.

### Formula

[
\text{zł/year (energy only)} \approx \text{kWh/year} \times 0{,}6212
]

Rule of thumb for **G11** at this rate: **~5,44 zł per year per watt** of *average* continuous draw ((8760 \times 0{,}6212 / 1000)).

### Rough cost table (G11 @ 0,6212 zł/kWh, energy only)

Illustrative **mid-range** and **endpoints** within the power bands above:

| Scenario | Assumed avg. power | kWh/year | ~zł/year (sprzedaż) | ~zł/month |
|---|---:|---:|---:|---:|
| A Light | 80 W | ~701 | ~435 | ~36 |
| A Light | 100 W | ~876 | ~544 | ~45 |
| A Light | 120 W | ~1051 | ~653 | ~54 |
| B Moderate + GPU sometimes | 140 W | ~1227 | ~762 | ~63 |
| B Moderate + GPU sometimes | 170 W | ~1490 | ~925 | ~77 |
| C LLM on GPU most of the time | 200 W | ~1752 | ~1088 | ~91 |
| C LLM on GPU most of the time | 230 W | ~2015 | ~1252 | ~104 |
| C LLM on GPU most of the time | 260 W | ~2278 | ~1415 | ~118 |

Monthly figures use (\approx 730{,}5) hours per month: (\text{kWh/mo} \approx P_\text{kW} \times 730{,}5).

***

## Caveats (read before trusting the zł)

1. **Not the full electricity bill.** The PDF prices **sold energy** (TAURON **Sprzedaż**). Invoices also include **dystrybucja** (TAURON **Dystrybucja** / OSD), often **abonament**, **opłata mocowa**, and other items. **Total cost is higher** than “kWh × 0,6212” alone.

2. **Tariff group matters.** Costs above assume **G11** (single całodobowa stawka). If the household is **G12** (day/night) or **G13** (three zones), effective **average** zł/kWh depends on **when** the PC runs. For **uniform 24/7** load, a **time-weighted** blend of zone rates applies (still not equal to G11 unless your contract matches that simplification).

3. **“Lower of Table 1 vs Table 2” may change over time.** The PDF contains **multiple date ranges** (e.g. sections 5.1 / 5.1a and different regulatory periods). **Verify** the rate on your **current** bill or supplier communication.

4. **Shielding / “rozwiązania osłonowe”.** The tariff PDF mentions protective measures (e.g. through **30.09.2025**). **Actual** settlements can differ from a naive kWh × tariff multiplication.

5. **Power estimates are bands, not guarantees.** Driver versions, **fan curves**, **headless vs display attached**, background services, disk activity, and **GPU idle** behaviour (multi-monitor can raise idle GPU draw) all shift the average.

6. **Scenario B is duty-cycle sensitive.** “Sometimes GPU” means the **average** W depends on **how often** and **how hard** the GPU runs; the table is illustrative.

7. **Scenario C has burst peaks.** Sustained inference averages are in the quoted band; **short** prefill or batch spikes can **exceed** the average power (cost impact depends on how long those spikes last relative to the billing period — for **kWh**, what matters is energy over time).

8. **DC vs wall.** Internal component “TDP” figures do not include PSU losses; **at-the-wall** metering is the ground truth.

9. **Measurement beats spreadsheets.** A **kill-a-watt style** meter (or logging **smart plug** / **PDU**) for a **representative week** per scenario collapses most uncertainty.

10. **Currency and date.** All monetary amounts are **PLN**; tariff components are tied to **regulatory** documents and **dates** in the PDF — **re-check** before long-term budgeting.

***

## Related files

- [`llm-server-on-desktop.md`](vault/projects/llm-server/done/llm-server-on-desktop.md) — architecture, models, setup
- [`taryfa-dla-energii-elektrycznej.PDF`](vault/projects/llm-server/reference/taryfa-dla-energii-elektrycznej.PDF) — tariff source for the **0,6212 zł/kWh** G11 comparison above
