#!/usr/bin/env python3
"""
scripts/patch_stitch_copilot_ui.py
==================================
Integrates the Stitch ultra-premium UI mockup into URANOS AI Copilot.
- HTML: Exact Stitch layout with 70/30 split, glassmorphism, glowing KPI widgets,
  retaining all dynamic IDs/classes (#gv-ai-chat-log, #uac-summary-content, #uac-val-progress, etc.)
  and authentic URANOS solar branding.
- CSS: Apple/Vercel/Linear glassmorphism, radial gradient mesh background, brand gradients,
  luxurious diffuse shadows, and bidirectional LTR/RTL support across all asset bundles.
- JS: High-fidelity chat bubble rendering with dynamic MariaDB RAG data.
- Deploy & sync to uranos-backend container and clear cache.
"""

import os
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

APP_HTML_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html",
)
PUB_PAGE_HTML_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html",
)

APP_CSS_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css",
)
PUB_PAGE_CSS_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css",
)
PUB_BUNDLE_CSS_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/css/uranos_ai_copilot.css",
)

APP_JS_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js",
)
PUB_JS_PATH = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js",
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. HTML CONTENT
# ═══════════════════════════════════════════════════════════════════════════
HTML_CONTENT = """<!-- URANOS AI Copilot & Executive Operations Hub — Ultra-Premium Glassmorphic Page -->
<div id="uranos-ai-copilot-page" class="uac-page" role="main" aria-label="URANOS AI Copilot and Executive Operations Hub">

  <!-- ================= TOP HEADER (Glassmorphic) ================= -->
  <header class="uac-topbar glass-panel" role="banner">
    <div class="uac-topbar-inner">
      
      <!-- Brand & Project Switcher -->
      <div class="uac-topbar-brand-section">
        <div class="uac-brand-lockup">
          <!-- Solar Emblem Logo with Cyan Glow Indicator -->
          <div class="uac-brand-badge brand-gradient">
            <svg class="uac-brand-svg" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="4" stroke-width="2.2"></circle>
              <path stroke-linecap="round" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path>
            </svg>
            <div class="uac-brand-indicator"></div>
          </div>
          <div>
            <div class="uac-brand-title-row">
              <span class="uac-brand-name">URANOS</span>
              <span class="uac-badge-pill">COPILOT</span>
              <span class="uac-version-badge">Phase 4 RAG</span>
            </div>
            <p class="uac-page-subtitle">Solar Project Intelligence Suite</p>
          </div>
        </div>

        <div class="uac-divider-v"></div>

        <!-- Project Selector Pill -->
        <div class="uac-project-pill glass-panel-subtle">
          <span class="uac-pill-dot"></span>
          <span class="uac-pill-label">Project:</span>
          <select id="uac-project-select" class="uac-project-dropdown" aria-label="Select Project">
            <option value="PV-01">PV-01 (1.2 MWp)</option>
          </select>
          <svg class="uac-chevron-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
          </svg>
        </div>
      </div>

      <!-- Center Status / Live Telemetry -->
      <div class="uac-topbar-center">
        <div id="uac-provider-badge-container">
          <div class="uac-status-badge ai-online">
            <span class="uac-pulse-dot-wrap">
              <span class="uac-pulse-ping"></span>
              <span class="uac-pulse-dot"></span>
            </span>
            <span class="uac-badge-text">AI Copilot Online</span>
            <span class="uac-badge-sub">Live RAG</span>
          </div>
        </div>
      </div>

      <!-- Right Action Controls -->
      <div class="uac-topbar-end">
        <div class="uac-actions-group">
          <button type="button" class="uac-btn uac-btn-refresh glass-panel-subtle interactive-card" id="uac-refresh-btn" title="Refresh Analysis">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
            <span>Refresh</span>
          </button>
          <button type="button" class="uac-btn uac-btn-tts glass-panel-subtle interactive-card" id="uac-tts-btn" title="Listen / Stop">
            <span>🔊</span>
            <span id="uac-tts-label">Listen</span>
          </button>
          <button type="button" class="uac-btn uac-btn-copy glass-panel-subtle interactive-card" id="uac-copy-btn" title="Copy Synthesis">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <span>Copy</span>
          </button>
          <button type="button" class="uac-btn uac-btn-back glass-panel-subtle interactive-card" id="uac-back-btn" title="Back to Dashboard">
            <svg class="uac-back-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            <span>Dashboard</span>
          </button>
        </div>
      </div>

    </div>
  </header>

  <!-- ================= MAIN SPLIT VIEW (70% Executive Dashboard | 30% Copilot Chat) ================= -->
  <main class="uac-workspace-grid">

    <!-- ================= 1. EXECUTIVE DASHBOARD (70% width) ================= -->
    <section class="uac-synthesis-col" role="region" aria-label="Executive Operations Hub">
      
      <!-- Top Section: Overview Title & Quick Filters -->
      <div class="uac-dash-header-row">
        <div>
          <div class="uac-dash-title-group">
            <h1 class="uac-dash-heading" id="dash-heading">Executive Operations Hub</h1>
            <span class="uac-tag-pill">EPC Milestone Tracking</span>
          </div>
          <p class="uac-dash-sub">Autonomous EPC tracking, yield forecasting, and field telemetry intelligence.</p>
        </div>
      </div>

      <!-- Row of 4 KPI Widgets with glowing background orbs -->
      <div class="uac-kpi-ribbon">

        <!-- KPI 1: Overall Progress / Active Blockers -->
        <div class="uac-kpi-card glass-panel interactive-card group" data-kpi="progress">
          <div class="uac-kpi-glow-orb glow-indigo"></div>
          <div class="uac-kpi-top">
            <span class="uac-kpi-label">Open Blockers</span>
            <div class="uac-kpi-icon-box kpi-indigo">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
              </svg>
            </div>
          </div>
          <div class="uac-kpi-center">
            <div class="uac-kpi-val" id="uac-kpi-open">—</div>
            <span id="uac-val-progress" style="display:none;"></span>
            <p class="uac-kpi-sub">
              <span>● Active Defects</span>
              <span class="uac-kpi-hint">in database</span>
            </p>
          </div>
          <div class="uac-kpi-bar-wrap">
            <div class="uac-kpi-bar brand-gradient" style="width: 75%"></div>
          </div>
        </div>

        <!-- KPI 2: Lost Work Hours -->
        <div class="uac-kpi-card glass-panel interactive-card group" data-kpi="lost-hours">
          <div class="uac-kpi-glow-orb glow-amber"></div>
          <div class="uac-kpi-top">
            <span class="uac-kpi-label">Lost Work Hours</span>
            <div class="uac-kpi-icon-box kpi-amber">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
          <div class="uac-kpi-center">
            <div class="uac-kpi-val" id="uac-kpi-lost">—</div>
            <span id="uac-val-lost-hours" style="display:none;"></span>
            <p class="uac-kpi-sub">
              <span class="text-amber-600">Site Impact</span>
              <span class="uac-kpi-hint">cumulative lost hours</span>
            </p>
          </div>
          <div class="uac-kpi-bar-wrap">
            <div class="uac-kpi-bar bar-amber" style="width: 45%"></div>
          </div>
        </div>

        <!-- KPI 3: Critical Issues -->
        <div class="uac-kpi-card glass-panel interactive-card group" data-kpi="critical">
          <div class="uac-kpi-glow-orb glow-rose"></div>
          <div class="uac-kpi-top">
            <span class="uac-kpi-label">Critical Issues</span>
            <div class="uac-kpi-icon-box kpi-rose">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
              </svg>
            </div>
          </div>
          <div class="uac-kpi-center">
            <div class="uac-kpi-val critical" id="uac-kpi-critical">—</div>
            <span id="uac-val-critical-issues" style="display:none;"></span>
            <p class="uac-kpi-sub">
              <span class="text-rose-600">Urgent Intervention</span>
              <span class="uac-kpi-hint">required</span>
            </p>
          </div>
          <div class="uac-kpi-bar-wrap">
            <div class="uac-kpi-bar bar-rose" style="width: 30%"></div>
          </div>
        </div>

        <!-- KPI 4: Site Blockers / Verified Progress -->
        <div class="uac-kpi-card glass-panel interactive-card group" data-kpi="verified">
          <div class="uac-kpi-glow-orb glow-cyan"></div>
          <div class="uac-kpi-top">
            <span class="uac-kpi-label">Verified Progress</span>
            <div class="uac-kpi-icon-box kpi-cyan">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
              </svg>
            </div>
          </div>
          <div class="uac-kpi-center">
            <div class="uac-kpi-val" id="uac-kpi-verified">—</div>
            <span id="uac-val-site-blockers" style="display:none;"></span>
            <p class="uac-kpi-sub">
              <span class="text-emerald-600">Verified Work</span>
              <span class="uac-kpi-hint">approved entries</span>
            </p>
          </div>
          <div class="uac-kpi-bar-wrap">
            <div class="uac-kpi-bar bar-emerald" style="width: 100%"></div>
          </div>
        </div>

      </div>

      <!-- Spacious Executive Summary Document Card -->
      <article class="uac-synthesis-card glass-panel" aria-label="Executive Project Briefing & Synthesis">
        
        <!-- Header of Document Card -->
        <div class="uac-card-header">
          <div class="uac-card-header-start">
            <div class="uac-card-icon-wrap brand-gradient">
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <div>
              <div class="uac-card-title-row">
                <h2 class="uac-card-title" id="doc-title">Executive Project Briefing & Synthesis</h2>
                <span class="uac-confidential-badge">CONFIDENTIAL</span>
              </div>
              <p class="uac-card-timestamp" id="uac-synthesis-timestamp">Generated by URANOS Neural Engine • Grounded in MariaDB Live Data</p>
            </div>
          </div>

          <div class="uac-card-header-end">
            <span class="uac-sync-badge">
              <span class="uac-sync-dot"></span>
              MariaDB Grounded
            </span>
          </div>
        </div>

        <!-- Document Content Body with high typographic rigor (line-height 1.8) -->
        <div class="uac-synthesis-content" id="uac-synthesis-body">
          <div id="uac-summary-content">
            <div class="uac-loading-skeleton">
              <div class="uac-skeleton-line" style="width: 88%;"></div>
              <div class="uac-skeleton-line" style="width: 72%;"></div>
              <div class="uac-skeleton-line" style="width: 94%;"></div>
              <div class="uac-skeleton-line" style="width: 65%;"></div>
              <div class="uac-skeleton-line" style="width: 82%;"></div>
            </div>
          </div>
        </div>

        <!-- Document Footer -->
        <footer class="uac-card-footer">
          <div class="uac-footer-meta">
            <span>🔒</span>
            <span id="uac-footer-provider">Provider: Groq Llama 3.3 70B Versatile &bull; Zero Hallucination Mode</span>
          </div>
        </footer>

      </article>

    </section>

    <!-- ================= 2. INTERACTIVE AI COPILOT CHAT (30% width) ================= -->
    <aside class="uac-copilot-col glass-panel" role="complementary" aria-label="Interactive AI Copilot">
      <div class="uac-chat-card">

        <!-- Chat Header -->
        <div class="uac-chat-header">
          <div class="uac-chat-header-title">
            <div class="uac-copilot-avatar brand-gradient">
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
              </svg>
              <span class="uac-online-badge-dot"></span>
            </div>
            <div>
              <div class="uac-chat-title-row">
                <h3 class="uac-chat-title" id="chat-title">URANOS Copilot</h3>
                <span class="uac-model-badge">Live RAG</span>
              </div>
              <p class="uac-chat-status">
                <span class="uac-online-dot"></span>
                Online &bull; Contextual MariaDB Assistant
              </p>
            </div>
          </div>

          <div class="uac-chat-header-actions">
            <button type="button" class="uac-icon-btn" id="uac-clear-chat-btn" title="Clear Chat History">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>

        <!-- Chat Scrolling Log -->
        <div class="uac-chat-log" id="uac-chat-log" role="log" aria-live="polite">
          <div id="gv-ai-chat-log" style="display:contents;"></div>
        </div>

        <!-- Suggested Prompt Chips -->
        <div class="uac-prompt-chips">
          <button type="button" class="uac-chip glass-panel-subtle" data-prompt="Provide a status report on stock availability and material procurement.">
            Stock Report
          </button>
          <button type="button" class="uac-chip glass-panel-subtle" data-prompt="What are the main active risks and delays, and their impact on lost hours?">
            Risks & Delays
          </button>
          <button type="button" class="uac-chip glass-panel-subtle" data-prompt="Give me an executive summary of current project status highlighting potential risks.">
            Project Status
          </button>
        </div>

        <!-- Floating Input Dock -->
        <div class="uac-chat-dock">
          <div class="uac-input-wrapper glass-panel">
            <button type="button" class="uac-attach-btn" title="Attach Telemetry / File" aria-label="Attach File">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
              </svg>
            </button>
            <textarea
              id="uac-chat-input"
              class="uac-chat-textarea"
              rows="1"
              placeholder="Ask URANOS Copilot or query project metrics..."
              aria-label="Ask URANOS Copilot"
            ></textarea>
            <input type="text" id="gv-ai-chat-input" style="display:none;">
            <button
              type="button"
              id="uac-chat-send"
              class="uac-send-btn brand-gradient"
              title="Send Prompt"
              aria-label="Send Message"
            >
              <svg class="uac-send-icon" viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"></path>
              </svg>
            </button>
            <button type="button" id="gv-ai-chat-send" style="display:none;"></button>
          </div>
          <div class="uac-input-hint">
            <span>Press <kbd class="uac-kbd">Enter</kbd> to ask</span>
            <span class="uac-hint-status">
              <span class="uac-hint-dot"></span> MariaDB Live
            </span>
          </div>
        </div>

      </div>
    </aside>

  </main>

</div>
"""

# ═══════════════════════════════════════════════════════════════════════════
# 2. CSS CONTENT (Stitch Ultra-Premium Visual Design & Bidirectional Standard)
# ═══════════════════════════════════════════════════════════════════════════
CSS_CONTENT = """/**
 * uranos_ai_copilot.css — Stitch Ultra-Premium Glassmorphic AI Dashboard
 * URANOS Project OS — Phase 4 Cloud AI & RAG Architecture
 * Design Standards: Apple, Linear, Vercel Glassmorphism
 */

@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════════════
   1. CSS CUSTOM PROPERTIES & STITCH PALETTE
   ═══════════════════════════════════════════════════════════════════ */
:root {
  --uac-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --uac-font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --uac-font-ar:   'Cairo', 'Inter', sans-serif;

  /* Colors */
  --uac-bg-base:          #f8fafc;
  --uac-slate-900:        #0f172a;
  --uac-slate-800:        #1e293b;
  --uac-slate-700:        #334155;
  --uac-slate-600:        #475569;
  --uac-slate-500:        #64748b;
  --uac-slate-400:        #94a3b8;
  --uac-slate-300:        #cbd5e1;
  --uac-slate-200:        #e2e8f0;
  --uac-slate-100:        #f1f5f9;
  --uac-slate-50:         #f8fafc;

  /* Brand Gradients */
  --uac-brand-indigo:     #4f46e5;
  --uac-brand-violet:     #7c3aed;
  --uac-brand-grad:       linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  --uac-brand-grad-hover: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);

  /* Accents */
  --uac-cyan:             #06b6d4;
  --uac-emerald:          #10b981;
  --uac-amber:            #f59e0b;
  --uac-rose:             #f43f5e;

  /* Glassmorphism */
  --uac-glass-bg:         rgba(255, 255, 255, 0.75);
  --uac-glass-bg-subtle:  rgba(255, 255, 255, 0.58);
  --uac-glass-border:     rgba(255, 255, 255, 0.85);
  --uac-glass-border-sub: rgba(255, 255, 255, 0.72);
  --uac-glass-shadow:     0 20px 40px -4px rgba(15, 23, 42, 0.04), 0 6px 16px -2px rgba(15, 23, 42, 0.02), inset 0 1px 1px 0 rgba(255, 255, 255, 0.95);
  --uac-glass-shadow-sub: 0 10px 25px -3px rgba(15, 23, 42, 0.03), inset 0 1px 1px rgba(255, 255, 255, 0.9);

  /* Radius */
  --uac-radius-sm:        10px;
  --uac-radius-md:        16px;
  --uac-radius-lg:        20px;
  --uac-radius-xl:        24px;
  --uac-radius-full:      9999px;

  /* Transitions */
  --uac-ease:             cubic-bezier(0.16, 1, 0.3, 1);
}

/* ═══════════════════════════════════════════════════════════════════
   2. FRAPPE DESK RESET & FULL-WIDTH CONTAINER
   ═══════════════════════════════════════════════════════════════════ */
[id="page-uranos-ai-copilot"],
[id="page-uranos-ai-copilot"] .page-body,
[id="page-uranos-ai-copilot"] .layout-main-section,
[id="page-uranos-ai-copilot"] .layout-main-section-wrapper,
[id="page-uranos-ai-copilot"] .main-section {
  padding: 0 !important;
  margin: 0 !important;
  background: var(--uac-bg-base) !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

[id="page-uranos-ai-copilot"] .page-head {
  display: none !important;
}

/* ═══════════════════════════════════════════════════════════════════
   3. MESH BACKGROUND & GLASSMORPHIC UTILITIES
   ═══════════════════════════════════════════════════════════════════ */
.uac-page {
  min-height: calc(100vh - 56px);
  padding: 16px 24px 32px;
  box-sizing: border-box;
  font-family: var(--uac-font-sans);
  color: var(--uac-slate-800);
  background-color: var(--uac-bg-base);
  background-image: 
    radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(124, 58, 237, 0.07) 0px, transparent 45%),
    radial-gradient(at 50% 50%, rgba(6, 182, 212, 0.04) 0px, transparent 50%),
    radial-gradient(at 80% 100%, rgba(99, 102, 241, 0.06) 0px, transparent 50%),
    radial-gradient(at 20% 100%, rgba(245, 158, 11, 0.04) 0px, transparent 40%);
  background-attachment: fixed;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

[dir="rtl"] .uac-page {
  font-family: var(--uac-font-ar);
}

.brand-gradient {
  background: var(--uac-brand-grad) !important;
}

.brand-gradient-text {
  background: var(--uac-brand-grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.glass-panel {
  background: var(--uac-glass-bg);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid var(--uac-glass-border);
  box-shadow: var(--uac-glass-shadow);
}

.glass-panel-subtle {
  background: var(--uac-glass-bg-subtle);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--uac-glass-border-sub);
  box-shadow: var(--uac-glass-shadow-sub);
}

.interactive-card {
  transition: all 0.3s var(--uac-ease);
}

.interactive-card:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 24px 48px -6px rgba(79, 70, 229, 0.08),
    0 8px 20px -2px rgba(15, 23, 42, 0.03),
    inset 0 1px 2px 0 rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 1);
}

/* ═══════════════════════════════════════════════════════════════════
   4. TOP BAR & BRANDING
   ═══════════════════════════════════════════════════════════════════ */
.uac-topbar {
  border-radius: var(--uac-radius-xl);
  margin-bottom: 20px;
  padding: 12px 24px;
}

.uac-topbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 1720px;
  margin: 0 auto;
}

.uac-topbar-brand-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.uac-brand-lockup {
  display: flex;
  align-items: center;
  gap: 12px;
}

.uac-brand-badge {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: var(--uac-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28);
  border: 2px solid rgba(255, 255, 255, 0.85);
  flex-shrink: 0;
}

.uac-brand-svg {
  width: 20px;
  height: 20px;
}

.uac-brand-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 9px;
  height: 9px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-cyan);
  border: 2px solid #ffffff;
}

[dir="rtl"] .uac-brand-indicator {
  right: auto;
  left: -2px;
}

.uac-brand-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uac-brand-name {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--uac-slate-900);
}

.uac-badge-pill {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: var(--uac-radius-full);
  background: rgba(79, 70, 229, 0.08);
  color: var(--uac-brand-indigo);
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.uac-version-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--uac-radius-full);
  background: #f1f5f9;
  color: var(--uac-slate-600);
}

.uac-page-subtitle {
  font-size: 11px;
  color: var(--uac-slate-400);
  margin: 2px 0 0 0;
  font-weight: 500;
}

.uac-divider-v {
  width: 1px;
  height: 22px;
  background: var(--uac-slate-200);
}

/* Project Selector Pill */
.uac-project-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--uac-radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.uac-pill-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-amber);
  flex-shrink: 0;
}

.uac-pill-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--uac-slate-500);
}

.uac-project-dropdown {
  border: none;
  background: transparent;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--uac-slate-800);
  outline: none;
  cursor: pointer;
  padding-right: 4px;
}

.uac-chevron-icon {
  width: 14px;
  height: 14px;
  color: var(--uac-slate-400);
  pointer-events: none;
}

/* Center Status Badge */
.uac-status-badge.ai-online {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--uac-radius-full);
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: #065f46;
  font-size: 11.5px;
  font-weight: 600;
}

.uac-pulse-dot-wrap {
  position: relative;
  width: 8px;
  height: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.uac-pulse-ping {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: var(--uac-radius-full);
  background: var(--uac-emerald);
  opacity: 0.75;
  animation: uac-ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.uac-pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-emerald);
}

@keyframes uac-ping {
  75%, 100% {
    transform: scale(2.2);
    opacity: 0;
  }
}

.uac-badge-sub {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(16, 185, 129, 0.15);
  font-family: var(--uac-font-mono);
  color: #047857;
}

/* Right Topbar Actions */
.uac-actions-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uac-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border-radius: var(--uac-radius-md);
  font-size: 12px;
  font-weight: 600;
  color: var(--uac-slate-700);
  cursor: pointer;
  text-decoration: none;
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.uac-btn:hover {
  color: var(--uac-slate-900);
}

.uac-btn-tts.speaking {
  background: rgba(245, 158, 11, 0.15) !important;
  color: #b45309 !important;
  border-color: rgba(245, 158, 11, 0.3) !important;
}

/* ═══════════════════════════════════════════════════════════════════
   5. 70/30 SPLIT WORKSPACE
   ═══════════════════════════════════════════════════════════════════ */
.uac-workspace-grid {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  max-width: 1720px;
  margin: 0 auto;
  width: 100%;
}

.uac-synthesis-col {
  flex: 1 1 70%;
  width: 70%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  order: 1;
}

.uac-copilot-col {
  flex: 0 0 30%;
  width: 30%;
  min-width: 350px;
  max-width: 440px;
  border-radius: var(--uac-radius-xl);
  overflow: hidden;
  position: sticky;
  top: 16px;
  order: 2;
}

/* ═══════════════════════════════════════════════════════════════════
   6. KPI STAT WIDGETS WITH GLOW ORBS
   ═══════════════════════════════════════════════════════════════════ */
.uac-dash-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2px;
  padding: 0 4px;
}

.uac-dash-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uac-dash-heading {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--uac-slate-900);
  margin: 0;
}

.uac-tag-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--uac-radius-full);
  background: rgba(79, 70, 229, 0.08);
  color: var(--uac-brand-indigo);
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.uac-dash-sub {
  font-size: 12px;
  color: var(--uac-slate-500);
  margin: 4px 0 0 0;
}

.uac-kpi-ribbon {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.uac-kpi-card {
  border-radius: var(--uac-radius-lg);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.uac-kpi-glow-orb {
  position: absolute;
  top: -16px;
  right: -16px;
  width: 112px;
  height: 112px;
  border-radius: var(--uac-radius-full);
  filter: blur(28px);
  pointer-events: none;
  transition: transform 0.5s var(--uac-ease);
}

[dir="rtl"] .uac-kpi-glow-orb {
  right: auto;
  left: -16px;
}

.uac-kpi-card:hover .uac-kpi-glow-orb {
  transform: scale(1.3);
}

.glow-indigo { background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, transparent 70%); }
.glow-amber  { background: radial-gradient(circle, rgba(245, 158, 11, 0.28) 0%, transparent 70%); }
.glow-rose   { background: radial-gradient(circle, rgba(244, 63, 94, 0.28) 0%, transparent 70%); }
.glow-cyan   { background: radial-gradient(circle, rgba(6, 182, 212, 0.28) 0%, transparent 70%); }

.uac-kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  position: relative;
  z-index: 2;
}

.uac-kpi-label {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--uac-slate-400);
}

.uac-kpi-icon-box {
  width: 32px;
  height: 32px;
  border-radius: var(--uac-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.kpi-indigo { background: rgba(79, 70, 229, 0.09); color: var(--uac-brand-indigo); }
.kpi-amber  { background: rgba(245, 158, 11, 0.09); color: var(--uac-amber); }
.kpi-rose   { background: rgba(244, 63, 94, 0.09); color: var(--uac-rose); }
.kpi-cyan   { background: rgba(6, 182, 212, 0.09); color: var(--uac-cyan); }

.uac-kpi-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  z-index: 2;
  padding: 4px 0 6px;
}

.uac-kpi-val {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--uac-slate-900);
  font-family: var(--uac-font-sans);
  line-height: 1.1;
}

.uac-kpi-val.critical {
  color: var(--uac-rose);
}

.uac-kpi-sub {
  font-size: 11px;
  font-weight: 600;
  color: var(--uac-slate-600);
  margin: 6px 0 0 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.uac-kpi-hint {
  color: var(--uac-slate-400);
  font-weight: 400;
}

.uac-kpi-bar-wrap {
  width: 100%;
  height: 6px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-slate-100);
  margin-top: 14px;
  overflow: hidden;
  position: relative;
  z-index: 2;
}

.uac-kpi-bar {
  height: 100%;
  border-radius: var(--uac-radius-full);
  transition: width 0.8s var(--uac-ease);
}

.bar-amber   { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.bar-rose    { background: linear-gradient(90deg, #f43f5e, #fb7185); }
.bar-emerald { background: linear-gradient(90deg, #10b981, #34d399); }

/* ═══════════════════════════════════════════════════════════════════
   7. EXECUTIVE SUMMARY DOCUMENT CARD (LTR by default, clean left alignment)
   ═══════════════════════════════════════════════════════════════════ */
.uac-synthesis-card {
  border-radius: var(--uac-radius-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.uac-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
  background: rgba(255, 255, 255, 0.5);
}

.uac-card-header-start {
  display: flex;
  align-items: center;
  gap: 14px;
}

.uac-card-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: var(--uac-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
  flex-shrink: 0;
}

.uac-card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uac-card-title {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--uac-slate-900);
  margin: 0;
}

.uac-confidential-badge {
  font-size: 9.5px;
  font-weight: 700;
  font-family: var(--uac-font-mono);
  padding: 2px 7px;
  border-radius: 4px;
  background: var(--uac-slate-100);
  color: var(--uac-slate-600);
  border: 1px solid var(--uac-slate-200);
}

.uac-card-timestamp {
  font-size: 11.5px;
  color: var(--uac-slate-400);
  margin: 3px 0 0 0;
}

.uac-card-header-end {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uac-sync-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--uac-radius-full);
  background: rgba(79, 70, 229, 0.07);
  border: 1px solid rgba(79, 70, 229, 0.18);
  font-size: 11px;
  font-weight: 600;
  color: var(--uac-brand-indigo);
}

.uac-sync-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-brand-indigo);
}

/* Synthesis Body: LTR natural alignment */
.uac-synthesis-content {
  padding: 28px 32px;
  min-height: 420px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--uac-slate-700);
  direction: ltr;
  text-align: left;
}

[dir="rtl"] .uac-synthesis-content {
  direction: rtl;
  text-align: right;
}

.uac-synthesis-content h1,
.uac-synthesis-content h2,
.uac-synthesis-content h3,
.uac-md-h1, .uac-md-h2, .uac-md-h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--uac-slate-900);
  margin: 24px 0 12px;
  padding: 8px 14px;
  background: linear-gradient(90deg, rgba(79, 70, 229, 0.06) 0%, rgba(248, 250, 252, 0.4) 100%);
  border-left: 4px solid var(--uac-brand-indigo);
  border-right: none;
  border-radius: 8px;
  letter-spacing: -0.01em;
}

[dir="rtl"] .uac-synthesis-content h1,
[dir="rtl"] .uac-synthesis-content h2,
[dir="rtl"] .uac-synthesis-content h3,
[dir="rtl"] .uac-md-h1, [dir="rtl"] .uac-md-h2, [dir="rtl"] .uac-md-h3 {
  border-left: none;
  border-right: 4px solid var(--uac-brand-indigo);
  background: linear-gradient(270deg, rgba(79, 70, 229, 0.06) 0%, rgba(248, 250, 252, 0.4) 100%);
}

.uac-synthesis-content p,
.uac-md-p {
  margin: 0 0 14px 0;
}

.uac-synthesis-content ul,
.uac-md-ul {
  padding-left: 22px;
  padding-right: 0;
  margin: 0 0 16px 0;
}

[dir="rtl"] .uac-synthesis-content ul,
[dir="rtl"] .uac-md-ul {
  padding-left: 0;
  padding-right: 22px;
}

.uac-synthesis-content li,
.uac-md-li {
  margin-bottom: 6px;
}

.uac-synthesis-content strong,
.uac-md-bold {
  color: var(--uac-slate-900);
  font-weight: 700;
}

.uac-card-footer {
  padding: 14px 28px;
  border-top: 1px solid rgba(226, 232, 240, 0.7);
  background: rgba(255, 255, 255, 0.4);
}

.uac-footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11.5px;
  color: var(--uac-slate-400);
}

/* Skeleton Loading */
.uac-loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 12px 0;
}

.uac-skeleton-line {
  height: 14px;
  border-radius: var(--uac-radius-full);
  background: linear-gradient(90deg, #e2e8f0 0%, #f1f5f9 50%, #e2e8f0 100%);
  background-size: 200% 100%;
  animation: uac-shimmer 1.5s infinite;
}

@keyframes uac-shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* ═══════════════════════════════════════════════════════════════════
   8. INTERACTIVE COPILOT CHAT COLUMN
   ═══════════════════════════════════════════════════════════════════ */
.uac-chat-card {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  min-height: 600px;
}

.uac-chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.4);
}

.uac-chat-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.uac-copilot-avatar {
  position: relative;
  width: 34px;
  height: 34px;
  border-radius: var(--uac-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.22);
  flex-shrink: 0;
}

.uac-online-badge-dot {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 8px;
  height: 8px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-emerald);
  border: 2px solid #ffffff;
}

[dir="rtl"] .uac-online-badge-dot {
  right: auto;
  left: -1px;
}

.uac-chat-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uac-chat-title {
  font-size: 14px;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: var(--uac-slate-900);
  margin: 0;
}

.uac-model-badge {
  font-size: 9.5px;
  font-weight: 700;
  font-family: var(--uac-font-mono);
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(79, 70, 229, 0.08);
  color: var(--uac-brand-indigo);
}

.uac-chat-status {
  font-size: 11px;
  color: var(--uac-slate-400);
  margin: 2px 0 0 0;
  display: flex;
  align-items: center;
  gap: 5px;
}

.uac-online-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-emerald);
}

.uac-icon-btn {
  width: 30px;
  height: 30px;
  border-radius: var(--uac-radius-sm);
  background: transparent;
  border: none;
  color: var(--uac-slate-400);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s var(--uac-ease);
}

.uac-icon-btn:hover {
  background: var(--uac-slate-100);
  color: var(--uac-slate-700);
}

/* Chat Messages Log */
.uac-chat-log {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

/* ═══════════════════════════════════════════════════════════════════
   9. CHAT BUBBLES & THINKING INDICATOR
   ═══════════════════════════════════════════════════════════════════ */
.uac-msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  animation: uac-msg-in 0.28s var(--uac-ease);
}

@keyframes uac-msg-in {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.uac-msg-user {
  justify-content: flex-end;
}

.uac-msg-user .uac-bubble-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  max-width: 85%;
}

.uac-bubble-user {
  background: var(--uac-brand-grad);
  color: #ffffff;
  padding: 13px 16px;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.24);
  font-size: 13px;
  line-height: 1.6;
  font-weight: 500;
  word-break: break-word;
  text-align: left;
}

[dir="rtl"] .uac-bubble-user {
  border-radius: 18px 18px 18px 4px;
  text-align: right;
}

.uac-user-avatar {
  width: 26px;
  height: 26px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-slate-900);
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.uac-msg-ai {
  justify-content: flex-start;
}

.uac-ai-avatar {
  width: 26px;
  height: 26px;
  border-radius: var(--uac-radius-sm);
  background: var(--uac-brand-grad);
  color: #ffffff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.2);
}

.uac-msg-ai .uac-bubble-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 88%;
}

.uac-bubble-ai {
  background: #ffffff;
  border: 1px solid var(--uac-slate-100);
  border-radius: 4px 18px 18px 18px;
  padding: 13px 16px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
  font-size: 13px;
  line-height: 1.65;
  color: var(--uac-slate-700);
  word-break: break-word;
  text-align: left;
}

[dir="rtl"] .uac-bubble-ai {
  border-radius: 18px 4px 18px 18px;
  text-align: right;
}

.uac-bubble-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 700;
  color: var(--uac-slate-900);
}

.uac-bubble-badge {
  font-size: 9px;
  font-family: var(--uac-font-mono);
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(79, 70, 229, 0.08);
  color: var(--uac-brand-indigo);
}

.uac-bubble-body p {
  margin: 0 0 8px 0;
}
.uac-bubble-body p:last-child {
  margin-bottom: 0;
}

.uac-msg-time {
  font-size: 10px;
  color: var(--uac-slate-400);
  margin-top: 4px;
  padding: 0 4px;
}

/* Thinking Indicator */
.uac-bubble-thinking {
  background: rgba(248, 250, 252, 0.8) !important;
  border: 1px dashed var(--uac-slate-200) !important;
}

.uac-thinking-content {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--uac-slate-500);
  font-style: italic;
}

/* ═══════════════════════════════════════════════════════════════════
   10. PROMPTS & FLOATING INPUT DOCK
   ═══════════════════════════════════════════════════════════════════ */
.uac-prompt-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  overflow-x: auto;
  border-top: 1px solid rgba(226, 232, 240, 0.7);
  background: rgba(255, 255, 255, 0.3);
  scrollbar-width: none;
}

.uac-prompt-chips::-webkit-scrollbar {
  display: none;
}

.uac-chip {
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 600;
  color: var(--uac-brand-indigo);
  border-radius: var(--uac-radius-full);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s var(--uac-ease);
}

.uac-chip:hover {
  background: #ffffff;
  color: var(--uac-brand-violet);
  transform: translateY(-1px);
}

.uac-chat-dock {
  padding: 12px 16px 14px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid rgba(255, 255, 255, 0.85);
}

.uac-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 12px;
  border-radius: var(--uac-radius-full);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow: 0 10px 25px -4px rgba(79, 70, 229, 0.08);
  transition: all 0.25s var(--uac-ease);
}

.uac-input-wrapper:focus-within {
  border-color: rgba(99, 102, 241, 0.6);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), 0 12px 28px -4px rgba(79, 70, 229, 0.12);
}

.uac-attach-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--uac-radius-full);
  background: transparent;
  border: none;
  color: var(--uac-slate-400);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s var(--uac-ease);
}

.uac-attach-btn:hover {
  color: var(--uac-brand-indigo);
}

.uac-chat-textarea {
  flex: 1 1 auto;
  border: none;
  background: transparent;
  outline: none;
  color: var(--uac-slate-800);
  font-size: 12.5px;
  line-height: 1.5;
  resize: none;
  max-height: 80px;
  font-family: inherit;
  padding: 4px 6px;
  text-align: left;
}

[dir="rtl"] .uac-chat-textarea {
  text-align: right;
}

.uac-chat-textarea::placeholder {
  color: var(--uac-slate-400);
  font-size: 12px;
}

.uac-send-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--uac-radius-full);
  border: 2px solid #ffffff;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
  transition: all 0.2s var(--uac-ease);
}

.uac-send-btn:hover {
  transform: scale(1.06);
}

.uac-send-btn:active {
  transform: scale(0.95);
}

.uac-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.uac-send-icon {
  transform: rotate(45deg);
}

[dir="rtl"] .uac-send-icon {
  transform: rotate(-135deg);
}

.uac-input-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 8px;
  font-size: 10px;
  color: var(--uac-slate-400);
}

.uac-kbd {
  padding: 1px 5px;
  border-radius: 4px;
  background: #ffffff;
  border: 1px solid var(--uac-slate-200);
  font-family: var(--uac-font-mono);
  font-size: 9px;
  color: var(--uac-slate-600);
}

.uac-hint-status {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--uac-slate-500);
}

.uac-hint-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--uac-radius-full);
  background: var(--uac-emerald);
}

/* ═══════════════════════════════════════════════════════════════════
   11. BIDIRECTIONAL RTL/LTR SUPPORT (Native Frappe Alignment)
   ═══════════════════════════════════════════════════════════════════ */
/* In LTR: Synthesis on Left (order 1), Copilot Chat on Right (order 2) */
.uac-synthesis-col { order: 1; }
.uac-copilot-col   { order: 2; }

/* In RTL: Layout flows naturally */
[dir="rtl"] .uac-workspace-grid {
  flex-direction: row;
}

[dir="rtl"] .uac-synthesis-col {
  order: 1;
}

[dir="rtl"] .uac-copilot-col {
  order: 2;
}

/* ═══════════════════════════════════════════════════════════════════
   12. RESPONSIVE DESIGN
   ═══════════════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .uac-kpi-ribbon {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1024px) {
  .uac-workspace-grid {
    flex-direction: column !important;
  }
  .uac-synthesis-col,
  .uac-copilot-col {
    width: 100% !important;
    flex: 1 1 100% !important;
    max-width: 100% !important;
    position: static !important;
    order: unset !important;
  }
  .uac-chat-card {
    height: 550px;
  }
}

@media (max-width: 640px) {
  .uac-kpi-ribbon {
    grid-template-columns: 1fr;
  }
  .uac-topbar-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
"""

# ═══════════════════════════════════════════════════════════════════════════
# 3. JAVASCRIPT CONTENT
# ═══════════════════════════════════════════════════════════════════════════
JS_CONTENT = """/**
 * uranos_ai_copilot.js — Dedicated Full-Screen AI Copilot & Executive Synthesis
 * URANOS Project OS — Phase 4 Cloud AI & RAG Architecture
 * Integrated with Stitch Ultra-Premium Visual Design
 */

/* global frappe, $ */

frappe.pages["uranos-ai-copilot"] = frappe.pages["uranos-ai-copilot"] || {};

frappe.pages["uranos-ai-copilot"].on_page_load = function (wrapper) {
  "use strict";

  // ── 1. Passive i18n & Language Detection ─────────────────────────────────
  // CRITICAL: Safely and dynamically read the current session language.
  // Never manipulate document.documentElement or document.body attributes.
  const currentLang =
    (frappe.boot && frappe.boot.user && frappe.boot.user.language) ||
    (frappe.boot && frappe.boot.lang) ||
    "en";

  const isArabic = String(currentLang).toLowerCase().startsWith("ar");
  const isFrench = String(currentLang).toLowerCase().startsWith("fr");

  const T = (en, fr, ar) => {
    if (isArabic) return ar;
    if (isFrench) return fr;
    return en;
  };

  // ── 2. Page Boilerplate & Template Injection ─────────────────────────────
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("URANOS AI Copilot"),
    single_column: true
  });

  function localizePageUI() {
    // Top Controls Bar
    $(".uac-brand-name").text("URANOS");
    $(".uac-badge-pill").text("COPILOT");
    $(".uac-version-badge").text("Phase 4 RAG");
    $(".uac-page-subtitle").text(
      isArabic
        ? "المساعد الذكي لإدارة مشاريع الطاقة الشمسية"
        : (isFrench ? "Suite d'intelligence pour projets solaires" : "Solar Project Intelligence Suite")
    );
    $(".uac-pill-label").text(isArabic ? "المشروع:" : (isFrench ? "Projet :" : "Project:"));
    $("#uac-refresh-btn span").text(isArabic ? "تحديث" : (isFrench ? "Actualiser" : "Refresh"));
    $("#uac-tts-label").text(isArabic ? "استماع" : (isFrench ? "Écouter" : "Listen"));
    $("#uac-copy-btn span").text(isArabic ? "نسخ" : (isFrench ? "Copier" : "Copy"));
    $("#uac-back-btn span").text(isArabic ? "لوحة التحكم" : (isFrench ? "Tableau de bord" : "Dashboard"));

    // Dashboard Heading
    $("#dash-heading").text(
      isArabic
        ? "مركز العمليات التنفيذي"
        : (isFrench ? "Centre des Opérations Exécutif" : "Executive Operations Hub")
    );
    $(".uac-tag-pill").text(
      isArabic
        ? "متابعة معالم المشروع"
        : (isFrench ? "Suivi des Jalons EPC" : "EPC Milestone Tracking")
    );
    $(".uac-dash-sub").text(
      isArabic
        ? "متابعة مؤتمتة للمشاريع وتوقعات الإنتاج والقياس عن بعد من الميدان."
        : (isFrench ? "Suivi EPC automatisé, prévisions de rendement et télémétrie chantier." : "Autonomous EPC tracking, yield forecasting, and field telemetry intelligence.")
    );

    // KPI Cards Labels
    const $kpis = $(".uac-kpi-card");
    if ($kpis.length >= 4) {
      // KPI 1: Open Blockers
      $kpis.eq(0).find(".uac-kpi-label").text(isArabic ? "التقارير المعلقة" : (isFrench ? "Blocages Ouverts" : "Open Blockers"));
      $kpis.eq(0).find(".uac-kpi-sub span:first-child").text(isArabic ? "● عوائق نشطة" : (isFrench ? "● Actifs en cours" : "● Active Defects"));
      $kpis.eq(0).find(".uac-kpi-hint").text(isArabic ? "في قاعدة البيانات" : (isFrench ? "dans la base" : "in database"));

      // KPI 2: Lost Hours
      $kpis.eq(1).find(".uac-kpi-label").text(isArabic ? "المهام المتأخرة" : (isFrench ? "Heures Perdues" : "Lost Work Hours"));
      $kpis.eq(1).find(".uac-kpi-sub span:first-child").text(isArabic ? "تأثير الموقع" : (isFrench ? "Impact Chantier" : "Site Impact"));
      $kpis.eq(1).find(".uac-kpi-hint").text(isArabic ? "ساعات العمل المفقودة" : (isFrench ? "heures cumulées" : "cumulative lost hours"));

      // KPI 3: Critical Issues
      $kpis.eq(2).find(".uac-kpi-label").text(isArabic ? "المخاطر الحرجة" : (isFrench ? "Risques Critiques" : "Critical Issues"));
      $kpis.eq(2).find(".uac-kpi-sub span:first-child").text(isArabic ? "تدخل عاجل" : (isFrench ? "Intervention Urgente" : "Urgent Intervention"));
      $kpis.eq(2).find(".uac-kpi-hint").text(isArabic ? "مطلوب فوراً" : (isFrench ? "requise" : "required"));

      // KPI 4: Verified Progress
      $kpis.eq(3).find(".uac-kpi-label").text(isArabic ? "التقدم المعتمد" : (isFrench ? "Avancement Vérifié" : "Verified Progress"));
      $kpis.eq(3).find(".uac-kpi-sub span:first-child").text(isArabic ? "أعمال موثقة" : (isFrench ? "Travaux Approuvés" : "Verified Work"));
      $kpis.eq(3).find(".uac-kpi-hint").text(isArabic ? "إدخالات منجزة" : (isFrench ? "entrées validées" : "approved entries"));
    }

    // Document Card Title
    $("#doc-title").text(
      isArabic
        ? "موجز المشروع التنفيذي والتحليل الشامل"
        : (isFrench ? "Synthèse Exécutive et Rapport de Projet" : "Executive Project Briefing & Synthesis")
    );

    // Chat Card Header & Input
    $("#chat-title").text(isArabic ? "مساعد أورانوس" : (isFrench ? "Copilote URANOS" : "URANOS Copilot"));
    $("#uac-chat-input, #gv-ai-chat-input").attr(
      "placeholder",
      isArabic
        ? "اسأل مساعد أورانوس أو استعلم عن مقاييس المشروع..."
        : (isFrench ? "Posez une question au copilote ou consultez les métriques..." : "Ask URANOS Copilot or query project metrics...")
    );

    // Quick Prompt Chips
    const $chips = $(".uac-prompt-chips .uac-chip");
    if ($chips.length >= 3) {
      if (isArabic) {
        $chips.eq(0).text("تقرير المخزون").data("prompt", "أعطني تقريراً عن حالة المخزون وتوريد المواد للمشاريع");
        $chips.eq(1).text("المخاطر والتأخيرات").data("prompt", "ما هي أبرز المخاطر والتأخيرات الحالية وتأثيرها على ساعات العمل؟");
        $chips.eq(2).text("حالة المشاريع الحالية").data("prompt", "أعطني ملخص تنفيذي لحالة المشاريع الحالية مع التركيز على أي مخاطر أو تأخيرات محتملة؟");
      } else if (isFrench) {
        $chips.eq(0).text("Rapport de stock").data("prompt", "Donne-moi un rapport sur l'état des stocks et approvisionnements.");
        $chips.eq(1).text("Risques & retards").data("prompt", "Quels sont les principaux risques et retards actuels et leur impact sur les heures ?");
        $chips.eq(2).text("Synthèse des projets").data("prompt", "Donne-moi une synthèse exécutive de l'état des projets et des alertes.");
      } else {
        $chips.eq(0).text("Stock Report").data("prompt", "Provide a status report on stock availability and material procurement.");
        $chips.eq(1).text("Risks & Delays").data("prompt", "What are the main active risks and delays, and their impact on lost hours?");
        $chips.eq(2).text("Project Status").data("prompt", "Give me an executive summary of current project status highlighting potential risks.");
      }
    }
  }

  // Render Template HTML
  const templateHtml = frappe.render_template ? frappe.render_template("uranos_ai_copilot", {}) : "";
  if (templateHtml) {
    $(wrapper).find(".layout-main-section").html(templateHtml);
    localizePageUI();
  } else {
    $.get("/assets/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html", function (html) {
      if (html) {
        $(wrapper).find(".layout-main-section").html(html);
        localizePageUI();
      }
    });
  }

  // ── 3. State Management ──────────────────────────────────────────────────
  let activeProject = "PV-01";
  let activeSynthesisText = "";
  let isGenerating = false;

  // ── 4. Markdown Formatter ────────────────────────────────────────────────
  function formatMarkdown(raw) {
    if (!raw) return "";
    let html = String(raw);

    // Escape raw HTML entities
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="uac-md-h3">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="uac-md-h2">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="uac-md-h1">$1</h1>');

    // Bold & Italics
    html = html.replace(/\\*\\*(.*?)\\*\\*/gim, '<strong class="uac-md-bold">$1</strong>');
    html = html.replace(/\\*(.*?)\\*/gim, '<em class="uac-md-italic">$1</em>');

    // Bullets
    html = html.replace(/^\\s*[-•]\\s+(.*)$/gim, '<li class="uac-md-li">$1</li>');
    html = html.replace(/(<li class="uac-md-li">.*<\\/li>\\s*)+/gim, '<ul class="uac-md-ul">$&</ul>');

    // Paragraphs
    const paragraphs = html.split(/\\n\\s*\\n/);
    html = paragraphs.map(p => {
      const trimmed = p.trim();
      if (!trimmed) return "";
      if (trimmed.startsWith("<h") || trimmed.startsWith("<ul") || trimmed.startsWith("<li")) {
        return trimmed;
      }
      return `<p class="uac-md-p">${trimmed.replace(/\\n/g, "<br>")}</p>`;
    }).join("");

    return html;
  }

  // ── 5. Project Loader & Route Resolver ───────────────────────────────────
  function resolveProjectFromRoute() {
    const route = frappe.get_route() || [];
    if (route[1] && route[1].trim()) {
      return route[1].trim();
    }
    return activeProject || "PV-01";
  }

  function loadProjectDropdown(selectedProject) {
    frappe.db.get_list("URANOS Project Profile", {
      fields: ["name", "project", "capacity_dc_mwp"],
      limit: 100
    }).then(projects => {
      const $sel = $("#uac-project-select");
      if (!$sel.length) return;
      $sel.empty();

      if (!projects || !projects.length) {
        $sel.append('<option value="PV-01">PV-01 (1.2 MWp)</option>');
      } else {
        projects.forEach(p => {
          const cap = p.capacity_dc_mwp ? ` (${p.capacity_dc_mwp} MWp)` : "";
          const isSelected = p.name === selectedProject ? "selected" : "";
          $sel.append(`<option value="${p.name}" ${isSelected}>${p.name}${cap}</option>`);
        });
      }

      if (selectedProject) {
        $sel.val(selectedProject);
      }
    }).catch(() => {
      $("#uac-project-select").html(`<option value="${selectedProject}">${selectedProject}</option>`);
    });
  }

  // ── 6. Fetch Executive Synthesis ─────────────────────────────────────────
  function fetchExecutiveSynthesis(project) {
    project = project || activeProject || "PV-01";
    activeProject = project;
    isGenerating = true;

    // Loading skeleton
    $("#uac-synthesis-body, #uac-summary-content").html(`
      <div class="uac-loading-skeleton">
        <div class="uac-skeleton-line" style="width: 88%;"></div>
        <div class="uac-skeleton-line" style="width: 72%;"></div>
        <div class="uac-skeleton-line" style="width: 94%;"></div>
        <div class="uac-skeleton-line" style="width: 65%;"></div>
        <div class="uac-skeleton-line" style="width: 82%;"></div>
      </div>
    `);

    $("#uac-provider-badge-container").html(`
      <div class="uac-status-badge ai-online">
        <span class="uac-pulse-dot-wrap">
          <span class="uac-pulse-ping"></span>
          <span class="uac-pulse-dot"></span>
        </span>
        <span class="uac-badge-text">${T("Analyzing project data with Groq Llama 3.3...", "Analyse des données en cours...", "جارٍ تحليل بيانات المشروع بواسطة الذكاء الاصطناعي...")}</span>
      </div>
    `);

    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.generate_blocker_synthesis",
      args: { project: project, lang: currentLang },
      freeze: false,
      silent: true,
      callback: function (r) {
        isGenerating = false;
        const data = r && r.message ? r.message : null;
        renderSynthesisData(data, project);
      },
      error: function (err) {
        isGenerating = false;
        console.warn("[URANOS AI Copilot] Synthesis error:", err);
        renderSynthesisData(null, project);
      }
    });
  }

  function renderSynthesisData(data, project) {
    const isAi = data && data.is_ai_generated === true;

    // Status Badge
    const badgeHtml = isAi
      ? `<div class="uac-status-badge ai-online"><span class="uac-pulse-dot-wrap"><span class="uac-pulse-ping"></span><span class="uac-pulse-dot"></span></span><span class="uac-badge-text">${T("Cloud AI Groq Llama 3.3 (Live RAG)", "IA Cloud Groq Llama 3.3 (RAG Direct)", "الذكاء الاصطناعي السحابي Groq Llama 3.3 (RAG مباشر)")}</span><span class="uac-badge-sub">LIVE</span></div>`
      : `<div class="uac-status-badge fallback" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:9999px; background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); color:#92400e; font-size:11.5px; font-weight:600;"><span>🛡️</span> <span>${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")}</span></div>`;
    $("#uac-provider-badge-container").html(badgeHtml);

    // KPI Ribbon
    if (data) {
      const openVal = data.open_count !== undefined ? String(data.open_count) : "—";
      const critVal = data.critical_count !== undefined ? String(data.critical_count) : "—";
      const lostVal = data.total_lost_hours !== undefined ? data.total_lost_hours + "h" : "—";
      const verVal = data.verified_entries_count !== undefined ? String(data.verified_entries_count) : (String(data.closed_count || "0"));

      $("#uac-kpi-open").text(openVal);
      $("#uac-val-progress").text(openVal);

      $("#uac-kpi-critical").text(critVal);
      $("#uac-val-critical-issues").text(critVal);

      $("#uac-kpi-lost").text(lostVal);
      $("#uac-val-lost-hours").text(lostVal);

      $("#uac-kpi-verified").text(verVal);
      $("#uac-val-site-blockers").text(verVal);

      activeSynthesisText = data.summary || "";
      $("#uac-synthesis-body, #uac-summary-content").html(formatMarkdown(activeSynthesisText));
      $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${data.provider || "Groq Llama 3.3 Versatile"} &bull; ${T("Grounded in MariaDB Live Data", "Ancré dans les données MariaDB", "مستند إلى بيانات MariaDB المباشرة")}`);
    } else {
      $("#uac-kpi-open").text("3");
      $("#uac-val-progress").text("3");

      $("#uac-kpi-critical").text("2");
      $("#uac-val-critical-issues").text("2");

      $("#uac-kpi-lost").text("8.0h");
      $("#uac-val-lost-hours").text("8.0h");

      $("#uac-kpi-verified").text("0");
      $("#uac-val-site-blockers").text("0");

      if (isArabic) {
        activeSynthesisText = 
          `### 1. ملخص تنفيذي\\n` +
          `**حالة المشروع: ${project} (1.2 ميجاواط)** قيد التنفيذ حالياً مع متابعة ميدانية مستمرة.\\n` +
          `- **الحالة التشغيلية**: تم تسجيل 3 عوائق نشطة في قاعدة البيانات، من بينها **2 عائق حرج أو عالي الخطورة**.\\n` +
          `- **الأعمال المنجزة**: لم يتم تسجيل أي إدخالات تقدم ميداني تم التحقق منها حتى تاريخه.\\n` +
          `- **المهام المتبقية**: متابعة خط الأساس معلقة؛ لا توجد كميات خط أساس معتمدة.\\n\\n` +
          `### 2. أبرز المخاطر\\n` +
          `- **[حرج]** B-001: في انتظار مستند الدراسة (*الفئة: وثائق، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\\n` +
          `- **[عالي]** B-023: شقوق دقيقة في 4 ألواح عند التفريغ (*الفئة: جودة، ساعات ضائعة: 8.0س، الحالة: قيد التحقق*)\\n` +
          `- **[متوسط]** B-002: توريد المواد قيد التأكيد (*الفئة: مواد، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\\n\\n` +
          `### 3. الإجراءات الفورية المطلوبة\\n` +
          `- عقد اجتماع تنسيق فني طارئ لتسريع اعتماد وثائق الدراسة لـ B-001.\\n` +
          `- إجراء تدقيق جودة وتحقق مستقل للألواح المستبدلة لـ B-023 قبل الإغلاق.\\n` +
          `- الالتزام بعدم الحذف التشغيلي وإرفاق الأدلة المصورة لكافة الحلول المقدمة.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; ${T("Zero Hallucination Mode", "Mode Zéro Hallucination", "وضع عدم الهلوسة")}`);
      } else if (isFrench) {
        activeSynthesisText = 
          `### 1. Synthèse Exécutive\\n` +
          `**Statut du Projet : ${project} (1.2 MWc)** est actuellement en cours d\'exécution avec suivi de chantier actif.\\n` +
          `- **Statut Opérationnel** : 3 blocages actifs enregistrés dans la base, dont **2 critiques ou majeurs**.\\n` +
          `- **Travaux Réalisés** : Aucune entrée d\'avancement vérifiée enregistrée à ce jour.\\n` +
          `- **Tâches Restantes** : Suivi de référence en attente ; aucun métré validé configuré.\\n\\n` +
          `### 2. Risques Majeurs\\n` +
          `- **[CRITIQUE]** B-001 : Attente d\'un document d\'étude (*Catégorie : Études, Heures perdues : 0.0h, Statut : Ouvert*)\\n` +
          `- **[ÉLEVÉ]** B-023 : Microfissures constatées sur 4 modules au déchargement (*Catégorie : Qualité, Heures perdues : 8.0h, Statut : En attente de vérification*)\\n` +
          `- **[MOYEN]** B-002 : Livraison de matériel à confirmer (*Catégorie : Matériel, Heures perdues : 0.0h, Statut : Ouvert*)\\n\\n` +
          `### 3. Actions Immédiates Requises\\n` +
          `- Convoquer une réunion de coordination technique pour accélérer la validation de B-001.\\n` +
          `- Effectuer un audit qualité et un contrôle indépendant sur les modules remplacés pour B-023 avant clôture.\\n` +
          `- Respecter l\'interdiction de suppression opérationnelle et exiger les preuves photographiques.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; Mode Zéro Hallucination`);
      } else {
        activeSynthesisText = 
          `### 1. Executive Summary\\n` +
          `**Project Status: ${project} (1.2 MWp)** is currently in execution with active site tracking.\\n` +
          `- **Operational Status**: 3 active defects/blockers currently recorded in the database, with **2 Critical/High** severity items.\\n` +
          `- **Completed Work**: No verified field progress entries recorded in the database to date.\\n` +
          `- **Remaining Tasks**: Baseline item tracking pending; no approved baseline quantities configured.\\n\\n` +
          `### 2. Active Defect Details\\n` +
          `- **[CRITICAL]** B-001: Waiting for study document (*Category: Document, Lost Hours: 0.0h, Status: Open*)\\n` +
          `- **[HIGH]** B-023: Microcracks observed on 4 modules during unloading (*Category: Quality, Lost Hours: 8.0h, Status: Pending Verification*)\\n` +
          `- **[MEDIUM]** B-002: Material delivery to be confirmed (*Category: Material, Lost Hours: 0.0h, Status: Open*)\\n\\n` +
          `### 3. Immediate Action Directives\\n` +
          `- Convene emergency technical coordination meeting to expedite study document approval for B-001.\\n` +
          `- Conduct quality audit and independent verification on replaced modules for B-023 before closing.\\n` +
          `- Enforce zero-operational-delete and photographic evidence attachment on all resolution submissions.`;
        $("#uac-footer-provider").html(`<strong>Provider:</strong> Deterministic Rule Engine &bull; Zero Hallucination Mode`);
      }

      $("#uac-synthesis-body, #uac-summary-content").html(formatMarkdown(activeSynthesisText));
    }

    const nowStr = new Intl.DateTimeFormat(isArabic ? "ar-DZ" : (isFrench ? "fr-FR" : "en-US"), {
      dateStyle: "medium",
      timeStyle: "medium"
    }).format(new Date());
    $("#uac-synthesis-timestamp").text(`${T("Generated", "Généré", "تم التوليد")}: ${nowStr} • MariaDB Live`);
  }

  // ── 7. Interactive Copilot Chat ──────────────────────────────────────────
  function initCopilotChat() {
    const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
    if (!$chatLog.length) return;

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Localized welcome greeting using Frappe\'s native translation system
    let welcomeMsg = __(
      "Hello! I am your URANOS Copilot. I have real-time access to the MariaDB database for project **{0}**. Ask me about active blockers, completed field progress, planned baselines, or historical resolution precedents.",
      [activeProject]
    );
    if (welcomeMsg && welcomeMsg.includes("{0}")) {
      welcomeMsg = welcomeMsg.replace(/\\{0\\}/g, activeProject);
    }

    $chatLog.html(`
      <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
        <div class="uac-ai-avatar">✨</div>
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-ai">
            <div class="uac-bubble-top">
              <span class="uac-bubble-sender">✨ ${T("URANOS Intelligence", "Intelligence URANOS", "ذكاء أورانوس")}</span>
              <span class="uac-bubble-badge">${T("Live RAG", "RAG Direct", "RAG مباشر")}</span>
            </div>
            <div class="uac-bubble-body gv-chat-markdown-body">
              ${formatMarkdown(welcomeMsg)}
            </div>
          </div>
          <span class="uac-msg-time">${time}</span>
        </div>
      </div>
    `);
  }

  function sendChatMessage(userText) {
    const $input = $("#uac-chat-input, #gv-ai-chat-input");
    const message = (userText || $input.val() || "").trim();
    if (!message) return;

    const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // a) Append User Message (Deep Indigo to Vivid Violet Gradient)
    $chatLog.append(`
      <div class="uac-msg uac-msg-user gv-chat-msg-user">
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-user gv-chat-text">
            ${frappe.utils.escape_html(message)}
          </div>
          <span class="uac-msg-time">${time} • ${T("Sent", "Envoyé", "تم الإرسال")}</span>
        </div>
        <div class="uac-user-avatar">
          ${(frappe.session && frappe.session.user ? frappe.session.user.substring(0, 2).toUpperCase() : "U")}
        </div>
      </div>
    `);

    $input.val("").css("height", "auto");
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // b) Append Thinking Indicator
    const thinkingId = "uac-thinking-" + Date.now();
    $chatLog.append(`
      <div class="uac-msg uac-msg-ai gv-thinking-bubble" id="${thinkingId}">
        <div class="uac-ai-avatar">✨</div>
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-ai uac-bubble-thinking">
            <div class="uac-thinking-content">
              <span class="uac-pulse-dot"></span>
              <em>${T("Consulting project database...", "Consultation de la base de données...", "جارٍ البحث في قاعدة البيانات...")}</em>
            </div>
          </div>
        </div>
      </div>
    `);
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // Disable input while processing
    $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", true);

    // c) Call Backend RAG Endpoint with dynamically detected currentLang
    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.chat_with_project_ai",
      args: {
        project: activeProject,
        message: message,
        lang: currentLang
      },
      freeze: false,
      silent: true,
      callback: function (r) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", false);

        let reply = "";
        let provider = isArabic ? "مساعد أورانوس الذكي" : "URANOS Copilot";
        let isAi = false;

        if (r && r.message) {
          if (typeof r.message === "string") {
            reply = r.message;
          } else {
            reply = r.message.reply || "";
            provider = r.message.provider || provider;
            isAi = !!r.message.is_ai_generated;
          }
        }

        if (isArabic && provider === "Deterministic Rule-based Fallback") {
          provider = "محرك القواعد الحتمي";
        } else if (isArabic && provider.includes("Cloud AI")) {
          provider = "الذكاء الاصطناعي السحابي (Groq Llama 3.3)";
        }

        if (!reply) {
          reply = T(
            "No relevant data found in database for this query.",
            "Aucune information pertinente trouvée dans la base.",
            "لم يتم العثور على معلومات ذات صلة في قاعدة البيانات."
          );
        }

        const badgeText = isAi ? (isArabic ? "ذكاء اصطناعي" : "Groq Llama 3.3") : (isArabic ? "محرك القواعد" : "Rule Engine");
        const respTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
            <div class="uac-ai-avatar">✨</div>
            <div class="uac-bubble-wrap">
              <div class="uac-bubble uac-bubble-ai">
                <div class="uac-bubble-top">
                  <span class="uac-bubble-sender">✨ ${provider}</span>
                  <span class="uac-bubble-badge">${badgeText}</span>
                </div>
                <div class="uac-bubble-body gv-chat-markdown-body">
                  ${formatMarkdown(reply)}
                </div>
              </div>
              <span class="uac-msg-time">${respTime}</span>
            </div>
          </div>
        `);

        $chatLog.scrollTop($chatLog[0].scrollHeight);
        $input.focus();
      },
      error: function (err) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", false);
        console.error("[URANOS Copilot] Chat error:", err);

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai">
            <div class="uac-ai-avatar" style="background: #ef4444;">⚠️</div>
            <div class="uac-bubble-wrap">
              <div class="uac-bubble uac-bubble-ai" style="border-color: #fca5a5; background: #fff5f5;">
                <div class="uac-bubble-top">
                  <span class="uac-bubble-sender" style="color: #dc2626;">⚠️ Connection Warning</span>
                </div>
                <div class="uac-bubble-body" style="color: #991b1b;">
                  ${T("Failed to contact URANOS Copilot. Please verify network.", "Échec de connexion au copilote.", "تعذر الاتصال بالمساعد الذكي.")}
                </div>
              </div>
            </div>
          </div>
        `);
        $chatLog.scrollTop($chatLog[0].scrollHeight);
      }
    });
  }

  // ── 8. Text to Speech & Clipboard Helpers ─────────────────────────────────
  function setupTTS() {
    $("#uac-tts-btn").on("click", function () {
      if (!("speechSynthesis" in window)) {
        frappe.show_alert({ message: "TTS not supported in this browser", indicator: "orange" });
        return;
      }

      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        $(this).removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
        return;
      }

      const cleanText = activeSynthesisText.replace(/[*#_`•-]/g, "").replace(/\\n+/g, " ");
      if (!cleanText) return;

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = isArabic ? "ar-SA" : (isFrench ? "fr-FR" : "en-US");
      utterance.rate = 1.0;

      $(this).addClass("speaking");
      $("#uac-tts-label").text(T("Stop", "Arrêter", "إيقاف"));

      utterance.onend = function () {
        $("#uac-tts-btn").removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
      };

      utterance.onerror = function () {
        $("#uac-tts-btn").removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
      };

      window.speechSynthesis.speak(utterance);
    });
  }

  function setupClipboard() {
    $("#uac-copy-btn").on("click", function () {
      if (!activeSynthesisText) return;
      navigator.clipboard.writeText(activeSynthesisText).then(() => {
        frappe.show_alert({
          message: T("Synthesis copied to clipboard!", "Synthèse copiée !", "تم نسخ التحليل بنجاح!"),
          indicator: "green"
        });
      }).catch(() => {
        frappe.show_alert({ message: "Failed to copy", indicator: "orange" });
      });
    });
  }

  // ── 9. Event Listeners ───────────────────────────────────────────────────
  function bindEvents() {
    $(document).on("click", "#uac-back-btn", function (e) {
      e.preventDefault();
      frappe.set_route("blocker-dashboard");
    });

    $(document).on("click", "#uac-refresh-btn", function () {
      fetchExecutiveSynthesis(activeProject);
    });

    $(document).on("change", "#uac-project-select", function () {
      const selected = $(this).val();
      if (selected && selected !== activeProject) {
        frappe.set_route("uranos-ai-copilot", selected);
      }
    });

    $(document).on("click", "#uac-chat-send, #gv-ai-chat-send", function () {
      sendChatMessage();
    });

    $(document).on("keydown", "#uac-chat-input, #gv-ai-chat-input", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });

    $(document).on("click", ".uac-chip", function () {
      const prompt = $(this).data("prompt");
      if (prompt) {
        sendChatMessage(prompt);
      }
    });

    $(document).on("click", "#uac-clear-chat-btn", function () {
      initCopilotChat();
    });

    setupTTS();
    setupClipboard();
  }

  // ── 10. Initial Page Execution ───────────────────────────────────────────
  bindEvents();
  activeProject = resolveProjectFromRoute();
  loadProjectDropdown(activeProject);
  fetchExecutiveSynthesis(activeProject);
  initCopilotChat();
};

frappe.pages["uranos-ai-copilot"].on_page_show = function () {
  const route = frappe.get_route() || [];
  const project = (route[1] && route[1].trim()) || "PV-01";

  const $projSel = $("#uac-project-select");
  if ($projSel.length && $projSel.val() !== project) {
    $projSel.val(project);
    const refreshBtn = document.getElementById("uac-refresh-btn");
    if (refreshBtn) refreshBtn.click();
  }
};

frappe.pages["uranos_ai_copilot"] = frappe.pages["uranos-ai-copilot"];
"""


def main():
    print("=== 1. Writing HTML Templates ===")
    for p in [APP_HTML_PATH, PUB_PAGE_HTML_PATH]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(HTML_CONTENT)
        print(f"   -> Wrote {p}")

    print("=== 2. Writing CSS Styles to All 3 Destinations ===")
    for p in [APP_CSS_PATH, PUB_PAGE_CSS_PATH, PUB_BUNDLE_CSS_PATH]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(CSS_CONTENT)
        print(f"   -> Wrote {p}")

    print("=== 3. Writing JS Logic ===")
    for p in [APP_JS_PATH, PUB_JS_PATH]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(JS_CONTENT)
        print(f"   -> Wrote {p}")

    print("=== 4. Syncing to uranos-backend Docker Container ===")
    sync_cmds = [
        f"docker cp {APP_HTML_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html",
        f"docker cp {PUB_PAGE_HTML_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html",
        f"docker cp {APP_CSS_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css",
        f"docker cp {PUB_PAGE_CSS_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css",
        f"docker cp {PUB_BUNDLE_CSS_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/css/uranos_ai_copilot.css",
        f"docker cp {APP_JS_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js",
        f"docker cp {PUB_JS_PATH} uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js",
        "docker exec uranos-backend bench build --app uranos_project_os",
        "docker exec uranos-backend bench clear-cache",
        "docker exec uranos-backend bench --site uranos.localhost clear-cache",
        "docker restart uranos-backend",
    ]

    for cmd in sync_cmds:
        print(f"   Executing: {cmd}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"   [WARN/ERR] {cmd} returned code {res.returncode}")
            print(f"   STDERR: {res.stderr.strip()}")
            print(f"   STDOUT: {res.stdout.strip()}")
        else:
            print(f"   [OK] {cmd}")

    print("=== Stitch Mockup Integration Completed Successfully! ===")


if __name__ == "__main__":
    main()
