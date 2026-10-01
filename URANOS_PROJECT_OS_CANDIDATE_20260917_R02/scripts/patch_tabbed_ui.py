import re

JS_PATH = 'apps/uranos_project_os/uranos_project_os/public/js/desk_theme.js'
CSS_PATH = 'apps/uranos_project_os/uranos_project_os/public/css/desk_theme.css'

def patch_js():
    with open(JS_PATH, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Replace modal body & chat with Tabbed UI structure
    old_body_and_chat = '''            <div class="gv-ai-modal-body" id="gv-ai-modal-body">
              <div class="gv-ai-loading-skeleton">
                <div class="gv-ai-skeleton-line" style="width: 85%;"></div>
                <div class="gv-ai-skeleton-line" style="width: 65%;"></div>
                <div class="gv-ai-skeleton-line" style="width: 95%;"></div>
                <div class="gv-ai-skeleton-line" style="width: 45%;"></div>
              </div>
            </div>

            <!-- INTERACTIVE RAG CHAT SECTION -->
            <div class="gv-ai-chat-section" id="gv-ai-chat-section">
              <div class="gv-ai-chat-header">
                <div class="gv-ai-chat-header-title">
                  <span class="gv-ai-chat-icon">💬</span>
                  <span class="gv-ai-chat-title-text">${__("Interactive Project Copilot")}</span>
                </div>
                <span class="gv-ai-chat-badge">${__("Live RAG")}</span>
              </div>
              <div class="gv-ai-chat-log" id="gv-ai-chat-log"></div>
              <div class="gv-ai-chat-input-row">
                <input
                  type="text"
                  id="gv-ai-chat-input"
                  class="gv-ai-chat-input"
                  placeholder="${__("Ask AI Copilot about blockers, material delays, or resolutions...")}"
                  aria-label="${__("Ask AI Copilot")}"
                  autocomplete="off"
                />
                <button
                  type="button"
                  id="gv-ai-chat-send"
                  class="gv-ai-chat-send"
                  title="${__("Send Inquiry")}"
                  aria-label="${__("Send Inquiry")}"
                >
                  <span class="gv-ai-chat-send-icon">➤</span>
                  <span class="gv-ai-chat-send-text">${__("Send")}</span>
                </button>
              </div>
            </div>'''

    new_tabbed_structure = '''            <!-- TAB NAVIGATION BAR -->
            <div class="gv-ai-tab-nav" role="tablist">
              <button type="button" class="gv-ai-tab-btn active" id="gv-ai-tab-btn-summary" data-tab="summary" role="tab" aria-selected="true">
                <span class="gv-tab-icon">📊</span>
                <span class="gv-tab-text">${__("Executive Summary")}</span>
              </button>
              <button type="button" class="gv-ai-tab-btn" id="gv-ai-tab-btn-copilot" data-tab="copilot" role="tab" aria-selected="false">
                <span class="gv-tab-icon">💬</span>
                <span class="gv-tab-text">${__("Interactive Copilot")}</span>
                <span class="gv-tab-badge">${__("Live RAG")}</span>
              </button>
            </div>

            <!-- TAB 1: EXECUTIVE SUMMARY -->
            <div class="gv-ai-tab-pane active" id="gv-ai-tab-summary" role="tabpanel">
              <div class="gv-ai-modal-body" id="gv-ai-modal-body">
                <div class="gv-ai-loading-skeleton">
                  <div class="gv-ai-skeleton-line" style="width: 85%;"></div>
                  <div class="gv-ai-skeleton-line" style="width: 65%;"></div>
                  <div class="gv-ai-skeleton-line" style="width: 95%;"></div>
                  <div class="gv-ai-skeleton-line" style="width: 45%;"></div>
                </div>
              </div>
            </div>

            <!-- TAB 2: INTERACTIVE COPILOT (Full Height) -->
            <div class="gv-ai-tab-pane" id="gv-ai-tab-copilot" role="tabpanel" style="display: none;">
              <div class="gv-ai-chat-full-container" id="gv-ai-chat-section">
                <div class="gv-ai-chat-log" id="gv-ai-chat-log"></div>
                <div class="gv-ai-chat-input-row">
                  <input
                    type="text"
                    id="gv-ai-chat-input"
                    class="gv-ai-chat-input"
                    placeholder="${__("Ask AI Copilot about blockers, progress, materials, or resolutions...")}"
                    aria-label="${__("Ask AI Copilot")}"
                    autocomplete="off"
                  />
                  <button
                    type="button"
                    id="gv-ai-chat-send"
                    class="gv-ai-chat-send"
                    title="${__("Send Inquiry")}"
                    aria-label="${__("Send Inquiry")}"
                  >
                    <span class="gv-ai-chat-send-icon">➤</span>
                    <span class="gv-ai-chat-send-text">${__("Send")}</span>
                  </button>
                </div>
              </div>
            </div>'''

    if old_body_and_chat in code:
        code = code.replace(old_body_and_chat, new_tabbed_structure, 1)
        print("1. Replaced modal body with Tabbed UI structure")
    else:
        print("Warning: old_body_and_chat pattern not found directly, checking partial replacement...")
        # If already partially modified or different indentation
        if 'id="gv-ai-tab-btn-summary"' not in code:
            code = code.replace('<div class="gv-ai-modal-body" id="gv-ai-modal-body">', '<!-- TAB NAVIGATION -->\n' + new_tabbed_structure, 1)

    # 2. Add switchAITab logic and event handler
    tab_logic = '''
  // ── AI MODAL TAB SWITCHING (EXECUTIVE SUMMARY / INTERACTIVE COPILOT) ──
  function switchAITab(tab) {
    if (tab === "copilot") {
      $("#gv-ai-tab-btn-summary").removeClass("active").attr("aria-selected", "false");
      $("#gv-ai-tab-btn-copilot").addClass("active").attr("aria-selected", "true");
      $("#gv-ai-tab-summary").hide();
      $("#gv-ai-tab-copilot").css("display", "flex");
      const el = document.getElementById("gv-ai-chat-log");
      if (el) el.scrollTop = el.scrollHeight;
      setTimeout(() => $("#gv-ai-chat-input").focus(), 80);
    } else {
      $("#gv-ai-tab-btn-copilot").removeClass("active").attr("aria-selected", "false");
      $("#gv-ai-tab-btn-summary").addClass("active").attr("aria-selected", "true");
      $("#gv-ai-tab-copilot").hide();
      $("#gv-ai-tab-summary").css("display", "flex");
    }
  }
  window.switchAITab = switchAITab;

  $(document).on("click", ".gv-ai-tab-btn", function (e) {
    e.preventDefault();
    const tab = $(this).data("tab") || ($(this).attr("id") === "gv-ai-tab-btn-copilot" ? "copilot" : "summary");
    switchAITab(tab);
  });
'''

    if 'function switchAITab(' not in code:
        code = code.replace('  function sendChatToRAG() {', tab_logic + '\n  function sendChatToRAG() {', 1)
        print("2. Added switchAITab function and click listeners")

    # In openAISynthesisModal, ensure it resets to summary tab on open
    old_open_reset = '''    $modal.addClass("open").fadeIn(200);'''
    new_open_reset = '''    switchAITab("summary");
    $modal.addClass("open").fadeIn(200);'''
    if old_open_reset in code and 'switchAITab("summary");' not in code:
        code = code.replace(old_open_reset, new_open_reset, 1)
        print("3. Added switchAITab('summary') reset on openAISynthesisModal")

    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.write(code)
    print("Saved desk_theme.js with tabbed UI successfully!")

def patch_css():
    with open(CSS_PATH, 'r', encoding='utf-8') as f:
        css = f.read()

    tabbed_css = """
/* ── TAB NAVIGATION & FULL-HEIGHT COPILOT TAB ── */
.gv-ai-tab-nav {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 10px 26px !important;
  background: rgba(248, 250, 252, 0.85) !important;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9) !important;
}

.gv-ai-tab-btn {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 9px 20px !important;
  border-radius: 12px !important;
  font-size: 13.5px !important;
  font-weight: 600 !important;
  color: #64748b !important;
  background: transparent !important;
  border: 1.5px solid transparent !important;
  cursor: pointer !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

.gv-ai-tab-btn:hover {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #0f172a !important;
}

.gv-ai-tab-btn.active {
  background: #ffffff !important;
  color: #4f46e5 !important;
  font-weight: 700 !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.12) !important;
}

.gv-ai-tab-btn .gv-tab-badge {
  font-size: 9.5px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #4f46e5 !important;
  background: rgba(99, 102, 241, 0.12) !important;
  border: 1px solid rgba(99, 102, 241, 0.22) !important;
  padding: 1px 7px !important;
  border-radius: 9999px !important;
}

.gv-ai-tab-pane {
  display: flex !important;
  flex-direction: column !important;
  flex: 1 1 auto !important;
  overflow: hidden !important;
}

/* Full height chat inside Copilot Tab */
.gv-ai-chat-full-container {
  display: flex !important;
  flex-direction: column !important;
  flex: 1 1 auto !important;
  height: 480px !important;
  max-height: 56vh !important;
  padding: 18px 26px 14px 26px !important;
  box-sizing: border-box !important;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(255, 255, 255, 0.9) 100%) !important;
}

.gv-ai-chat-full-container .gv-ai-chat-log {
  flex: 1 1 auto !important;
  min-height: 320px !important;
  max-height: 46vh !important;
  overflow-y: auto !important;
  padding: 14px 18px !important;
  margin-bottom: 14px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
  background: #ffffff !important;
  border: 1.5px solid rgba(226, 232, 240, 0.9) !important;
  border-radius: 18px !important;
  box-shadow: inset 0 2px 6px rgba(15, 23, 42, 0.02) !important;
  scroll-behavior: smooth !important;
}

/* Tab 1 Executive Summary Height */
#gv-ai-tab-summary .gv-ai-modal-body {
  flex: 1 1 auto !important;
  height: 480px !important;
  max-height: 56vh !important;
  overflow-y: auto !important;
}

/* RTL Support for Tabbed Interface */
[dir="rtl"] .gv-ai-tab-nav {
  flex-direction: row !important;
}

[dir="rtl"] .gv-ai-tab-btn {
  flex-direction: row !important;
}
"""

    if '.gv-ai-tab-nav' not in css:
        css += "\n" + tabbed_css
        print("4. Appended Tabbed UI styles to desk_theme.css")

    with open(CSS_PATH, 'w', encoding='utf-8') as f:
        f.write(css)
    print("Saved desk_theme.css with tabbed styles successfully!")

if __name__ == '__main__':
    patch_js()
    patch_css()
    print("All Tabbed UI patches completed successfully!")
