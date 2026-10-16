"""Modern AI Travel Agent Portal with adaptive Light/Dark themes, timeline cards, and financial telemetry."""
import html
import gradio as gr
import pandas as pd

from app.agent.core import plan_trip
from app.schemas import TripPlanResponse
from app.tools.attractions import search_attractions
from app.tools.memory import delete_memory, get_memories, save_memory

# ---------------------------------------------------------------------------
# Custom CSS: Clean Adaptive Light / Dark Theme for Travel Agent Interface
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* --- LIGHT THEME (Default) --- */
:root {
    --bg-page: #f8fafc;
    --card-bg: #ffffff;
    --card-subtle-bg: #f8fafc;
    --border-subtle: #e2e8f0;
    --border-strong: #cbd5e1;
    --text-main: #0f172a;
    --text-muted: #64748b;
    --primary: #059669;
    --primary-light: #ecfdf5;
    --primary-border: #a7f3d0;
    --hero-bg: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
    --hero-border: #bbf7d0;
    --hero-title: #064e3b;
    --stay-bg: #f5f3ff;
    --stay-border: #ddd6fe;
    --stay-text: #4338ca;
    --food-bg: #fffbeb;
    --food-border: #fde68a;
    --food-text: #b45309;
    --transit-bg: #f0f9ff;
    --transit-border: #bae6fd;
    --transit-text: #0369a1;
    --tickets-bg: #ecfdf5;
    --tickets-border: #a7f3d0;
    --tickets-text: #047857;
    --tag-bg: #f1f5f9;
    --tag-text: #475569;
    --table-header-bg: #f8fafc;
    --table-border: #f1f5f9;
    --agent-callout-bg: #f8fafc;
    --agent-callout-text: #334155;
    --empty-bg: #ffffff;
    --empty-border: #cbd5e1;
    --empty-title: #1e293b;
}

/* --- DARK THEME (Gradio .dark or System Dark Mode) --- */
body.dark,
.dark,
gradio-app.dark,
[data-theme="dark"] {
    --bg-page: #0b0f19 !important;
    --card-bg: #1e293b !important;
    --card-subtle-bg: #0f172a !important;
    --border-subtle: #334155 !important;
    --border-strong: #475569 !important;
    --text-main: #f8fafc !important;
    --text-muted: #94a3b8 !important;
    --primary: #10b981 !important;
    --primary-light: rgba(16, 185, 129, 0.15) !important;
    --primary-border: #059669 !important;
    --hero-bg: linear-gradient(135deg, #1e293b 0%, rgba(6, 78, 59, 0.3) 100%) !important;
    --hero-border: #059669 !important;
    --hero-title: #34d399 !important;
    --stay-bg: rgba(49, 46, 129, 0.25) !important;
    --stay-border: #4338ca !important;
    --stay-text: #a5b4fc !important;
    --food-bg: rgba(120, 53, 15, 0.25) !important;
    --food-border: #b45309 !important;
    --food-text: #fcd34d !important;
    --transit-bg: rgba(7, 89, 133, 0.25) !important;
    --transit-border: #0284c7 !important;
    --transit-text: #7dd3fc !important;
    --tickets-bg: rgba(6, 78, 59, 0.25) !important;
    --tickets-border: #10b981 !important;
    --tickets-text: #6ee7b7 !important;
    --tag-bg: #334155 !important;
    --tag-text: #cbd5e1 !important;
    --table-header-bg: #0f172a !important;
    --table-border: #334155 !important;
    --agent-callout-bg: #0f172a !important;
    --agent-callout-text: #cbd5e1 !important;
    --empty-bg: #1e293b !important;
    --empty-border: #334155 !important;
    --empty-title: #f8fafc !important;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-page: #0b0f19;
        --card-bg: #1e293b;
        --card-subtle-bg: #0f172a;
        --border-subtle: #334155;
        --border-strong: #475569;
        --text-main: #f8fafc;
        --text-muted: #94a3b8;
        --primary: #10b981;
        --primary-light: rgba(16, 185, 129, 0.15);
        --primary-border: #059669;
        --hero-bg: linear-gradient(135deg, #1e293b 0%, rgba(6, 78, 59, 0.3) 100%);
        --hero-border: #059669;
        --hero-title: #34d399;
        --stay-bg: rgba(49, 46, 129, 0.25);
        --stay-border: #4338ca;
        --stay-text: #a5b4fc;
        --food-bg: rgba(120, 53, 15, 0.25);
        --food-border: #b45309;
        --food-text: #fcd34d;
        --transit-bg: rgba(7, 89, 133, 0.25);
        --transit-border: #0284c7;
        --transit-text: #7dd3fc;
        --tickets-bg: rgba(6, 78, 59, 0.25);
        --tickets-border: #10b981;
        --tickets-text: #6ee7b7;
        --tag-bg: #334155;
        --tag-text: #cbd5e1;
        --table-header-bg: #0f172a;
        --table-border: #334155;
        --agent-callout-bg: #0f172a;
        --agent-callout-text: #cbd5e1;
        --empty-bg: #1e293b;
        --empty-border: #334155;
        --empty-title: #f8fafc;
    }
}

/* Global Container */
.gradio-container {
    max-width: 1320px !important;
    margin: 0 auto !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    background-color: var(--bg-page) !important;
}

/* Fix Tab Typography & Contrast in Dark Mode */
button[role="tab"] {
    font-weight: 600 !important;
    font-size: 14px !important;
    color: var(--text-muted) !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s ease !important;
}
button[role="tab"][aria-selected="true"],
.selected[role="tab"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
    background: transparent !important;
}

/* Clean Input Labels: remove distracting green blocks */
label span {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    padding: 0 !important;
    margin-bottom: 4px !important;
}

/* Navbar Header */
.travel-navbar {
    background: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.brand-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 800;
    color: var(--text-main);
    letter-spacing: -0.02em;
}
.brand-badge {
    background: var(--primary-light);
    color: var(--primary);
    border: 1px solid var(--primary-border);
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* Hero Destination Card */
.trip-hero-card {
    background: var(--hero-bg);
    border: 1px solid var(--hero-border);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.trip-destination-title {
    font-size: 24px;
    font-weight: 800;
    color: var(--hero-title);
    letter-spacing: -0.02em;
    margin: 0 0 6px 0;
}
.trip-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-top: 10px;
}
.trip-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--card-bg);
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-main);
}

/* Metric Stats Cards */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 12px;
    margin-bottom: 18px;
}
.metric-box {
    background: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-box .label {
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.metric-box .val {
    font-size: 20px;
    font-weight: 800;
    color: var(--text-main);
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
}
.metric-box .note {
    font-size: 11.5px;
    color: var(--text-muted);
    margin-top: 2px;
}

/* Financial Section */
.finance-panel {
    background: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.finance-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 700;
    font-size: 15px;
    color: var(--text-main);
    margin-bottom: 10px;
}
.multi-progress-bar {
    display: flex;
    height: 10px;
    border-radius: 6px;
    overflow: hidden;
    background: var(--border-subtle);
    margin: 10px 0 14px 0;
}
.progress-seg {
    height: 100%;
}
.spend-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin-bottom: 12px;
}
.spend-box {
    border-radius: 8px;
    padding: 10px 12px;
    border: 1px solid transparent;
}
.spend-box.stay { background: var(--stay-bg); border-color: var(--stay-border); color: var(--stay-text); }
.spend-box.food { background: var(--food-bg); border-color: var(--food-border); color: var(--food-text); }
.spend-box.transit { background: var(--transit-bg); border-color: var(--transit-border); color: var(--transit-text); }
.spend-box.tickets { background: var(--tickets-bg); border-color: var(--tickets-border); color: var(--tickets-text); }
.spend-box .hdr { font-size: 12px; font-weight: 700; }
.spend-box .amt { font-size: 17px; font-weight: 800; margin: 3px 0 1px 0; color: var(--text-main); }
.spend-box .sub { font-size: 11px; color: var(--text-muted); }

/* Day Timeline Cards */
.timeline-card {
    background: var(--card-bg);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.day-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 10px;
}
.day-pill {
    background: var(--primary);
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 9px;
    border-radius: 6px;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.attraction-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px dashed var(--border-subtle);
}
.attraction-item:last-child {
    border-bottom: none;
}
.attr-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-main);
}
.badge-tag {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 600;
    background: var(--tag-bg);
    color: var(--tag-text);
    margin-left: 5px;
}

/* Agent Note */
.agent-callout {
    background: var(--agent-callout-bg);
    border-left: 3px solid var(--primary);
    border-radius: 0 8px 8px 0;
    padding: 12px 14px;
    font-size: 12.5px;
    color: var(--agent-callout-text);
    margin-top: 14px;
}
"""


def _generate_dashboard_html(plan: TripPlanResponse) -> str:
    """Generate responsive travel dashboard that adapts to Light and Dark themes."""
    b = plan.budget
    nights = max(plan.duration_days - 1, 0)

    # Budget Status Pill
    if b.is_within_budget:
        budget_chip = f'<span style="background:var(--tickets-bg);color:var(--tickets-text);border:1px solid var(--tickets-border);padding:4px 10px;border-radius:9999px;font-size:12px;font-weight:700;">✓ Within Budget (₹{b.remaining:,.0f} surplus)</span>'
    else:
        budget_chip = f'<span style="background:rgba(225,29,72,0.15);color:#f43f5e;border:1px solid #f43f5e;padding:4px 10px;border-radius:9999px;font-size:12px;font-weight:700;">⚠ Over Budget by ₹{abs(b.remaining):,.0f}</span>'

    # Weather Chip
    weather_desc = "Forecast Pending"
    if plan.weather:
        weather_desc = f"{plan.weather.temperature_current}°C, {plan.weather.condition}"

    hero_html = f"""
    <div class="trip-hero-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <h2 class="trip-destination-title">📍 {html.escape(plan.city)}</h2>
                <div style="font-size:13px;color:var(--text-muted);">Customized {plan.duration_days}-Day Itinerary for {plan.travelers} Traveler(s)</div>
            </div>
            <div>{budget_chip}</div>
        </div>
        <div class="trip-chip-row">
            <span class="trip-chip">📅 {plan.duration_days} Days / {nights} Nights</span>
            <span class="trip-chip">👥 {plan.travelers} Traveler(s)</span>
            <span class="trip-chip">🚕 {html.escape(plan.transportation.mode)} Commute</span>
            <span class="trip-chip">🌤️ {html.escape(weather_desc)}</span>
        </div>
    </div>
    """

    # 4 Key Metrics Cards
    metrics_html = f"""
    <div class="metrics-row">
        <div class="metric-box">
            <div class="label">Total Budget</div>
            <div class="val">₹{b.total_budget:,.0f}</div>
            <div class="note">Stated spending limit</div>
        </div>
        <div class="metric-box">
            <div class="label">Estimated Spend</div>
            <div class="val" style="color: {'var(--primary)' if b.is_within_budget else '#f43f5e'};">₹{b.estimated_total:,.0f}</div>
            <div class="note">{(b.estimated_total / max(b.total_budget, 1.0)) * 100:.1f}% of budget allocated</div>
        </div>
        <div class="metric-box">
            <div class="label">Net Balance</div>
            <div class="val">₹{b.remaining:,.0f}</div>
            <div class="note">{'Remaining reserve funds' if b.is_within_budget else 'Budget shortfall'}</div>
        </div>
        <div class="metric-box">
            <div class="label">Daily Avg / Person</div>
            <div class="val">₹{b.estimated_total / max(plan.travelers * plan.duration_days, 1):,.0f}</div>
            <div class="note">All-inclusive daily rate</div>
        </div>
    </div>
    """

    # Financial Breakdown
    total_spent = max(b.estimated_total, 1.0)
    stay_pct = (b.accommodation_cost / total_spent) * 100
    food_pct = (b.food_cost / total_spent) * 100
    trans_pct = (b.transport_cost / total_spent) * 100
    fee_pct = (b.attraction_fees / total_spent) * 100

    daily_food_rate = (b.food_cost / (plan.travelers * plan.duration_days)) if (plan.travelers * plan.duration_days) > 0 else 500

    ticket_rows = ""
    seen_places = set()
    for day in plan.itinerary:
        for a in day.attractions:
            if a.name in seen_places:
                continue
            seen_places.add(a.name)
            total_fee = a.fee_per_person * plan.travelers
            calc_text = f"₹{a.fee_per_person:.0f} × {plan.travelers} traveler(s)" if a.fee_per_person > 0 else "Free dataset entry"
            ticket_rows += f"""
            <tr style="border-bottom:1px solid var(--border-subtle);font-size:12.5px;">
                <td style="padding:7px 8px;color:var(--text-main);"><strong>{html.escape(a.name)}</strong> ({html.escape(a.category)})</td>
                <td style="padding:7px 8px;color:var(--tickets-text);">🎟️ Sightseeing</td>
                <td style="padding:7px 8px;color:var(--text-muted);">{calc_text}</td>
                <td style="padding:7px 8px;text-align:right;font-weight:700;color:var(--text-main);">₹{total_fee:,.0f}</td>
            </tr>
            """

    finance_html = f"""
    <div class="finance-panel">
        <div class="finance-panel-header">
            <span>💳 Where the Money Goes</span>
            <span style="font-size:12.5px;color:var(--text-muted);font-weight:600;">Total Outlay: <strong>₹{b.estimated_total:,.0f}</strong></span>
        </div>

        <div class="multi-progress-bar">
            <div class="progress-seg" style="width:{stay_pct}%;background:#818cf8;" title="Stay: ₹{b.accommodation_cost:,.0f}"></div>
            <div class="progress-seg" style="width:{food_pct}%;background:#f59e0b;" title="Food: ₹{b.food_cost:,.0f}"></div>
            <div class="progress-seg" style="width:{trans_pct}%;background:#38bdf8;" title="Transit: ₹{b.transport_cost:,.0f}"></div>
            <div class="progress-seg" style="width:{fee_pct}%;background:#34d399;" title="Tickets: ₹{b.attraction_fees:,.0f}"></div>
        </div>

        <div class="spend-grid">
            <div class="spend-box stay">
                <div class="hdr">🏨 Stay & Hotel</div>
                <div class="amt">₹{b.accommodation_cost:,.0f}</div>
                <div class="sub">{stay_pct:.1f}% • {nights} night(s)</div>
            </div>
            <div class="spend-box food">
                <div class="hdr">🍽️ Dining & Food</div>
                <div class="amt">₹{b.food_cost:,.0f}</div>
                <div class="sub">{food_pct:.1f}% • ₹{daily_food_rate:.0f}/day/person</div>
            </div>
            <div class="spend-box transit">
                <div class="hdr">🚕 Transit & Autos</div>
                <div class="amt">₹{b.transport_cost:,.0f}</div>
                <div class="sub">{trans_pct:.1f}% • {html.escape(plan.transportation.mode)}</div>
            </div>
            <div class="spend-box tickets">
                <div class="hdr">🎟️ Attraction Passes</div>
                <div class="amt">₹{b.attraction_fees:,.0f}</div>
                <div class="sub">{fee_pct:.1f}% • {len(seen_places)} places</div>
            </div>
        </div>

        <details style="margin-top:10px;cursor:pointer;">
            <summary style="font-size:12px;font-weight:700;color:var(--primary);padding:4px 0;">
                ▶ View Itemized Cost Ledger (Where Every Rupee is Spent)
            </summary>
            <table style="width:100%;border-collapse:collapse;margin-top:8px;">
                <thead>
                    <tr style="background:var(--table-header-bg);font-size:11px;text-transform:uppercase;color:var(--text-muted);text-align:left;border-bottom:1px solid var(--border-subtle);">
                        <th style="padding:6px 8px;">Expense Line Item</th>
                        <th style="padding:6px 8px;">Category</th>
                        <th style="padding:6px 8px;">Calculation Basis</th>
                        <th style="padding:6px 8px;text-align:right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid var(--border-subtle);font-size:12.5px;">
                        <td style="padding:7px 8px;color:var(--text-main);"><strong>Hotel / Guesthouse Lodging</strong></td>
                        <td style="padding:7px 8px;color:var(--stay-text);">🏨 Stay</td>
                        <td style="padding:7px 8px;color:var(--text-muted);">{nights} nights @ ₹1,500/room/night</td>
                        <td style="padding:7px 8px;text-align:right;font-weight:700;color:var(--text-main);">₹{b.accommodation_cost:,.0f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border-subtle);font-size:12.5px;">
                        <td style="padding:7px 8px;color:var(--text-main);"><strong>Breakfast, Lunch & Dinner</strong></td>
                        <td style="padding:7px 8px;color:var(--food-text);">🍽️ Food</td>
                        <td style="padding:7px 8px;color:var(--text-muted);">{plan.travelers} travelers × {plan.duration_days} days @ ₹{daily_food_rate:.0f}/day</td>
                        <td style="padding:7px 8px;text-align:right;font-weight:700;color:var(--text-main);">₹{b.food_cost:,.0f}</td>
                    </tr>
                    <tr style="border-bottom:1px solid var(--border-subtle);font-size:12.5px;">
                        <td style="padding:7px 8px;color:var(--text-main);"><strong>Local Rides & Transfers</strong></td>
                        <td style="padding:7px 8px;color:var(--transit-text);">🚕 Transit</td>
                        <td style="padding:7px 8px;color:var(--text-muted);">{plan.duration_days} days of {html.escape(plan.transportation.mode)} rides</td>
                        <td style="padding:7px 8px;text-align:right;font-weight:700;color:var(--text-main);">₹{b.transport_cost:,.0f}</td>
                    </tr>
                    {ticket_rows}
                    <tr style="background:var(--table-header-bg);font-weight:800;font-size:13px;border-top:2px solid var(--border-strong);">
                        <td colspan="3" style="padding:8px;color:var(--text-main);">Total Estimated Trip Cost</td>
                        <td style="padding:8px;text-align:right;color:var(--primary);">₹{b.estimated_total:,.0f}</td>
                    </tr>
                </tbody>
            </table>
        </details>
    </div>
    """

    # Day-by-Day Timeline
    timeline_html = ""
    for day in plan.itinerary:
        rows = ""
        for a in day.attractions:
            fee_tag = f"₹{a.fee_per_person:,.0f}/person" if a.fee_per_person > 0 else "Free Entry"
            rating_badge = f'<span class="badge-tag" style="background:var(--food-bg);color:var(--food-text);">★ {a.rating:.1f}</span>' if a.rating > 0 else ""
            rows += f"""
            <div class="attraction-item">
                <div>
                    <span class="attr-title">{html.escape(a.name)}</span>
                    <span class="badge-tag">{html.escape(a.category)}</span>
                    <span class="badge-tag" style="color:var(--transit-text);background:var(--transit-bg);">⏱ {a.time_needed_hours:g} hrs</span>
                    {rating_badge}
                </div>
                <div style="font-size:12px;color:var(--text-muted);">
                    <strong style="color:var(--text-main);">{fee_tag}</strong>
                    <span class="badge-tag">Best: {html.escape(a.best_time)}</span>
                </div>
            </div>
            """

        timeline_html += f"""
        <div class="timeline-card">
            <div class="day-header-row">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="day-pill">Day {day.day}</span>
                    <span style="font-size:14px;font-weight:700;color:var(--text-main);">{html.escape(day.theme)}</span>
                </div>
                <div style="font-size:12px;font-weight:700;color:var(--primary);background:var(--primary-light);padding:3px 8px;border-radius:6px;">
                    Est. Day Outlay: ₹{day.estimated_day_cost:,.0f}
                </div>
            </div>
            {rows if rows else '<div style="color:var(--text-muted);font-size:13px;">Free exploration time scheduled.</div>'}
        </div>
        """

    # Agent Synthesis
    agent_html = f"""
    <div class="agent-callout">
        <strong>💡 Agent Intelligence Note:</strong> {html.escape(plan.agent_note)}
    </div>
    """

    return hero_html + metrics_html + finance_html + timeline_html + agent_html


# ---------------------------------------------------------------------------
# Interaction Logic
# ---------------------------------------------------------------------------
USER_LAST_PROMPT = {}


def handle_plan_submission(prompt: str, user_id: str):
    """Generate plan and update visual board."""
    if not prompt or not prompt.strip():
        return "<p style='color:#ef4444;font-size:13px;'>Please enter a destination city or trip instruction.</p>", ""

    clean_user = user_id.strip() if user_id and user_id.strip() else "traveler_one"
    prior_prompt = USER_LAST_PROMPT.get(clean_user)

    try:
        plan_resp = plan_trip(
            prompt=prompt.strip(),
            user_id=clean_user,
            include_weather=True,
            previous_prompt=prior_prompt,
        )
        USER_LAST_PROMPT[clean_user] = prompt.strip()
        dashboard_html = _generate_dashboard_html(plan_resp)
        return dashboard_html, ""
    except Exception as exc:
        err_msg = f"""
        <div style="background:rgba(244,63,94,0.1);border:1px solid #f43f5e;border-radius:10px;padding:16px;color:#f43f5e;font-size:13px;">
            <strong>Planning Notice:</strong> {html.escape(str(exc))}<br>
            <span style="color:var(--text-muted);margin-top:4px;display:block;">Tip: Please specify at least a city name (e.g. <em>'Plan a 3-day trip to Jaipur for 2 people with budget 10000'</em>).</span>
        </div>
        """
        return err_msg, ""


def handle_quick_book(city: str, travelers: int, days: int, budget: float, style: str, user_id: str):
    """Handle booking from form fields."""
    if not city or not city.strip():
        return "<p style='color:#ef4444;font-size:13px;'>Please provide a destination city.</p>", ""

    prompt = (
        f"Plan a {int(days)}-day trip to {city.strip()} for {int(travelers)} people "
        f"with a budget of ₹{budget:.0f}. Focus on {style} attractions."
    )
    return handle_plan_submission(prompt, user_id)


def handle_search_attractions(city: str, category: str):
    """Query attraction dataset for explorer tab."""
    if not city or not city.strip():
        return pd.DataFrame()
    try:
        cat = category.strip() if category and category != "All" else None
        records = search_attractions(city.strip(), category=cat, max_results=50)
        if not records:
            return pd.DataFrame([{"Notice": f"No attractions found for '{city}'"}])

        df = pd.DataFrame(records)
        cols = [c for c in ["Name", "Type", "Google review rating", "Entrance Fee in INR", "time needed to visit in hrs", "Best Time to visit"] if c in df.columns]
        return df[cols].rename(columns={
            "Entrance Fee in INR": "Entry Fee (₹)",
            "Google review rating": "Rating ★",
            "time needed to visit in hrs": "Hours Needed",
        })
    except Exception as exc:
        return pd.DataFrame([{"Error": str(exc)}])


def handle_save_pref(user_id: str, key: str, value: str):
    if not user_id or not key or not value:
        return "All fields are required.", handle_get_prefs(user_id)
    res = save_memory(user_id.strip(), key.strip(), value.strip())
    return res.get("message", "Saved."), handle_get_prefs(user_id)


def handle_get_prefs(user_id: str):
    if not user_id or not user_id.strip():
        return pd.DataFrame([{"Notice": "Enter a Traveler ID to view preferences"}])
    mems = get_memories(user_id.strip())
    if not mems:
        return pd.DataFrame([{"Notice": "No preferences saved yet for this traveler profile."}])
    return pd.DataFrame(mems).rename(columns={
        "memory_key": "Preference",
        "memory_value": "Saved Value",
        "updated_at": "Last Updated",
    })


def handle_delete_pref(user_id: str, key: str):
    if not user_id or not key:
        return "Traveler ID and Key are required.", handle_get_prefs(user_id)
    res = delete_memory(user_id.strip(), key.strip())
    return res.get("message", "Deleted."), handle_get_prefs(user_id)


# ---------------------------------------------------------------------------
# Gradio Application Definition
# ---------------------------------------------------------------------------
def build_app():
    with gr.Blocks(
        title="WanderAI — AI Travel Planning Agent",
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="emerald",
            secondary_hue="sky",
            neutral_hue="slate",
            font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "sans-serif"],
        ),
    ) as demo:

        # Navbar Header
        gr.HTML("""
        <div class="travel-navbar">
            <div class="brand-title">
                <span>🌿 WanderAI</span>
                <span class="brand-badge">Travel Agent Portal</span>
            </div>
            <div style="font-size:12.5px;color:var(--text-muted);font-weight:500;">
                Live Weather • Verified Dataset Fees • Smart Revision
            </div>
        </div>
        """)

        with gr.Tabs():
            # ---------------- TAB 1: Plan & Itinerary ----------------
            with gr.Tab("🗺️ Itinerary & Cost Planner"):
                with gr.Row():
                    # Left Column: Booking Controls
                    with gr.Column(scale=4):
                        with gr.Group():
                            gr.Markdown("#### ✈️ Configure Trip")
                            in_user = gr.Textbox(value="traveler_one", label="Profile ID", max_lines=1)
                            in_city = gr.Textbox(placeholder="e.g. Jaipur, Mumbai, Goa, Delhi", label="Destination City")
                            with gr.Row():
                                in_travelers = gr.Number(value=2, label="Travelers", precision=0, minimum=1, maximum=50)
                                in_days = gr.Number(value=3, label="Days", precision=0, minimum=1, maximum=14)
                            in_budget = gr.Number(value=12000, label="Budget (₹)", step=500)
                            in_style = gr.Dropdown(
                                choices=["Heritage & Forts", "Scenic & Nature", "Cultural & Temples", "Food & Markets", "Balanced"],
                                value="Balanced",
                                label="Travel Style",
                            )
                            btn_plan = gr.Button("✨ Generate Custom Plan", variant="primary")

                        # Conversational Revision Accordion
                        with gr.Accordion("💬 Conversational Revision & Tweaks", open=True):
                            gr.Markdown("<small style='color:var(--text-muted);'>Ask the agent to update the plan on the fly (e.g. <em>'Increase budget to 16000'</em> or <em>'Focus on forts'</em>).</small>")
                            in_chat = gr.Textbox(
                                placeholder="Type revision instructions...",
                                show_label=False,
                                lines=2,
                            )
                            btn_chat = gr.Button("Apply Revision", variant="secondary")

                            gr.Examples(
                                examples=[
                                    "Plan a 2-day trip to Jaipur for 2 people with a budget of ₹8,000",
                                    "Increase the budget to 15000 and focus on forts",
                                    "Plan a 3-day trip to Mumbai for 1 traveler with budget 10000",
                                ],
                                inputs=[in_chat],
                            )

                    # Right Column: Interactive Dashboard
                    with gr.Column(scale=8):
                        out_dashboard = gr.HTML(
                            value="""
                            <div style="background:var(--card-bg);border:1px dashed var(--border-strong);border-radius:14px;padding:60px 20px;text-align:center;">
                                <div style="font-size:36px;margin-bottom:8px;">🗺️</div>
                                <div style="font-size:17px;font-weight:700;color:var(--empty-title);">Your Custom Itinerary Will Appear Here</div>
                                <div style="font-size:13px;color:var(--text-muted);max-width:400px;margin:6px auto 0 auto;">
                                    Specify your destination and budget on the left to generate day-by-day schedules, ticket calculations, and weather viability.
                                </div>
                            </div>
                            """
                        )

                # Events
                btn_plan.click(
                    fn=handle_quick_book,
                    inputs=[in_city, in_travelers, in_days, in_budget, in_style, in_user],
                    outputs=[out_dashboard, in_chat],
                )
                btn_chat.click(
                    fn=handle_plan_submission,
                    inputs=[in_chat, in_user],
                    outputs=[out_dashboard, in_chat],
                )

            # ---------------- TAB 2: Attraction Explorer ----------------
            with gr.Tab("🏛️ Attraction & Fee Explorer"):
                gr.Markdown("#### 🔍 Search Dataset Tourist Attractions")
                with gr.Row():
                    search_city = gr.Textbox(placeholder="e.g. Jaipur, Delhi, Kolkata, Mumbai", label="City / Region")
                    search_cat = gr.Dropdown(
                        choices=["All", "Fort", "Palace", "Museum", "Temple", "Park", "Beach", "Monument"],
                        value="All",
                        label="Category",
                    )
                    btn_search = gr.Button("Search Attractions", variant="primary", scale=0)

                out_table = gr.Dataframe(label="Attractions & Entry Fees", interactive=False)
                btn_search.click(fn=handle_search_attractions, inputs=[search_city, search_cat], outputs=[out_table])

            # ---------------- TAB 3: Profile & Preferences ----------------
            with gr.Tab("👤 Traveler Profile & Memory"):
                gr.Markdown("#### 💾 Traveler Persistent Preferences (SQLite Store)")
                gr.Markdown("<small style='color:var(--text-muted);'>Preferences saved here are automatically referenced by the agent when drafting itineraries.</small>")
                with gr.Row():
                    with gr.Column(scale=5):
                        mem_user = gr.Textbox(value="traveler_one", label="Traveler Profile ID")
                        mem_key = gr.Dropdown(
                            choices=["preferred_category", "interests", "travel_style", "dietary", "hotel_preference"],
                            value="preferred_category",
                            label="Preference Key",
                        )
                        mem_val = gr.Textbox(placeholder="e.g. Fort, Museum, Scenic, Pure Veg", label="Preference Value")
                        with gr.Row():
                            btn_save_mem = gr.Button("Save Preference", variant="primary")
                            btn_del_mem = gr.Button("Delete Key", variant="stop")
                        mem_status = gr.Label(label="Status", show_label=False)

                    with gr.Column(scale=7):
                        gr.Markdown("##### Stored Profile Preferences")
                        btn_refresh_mem = gr.Button("🔄 Refresh", size="sm")
                        mem_table = gr.Dataframe(label="Stored Profile Keys", interactive=False)

                btn_save_mem.click(fn=handle_save_pref, inputs=[mem_user, mem_key, mem_val], outputs=[mem_status, mem_table])
                btn_del_mem.click(fn=handle_delete_pref, inputs=[mem_user, mem_key], outputs=[mem_status, mem_table])
                btn_refresh_mem.click(fn=handle_get_prefs, inputs=[mem_user], outputs=[mem_table])
                mem_user.change(fn=handle_get_prefs, inputs=[mem_user], outputs=[mem_table])

    return demo


def launch_ui():
    demo = build_app()
    demo.launch(server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    launch_ui()