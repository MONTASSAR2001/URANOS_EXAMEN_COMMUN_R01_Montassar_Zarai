import os

JS_PATH = 'apps/uranos_project_os/uranos_project_os/public/js/desk_theme.js'
CSS_PATH = 'apps/uranos_project_os/uranos_project_os/public/css/desk_theme.css'

def patch_js():
    with open(JS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    code = "".join(lines)
    if 'id="gv-ai-chat-input"' in code and 'function sendChatToRAG(' in code:
        print("desk_theme.js already patched.")
        return

    # 1. Inject Chat HTML before <div class="gv-ai-modal-footer">
    footer_idx = -1
    for i, line in enumerate(lines):
        if '<div class="gv-ai-modal-footer">' in line and i < 1150:
            footer_idx = i
            break

    if footer_idx == -1:
        raise ValueError("Could not find <div class=\"gv-ai-modal-footer\"> in desk_theme.js")

    chat_html = [
        '            <!-- INTERACTIVE RAG CHAT SECTION -->\n',
        '            <div class="gv-ai-chat-section" id="gv-ai-chat-section">\n',
        '              <div class="gv-ai-chat-header">\n',
        '                <div class="gv-ai-chat-header-title">\n',
        '                  <span class="gv-ai-chat-icon">💬</span>\n',
        '                  <span class="gv-ai-chat-title-text">${__("Interactive Project Copilot")}</span>\n',
        '                </div>\n',
        '                <span class="gv-ai-chat-badge">${__("Live RAG")}</span>\n',
        '              </div>\n',
        '              <div class="gv-ai-chat-log" id="gv-ai-chat-log"></div>\n',
        '              <div class="gv-ai-chat-input-row">\n',
        '                <input\n',
        '                  type="text"\n',
        '                  id="gv-ai-chat-input"\n',
        '                  class="gv-ai-chat-input"\n',
        '                  placeholder="${__("Ask AI Copilot about blockers, material delays, or resolutions...")}"\n',
        '                  aria-label="${__("Ask AI Copilot")}"\n',
        '                  autocomplete="off"\n',
        '                />\n',
        '                <button\n',
        '                  type="button"\n',
        '                  id="gv-ai-chat-send"\n',
        '                  class="gv-ai-chat-send"\n',
        '                  title="${__("Send Inquiry")}"\n',
        '                  aria-label="${__("Send Inquiry")}"\n',
        '                >\n',
        '                  <span class="gv-ai-chat-send-icon">➤</span>\n',
        '                  <span class="gv-ai-chat-send-text">${__("Send")}</span>\n',
        '                </button>\n',
        '              </div>\n',
        '            </div>\n\n',
    ]

    lines = lines[:footer_idx] + chat_html + lines[footer_idx:]
    print("Injected chat HTML into modal card before footer at line", footer_idx)

    # 2. Inject sendChatToRAG function after openAISynthesisModal
    open_end_idx = -1
    for i in range(footer_idx, len(lines)):
        if 'window.openAISynthesisModal = function' in lines[i]:
            pass
        if 'renderSynthesisResult(null, project);' in lines[i] and '500' in lines[i+1] and '};' in lines[i+3]:
            open_end_idx = i + 4
            break

    if open_end_idx == -1:
        # Fallback search for end of openAISynthesisModal
        for i in range(footer_idx, len(lines)):
            if '  // ── 1. NAVBAR OVERHAUL ──' in lines[i]:
                open_end_idx = i
                break

    if open_end_idx == -1:
        raise ValueError("Could not find end of openAISynthesisModal")

    chat_logic = [
        '  // ── INTERACTIVE RAG CHATBOT (PHASE 4 COPILOT) ──\n',
        '  function escapeChatHtml(str) {\n',
        '    if (!str) return "";\n',
        '    return String(str)\n',
        '      .replace(/&/g, "&amp;")\n',
        '      .replace(/</g, "&lt;")\n',
        '      .replace(/>/g, "&gt;")\n',
        '      .replace(/"/g, "&quot;")\n',
        '      .replace(/\'/g, "&#039;");\n',
        '  }\n',
        '\n',
        '  function sendChatToRAG() {\n',
        '    const $input = $("#gv-ai-chat-input");\n',
        '    const message = ($input.val() || "").trim();\n',
        '    if (!message) return;\n',
        '\n',
        '    const $chatLog = $("#gv-ai-chat-log");\n',
        '    const currentProject = $("#gv-ai-project-val").text().trim() || "PV-01";\n',
        '\n',
        '    // a) Show the user\'s message in the chat log\n',
        '    const userMsgHtml = `\n',
        '      <div class="gv-chat-msg gv-chat-msg-user">\n',
        '        <div class="gv-chat-bubble gv-chat-bubble-user">\n',
        '          <div class="gv-chat-sender-label">${__("You")}</div>\n',
        '          <div class="gv-chat-text">${escapeChatHtml(message)}</div>\n',
        '        </div>\n',
        '      </div>\n',
        '    `;\n',
        '    $chatLog.append(userMsgHtml);\n',
        '    $input.val("");\n',
        '    if ($chatLog[0]) $chatLog.scrollTop($chatLog[0].scrollHeight);\n',
        '\n',
        '    // c) Show a "thinking..." indicator\n',
        '    const thinkingId = "gv-ai-thinking-" + Date.now();\n',
        '    const thinkingHtml = `\n',
        '      <div class="gv-chat-msg gv-chat-msg-ai thinking" id="${thinkingId}">\n',
        '        <div class="gv-chat-bubble gv-chat-bubble-ai gv-thinking-bubble">\n',
        '          <div class="gv-chat-sender-label"><span class="gv-sparkle-icon">✨</span> ${__("AI Copilot")}</div>\n',
        '          <div class="gv-chat-thinking-content">\n',
        '            <span class="gv-pulse-dot"></span> <em>${__("Thinking...")}</em>\n',
        '          </div>\n',
        '        </div>\n',
        '      </div>\n',
        '    `;\n',
        '    $chatLog.append(thinkingHtml);\n',
        '    if ($chatLog[0]) $chatLog.scrollTop($chatLog[0].scrollHeight);\n',
        '\n',
        '    $input.prop("disabled", true);\n',
        '    $("#gv-ai-chat-send").prop("disabled", true);\n',
        '\n',
        '    const finishChatResponse = function (replyText, provider, isAi) {\n',
        '      $(`#${thinkingId}`).remove();\n',
        '      $input.prop("disabled", false);\n',
        '      $("#gv-ai-chat-send").prop("disabled", false);\n',
        '      $input.focus();\n',
        '\n',
        '      // d) Render the AI\'s response in the chat log using the existing Markdown parser\n',
        '      const parsedHtml = formatMarkdownContent(replyText);\n',
        '      const aiBadge = isAi\n',
        '        ? `<span class="gv-chat-badge-ai">✨ Groq Llama 3.3</span>`\n',
        '        : `<span class="gv-chat-badge-fallback">🛡️ Offline Safe</span>`;\n',
        '\n',
        '      const aiMsgHtml = `\n',
        '        <div class="gv-chat-msg gv-chat-msg-ai">\n',
        '          <div class="gv-chat-bubble gv-chat-bubble-ai">\n',
        '            <div class="gv-chat-ai-top">\n',
        '              <span class="gv-chat-sender-label"><span class="gv-sparkle-icon">✨</span> ${__("AI Copilot")}</span>\n',
        '              ${aiBadge}\n',
        '            </div>\n',
        '            <div class="gv-chat-markdown-body">${parsedHtml}</div>\n',
        '          </div>\n',
        '        </div>\n',
        '      `;\n',
        '      $chatLog.append(aiMsgHtml);\n',
        '      if ($chatLog[0]) $chatLog.scrollTop($chatLog[0].scrollHeight);\n',
        '    };\n',
        '\n',
        '    const targetLang =\n',
        '      (typeof frappe !== "undefined" && frappe.boot && frappe.boot.user && frappe.boot.user.language) ||\n',
        '      (typeof frappe !== "undefined" && frappe.local && frappe.local.lang) ||\n',
        '      document.documentElement.getAttribute("lang") ||\n',
        '      "en";\n',
        '\n',
        '    // b) Call the newly created @frappe.whitelist() backend method chat_with_project_ai using frappe.call\n',
        '    if (typeof frappe !== "undefined" && frappe.call) {\n',
        '      frappe.call({\n',
        '        method: "uranos_project_os.services.ai_synthesis.chat_with_project_ai",\n',
        '        args: {\n',
        '          project: currentProject,\n',
        '          message: message,\n',
        '          lang: targetLang\n',
        '        },\n',
        '        freeze: false,\n',
        '        silent: true,\n',
        '        callback: function (r) {\n',
        '          let reply = "";\n',
        '          let provider = "URANOS Copilot";\n',
        '          let isAi = false;\n',
        '          if (r && r.message) {\n',
        '            if (typeof r.message === "string") {\n',
        '              reply = r.message;\n',
        '            } else {\n',
        '              reply = r.message.reply || "";\n',
        '              provider = r.message.provider || provider;\n',
        '              isAi = !!r.message.is_ai_generated;\n',
        '            }\n',
        '          }\n',
        '          if (!reply) {\n',
        '            reply = __("No relevant information found for this inquiry.");\n',
        '          }\n',
        '          finishChatResponse(reply, provider, isAi);\n',
        '        },\n',
        '        error: function (err) {\n',
        '          console.error("Chat RAG call error:", err);\n',
        '          finishChatResponse(\n',
        '            __("Failed to contact URANOS AI Copilot. Please check network connection."),\n',
        '            "Error",\n',
        '            false\n',
        '          );\n',
        '        }\n',
        '      });\n',
        '    } else {\n',
        '      setTimeout(function () {\n',
        '        finishChatResponse(\n',
        '          `**Offline Copilot Fallback**\\n\\nReceived inquiry: "${message}" for project **${currentProject}**. (Running in offline fallback mode).`,\n',
        '          "Simulated Fallback",\n',
        '          false\n',
        '        );\n',
        '      }, 350);\n',
        '    }\n',
        '  }\n',
        '\n',
        '  window.sendChatToRAG = sendChatToRAG;\n',
        '\n',
        '  $(document).on("click", "#gv-ai-chat-send", function (e) {\n',
        '    e.preventDefault();\n',
        '    sendChatToRAG();\n',
        '  });\n',
        '\n',
        '  $(document).on("keydown", "#gv-ai-chat-input", function (e) {\n',
        '    if (e.key === "Enter" && !e.shiftKey) {\n',
        '      e.preventDefault();\n',
        '      sendChatToRAG();\n',
        '    }\n',
        '  });\n\n',
    ]

    lines = lines[:open_end_idx] + chat_logic + lines[open_end_idx:]
    print("Injected sendChatToRAG logic after openAISynthesisModal at line", open_end_idx)

    with open(JS_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Updated desk_theme.js successfully!")

def patch_css():
    with open(CSS_PATH, 'r', encoding='utf-8') as f:
        css = f.read()

    # Adjust .gv-ai-modal-body max-height
    if 'max-height: 36vh !important;' not in css:
        css = css.replace(
            '.gv-ai-modal-body {\n  padding: 22px 26px !important;\n  overflow-y: auto !important;\n  flex: 1 1 auto !important;',
            '.gv-ai-modal-body {\n  padding: 22px 26px !important;\n  overflow-y: auto !important;\n  flex: 1 1 auto !important;\n  max-height: 36vh !important;'
        )

    # Append chat section styles if not already present
    if '.gv-ai-chat-section' not in css:
        chat_css = """
/* ── INTERACTIVE RAG CHAT SECTION (PHASE 4 COPILOT) ── */
.gv-ai-chat-section {
  display: flex !important;
  flex-direction: column !important;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.98) 100%) !important;
  border-top: 1px solid rgba(226, 232, 240, 0.9) !important;
  padding: 14px 26px 16px 26px !important;
  flex-shrink: 0 !important;
}

.gv-ai-chat-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 8px !important;
}

.gv-ai-chat-header-title {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-size: 12.5px !important;
  font-weight: 700 !important;
  color: #334155 !important;
  letter-spacing: -0.01em !important;
}

.gv-ai-chat-badge {
  font-size: 10px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #4f46e5 !important;
  background: rgba(99, 102, 241, 0.12) !important;
  border: 1px solid rgba(99, 102, 241, 0.25) !important;
  padding: 2px 8px !important;
  border-radius: 9999px !important;
}

.gv-ai-chat-log {
  max-height: 165px !important;
  min-height: 48px !important;
  overflow-y: auto !important;
  padding: 8px 10px !important;
  margin-bottom: 10px !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 10px !important;
  background: rgba(255, 255, 255, 0.82) !important;
  border: 1px solid rgba(226, 232, 240, 0.8) !important;
  border-radius: 14px !important;
  scroll-behavior: smooth !important;
}

.gv-chat-msg {
  display: flex !important;
  width: 100% !important;
  animation: gv-chat-fade 0.2s ease-out !important;
}

@keyframes gv-chat-fade {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.gv-chat-msg-user {
  justify-content: flex-end !important;
}

.gv-chat-msg-ai {
  justify-content: flex-start !important;
}

.gv-chat-bubble {
  max-width: 84% !important;
  padding: 9px 14px !important;
  border-radius: 14px !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05) !important;
}

.gv-chat-bubble-user {
  background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
  color: #ffffff !important;
  border-bottom-right-radius: 4px !important;
}

.gv-chat-bubble-user .gv-chat-sender-label {
  font-size: 10px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  color: rgba(255, 255, 255, 0.85) !important;
  margin-bottom: 2px !important;
}

.gv-chat-bubble-ai {
  background: #ffffff !important;
  color: #1e293b !important;
  border: 1px solid rgba(226, 232, 240, 0.9) !important;
  border-bottom-left-radius: 4px !important;
}

.gv-chat-ai-top {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  margin-bottom: 4px !important;
  gap: 12px !important;
}

.gv-chat-sender-label {
  font-size: 11px !important;
  font-weight: 700 !important;
  color: #6366f1 !important;
}

.gv-chat-badge-ai {
  font-size: 9.5px !important;
  color: #4338ca !important;
  font-weight: 600 !important;
  background: #eef2ff !important;
  padding: 1px 6px !important;
  border-radius: 6px !important;
}

.gv-chat-badge-fallback {
  font-size: 9.5px !important;
  color: #b45309 !important;
  font-weight: 600 !important;
  background: #fef3c7 !important;
  padding: 1px 6px !important;
  border-radius: 6px !important;
}

.gv-thinking-bubble {
  background: #f8fafc !important;
  border: 1px dashed #cbd5e1 !important;
}

.gv-chat-thinking-content {
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  color: #64748b !important;
  font-size: 12.5px !important;
}

.gv-chat-system-bubble {
  width: 100% !important;
  text-align: center !important;
  font-size: 11.5px !important;
  color: #64748b !important;
  padding: 4px 8px !important;
  background: transparent !important;
}

.gv-chat-markdown-body p {
  margin: 0 0 6px 0 !important;
  font-size: 13px !important;
  line-height: 1.55 !important;
  color: #1e293b !important;
}

.gv-chat-markdown-body p:last-child {
  margin-bottom: 0 !important;
}

.gv-chat-markdown-body ul {
  margin: 4px 0 6px 0 !important;
  padding-left: 18px !important;
}

.gv-chat-markdown-body li {
  font-size: 12.5px !important;
  margin-bottom: 3px !important;
  color: #334155 !important;
}

.gv-chat-markdown-body strong {
  font-weight: 700 !important;
  color: #0f172a !important;
}

/* Chat Input Row */
.gv-ai-chat-input-row {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  width: 100% !important;
}

.gv-ai-chat-input {
  flex: 1 1 auto !important;
  height: 42px !important;
  padding: 0 16px !important;
  background: #ffffff !important;
  border: 1.5px solid #cbd5e1 !important;
  border-radius: 12px !important;
  font-size: 13px !important;
  color: #0f172a !important;
  outline: none !important;
  transition: all 0.18s ease !important;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
}

.gv-ai-chat-input:focus {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18) !important;
}

.gv-ai-chat-input::placeholder {
  color: #94a3b8 !important;
  font-size: 12.5px !important;
}

.gv-ai-chat-send {
  height: 42px !important;
  padding: 0 20px !important;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
  border: none !important;
  border-radius: 12px !important;
  color: #ffffff !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 7px !important;
  cursor: pointer !important;
  transition: all 0.18s ease !important;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.28) !important;
  flex-shrink: 0 !important;
}

.gv-ai-chat-send:hover {
  background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35) !important;
}

.gv-ai-chat-send:active {
  transform: translateY(0) !important;
}

.gv-ai-chat-send:disabled,
.gv-ai-chat-input:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

/* RTL Support for Chat */
[dir="rtl"] .gv-ai-chat-header,
[dir="rtl"] .gv-ai-chat-input-row {
  flex-direction: row !important;
}

[dir="rtl"] .gv-chat-msg-user {
  justify-content: flex-start !important;
}

[dir="rtl"] .gv-chat-msg-ai {
  justify-content: flex-end !important;
}

[dir="rtl"] .gv-chat-bubble-user {
  border-bottom-right-radius: 14px !important;
  border-bottom-left-radius: 4px !important;
}

[dir="rtl"] .gv-chat-bubble-ai {
  border-bottom-left-radius: 14px !important;
  border-bottom-right-radius: 4px !important;
}

[dir="rtl"] .gv-chat-markdown-body ul {
  padding-left: 0 !important;
  padding-right: 18px !important;
}
"""
        css += "\n" + chat_css
        print("Successfully appended Chat CSS to desk_theme.css")

    with open(CSS_PATH, 'w', encoding='utf-8') as f:
        f.write(css)
    print("Updated desk_theme.css successfully")

if __name__ == '__main__':
    patch_js()
    patch_css()
    print("All patches completed successfully!")
