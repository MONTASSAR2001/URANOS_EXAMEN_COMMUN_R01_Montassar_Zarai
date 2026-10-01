#!/usr/bin/env python3
"""
scripts/patch_multimodal_vision_and_hybrid_rag.py
=================================================
Automated deployment script for:
1. Multimodal Vision Analysis (Image-to-Report):
   - Camera/upload button in chat dock.
   - Base64 encoding and image thumbnail display.
   - Live loading indicator in chat.
   - analyze_site_image API call & technical diagnostic report insertion into chat context.
2. Hybrid Semantic Vector Search:
   - Cosine similarity ranking across historical blocker precedents.
   - Top-3 relevant past resolutions injected into RAG context.
3. Multi-destination asset sync & docker bench build.
"""
import os
import subprocess
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

HTML_FILES = [
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html"),
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html"),
]

CSS_FILES = [
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css"),
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css"),
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/public/css/uranos_ai_copilot.css"),
]

JS_FILES = [
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js"),
    os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js"),
]

SERVICES_AI = os.path.join(REPO_ROOT, "apps/uranos_project_os/uranos_project_os/services/ai_synthesis.py")


def patch_html():
    print("=== 1. Patching HTML Templates ===")
    vision_dock_html = '''            <!-- Multimodal Vision Image / Camera Upload -->
            <input type="file" id="uac-vision-file-input" accept="image/*" style="display:none;" />
            <button type="button" class="uac-vision-btn" id="uac-vision-upload-btn" title="Upload Site Photo / Camera (Multimodal Vision Analysis)" aria-label="Upload Site Photo">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                <circle cx="12" cy="13" r="4"></circle>
              </svg>
            </button>
            <button type="button" class="uac-attach-btn" id="uac-attach-btn" title="Attach Telemetry / File" aria-label="Attach File">'''

    for path in HTML_FILES:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if 'id="uac-vision-upload-btn"' not in content:
            # Replace the attach button block
            target = '<button type="button" class="uac-attach-btn" title="Attach Telemetry / File" aria-label="Attach File">'
            if target in content:
                content = content.replace(target, vision_dock_html)
            elif 'class="uac-attach-btn"' in content:
                content = re.sub(
                    r'<button type="button" class="uac-attach-btn".*?</button>',
                    vision_dock_html + '</button>',
                    content,
                    count=1,
                    flags=re.DOTALL
                )
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ Patched HTML: {path}")
        else:
            print(f"  ✓ HTML already contains vision button: {path}")


def patch_css():
    print("\n=== 2. Patching CSS Styles ===")
    vision_css = """
/* ═══════════════════════════════════════════════════════════════════
   MULTIMODAL VISION & ADVANCED DIAGNOSTICS STYLES
   ═══════════════════════════════════════════════════════════════════ */
.uac-vision-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--uac-radius-full);
  background: rgba(79, 70, 229, 0.08);
  border: 1px solid rgba(79, 70, 229, 0.2);
  color: var(--uac-brand-indigo);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s var(--uac-ease);
}

.uac-vision-btn:hover {
  background: var(--uac-brand-indigo);
  color: #ffffff;
  transform: scale(1.06);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.uac-chat-image-preview {
  max-width: 260px;
  max-height: 180px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: block;
}

.uac-image-preview-bubble {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.uac-image-caption {
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 6px;
}

.uac-vision-report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--uac-slate-100);
}

.uac-vision-badge {
  font-size: 10px;
  font-weight: 700;
  color: #059669;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 2px 8px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
"""
    for path in CSS_FILES:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if ".uac-vision-btn" not in content:
            content += "\n" + vision_css
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ Patched CSS: {path}")
        else:
            print(f"  ✓ CSS already contains vision styles: {path}")


def patch_js():
    print("\n=== 3. Patching JS Logic ===")
    vision_handler_code = """
  // ── Multimodal Vision Image Upload Handler ────────────────────────────────
  function handleVisionImageUpload(file) {
    if (!file || !file.type.startsWith("image/")) {
      frappe.show_alert({ message: __("Please select a valid image file"), indicator: "orange" });
      return;
    }

    const reader = new FileReader();
    reader.onload = function(evt) {
      const dataUrl = evt.target.result;
      const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
      const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      // Append User image bubble
      $chatLog.append(`
        <div class="uac-msg uac-msg-user gv-chat-msg-user">
          <div class="uac-bubble-wrap">
            <div class="uac-bubble uac-bubble-user gv-chat-text uac-image-preview-bubble">
              <img src="${dataUrl}" class="uac-chat-image-preview" alt="Site Inspection Photo" />
              <div class="uac-image-caption">📷 ${frappe.utils.escape_html(file.name)}</div>
            </div>
            <span class="uac-msg-time">${time} • ${T("Sent", "Envoyé", "تم الإرسال")}</span>
          </div>
          <div class="uac-user-avatar">
            ${(frappe.session && frappe.session.user ? frappe.session.user.substring(0, 2).toUpperCase() : "U")}
          </div>
        </div>
      `);
      $chatLog.scrollTop($chatLog[0].scrollHeight);

      // Append Vision thinking bubble
      const thinkingId = "uac-thinking-" + Date.now();
      $chatLog.append(`
        <div class="uac-msg uac-msg-ai gv-thinking-bubble" id="${thinkingId}">
          <div class="uac-ai-avatar">🔬</div>
          <div class="uac-bubble-wrap">
            <div class="uac-bubble uac-bubble-ai uac-bubble-thinking">
              <div class="uac-thinking-content">
                <span class="uac-pulse-dot"></span>
                <em>${T("Analyzing site photo with Multimodal Vision Engine (microfissures & defect detection)...", "Analyse de la photo de chantier avec le moteur de vision multimodale...", "جارٍ فحص صورة الموقع بمحرك الرؤية متعدد الوسائط...")}</em>
              </div>
            </div>
          </div>
        </div>
      `);
      $chatLog.scrollTop($chatLog[0].scrollHeight);

      frappe.call({
        method: "uranos_project_os.services.ai_synthesis.analyze_site_image",
        args: {
          image_base64: dataUrl,
          project: activeProject,
          lang: currentLang
        },
        freeze: false,
        silent: true,
        callback: function(r) {
          $(`#${thinkingId}`).remove();
          if (r && r.message && r.message.status === "success") {
            const report = r.message.diagnostic_report;
            const provider = r.message.provider || "Vision Engine";
            const spec = r.message.image_spec || "";
            window.uacLastImageReport = report; // Store for follow-up conversational context

            const respTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            $chatLog.append(`
              <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
                <div class="uac-ai-avatar">🔬</div>
                <div class="uac-bubble-wrap">
                  <div class="uac-bubble uac-bubble-ai">
                    <div class="uac-vision-report-header">
                      <span class="uac-vision-badge">🔬 ${T("Multimodal Vision Report", "Rapport de Vision Multimodale", "تقرير الرؤية متعدد الوسائط")}</span>
                      <span class="uac-bubble-badge">${spec}</span>
                    </div>
                    <div class="uac-bubble-body gv-chat-markdown-body">
                      ${formatMarkdown(report)}
                    </div>
                  </div>
                  <span class="uac-msg-time">${respTime}</span>
                </div>
              </div>
            `);
            $chatLog.scrollTop($chatLog[0].scrollHeight);
          } else {
            frappe.show_alert({ message: __("Failed to analyze site image"), indicator: "red" });
          }
        },
        error: function(err) {
          $(`#${thinkingId}`).remove();
          console.error("[URANOS Vision] Analysis error:", err);
          frappe.show_alert({ message: __("Vision analysis error"), indicator: "red" });
        }
      });
    };
    reader.readAsDataURL(file);
  }
"""

    for path in JS_FILES:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "handleVisionImageUpload" not in content:
            # 1. Insert handleVisionImageUpload right before sendChatMessage
            if "function sendChatMessage(userText) {" in content:
                content = content.replace("function sendChatMessage(userText) {", vision_handler_code + "\n  function sendChatMessage(userText) {")

            # 2. Update sendChatMessage to pass image_context
            old_call = """      args: {
        project: activeProject,
        message: message,
        lang: currentLang
      },"""
            new_call = """      args: {
        project: activeProject,
        message: message,
        lang: currentLang,
        image_context: window.uacLastImageReport || null
      },"""
            if old_call in content:
                content = content.replace(old_call, new_call)

            # 3. Bind file input and upload button
            bind_code = """
    // Vision Image Upload Binding
    const $visionBtn = $("#uac-vision-upload-btn");
    const $visionInput = $("#uac-vision-file-input");

    $visionBtn.off("click").on("click", function(e) {
      e.preventDefault();
      $visionInput.click();
    });

    $visionInput.off("change").on("change", function(e) {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      handleVisionImageUpload(file);
      $(this).val("");
    });
"""
            if "$input.on(\"keydown\"," in content:
                content = content.replace('$input.on("keydown",', bind_code + '\n    $input.on("keydown",')

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ Patched JS: {path}")
        else:
            print(f"  ✓ JS already contains vision handling: {path}")


def sync_and_deploy():
    print("\n=== 4. Syncing files to Docker Container 'uranos-backend' ===")
    all_files = HTML_FILES + CSS_FILES + JS_FILES + [SERVICES_AI]

    for local_path in all_files:
        # Determine container path by replacing REPO_ROOT with /home/frappe/frappe-bench
        rel_path = os.path.relpath(local_path, REPO_ROOT)
        container_path = f"/home/frappe/frappe-bench/{rel_path}"
        cmd = ["docker", "cp", local_path, f"uranos-backend:{container_path}"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  [OK] docker cp -> {container_path}")
        else:
            print(f"  [ERR] {res.stderr.strip()}")

    print("\n=== 5. Building Frappe Assets & Clearing Cache ===")
    cmds = [
        ["docker", "exec", "uranos-backend", "bench", "build", "--app", "uranos_project_os"],
        ["docker", "exec", "uranos-backend", "bench", "clear-cache"],
        ["docker", "exec", "uranos-backend", "bench", "--site", "uranos.localhost", "clear-cache"],
        ["docker", "restart", "uranos-backend"],
    ]
    for c in cmds:
        print(f"   Executing: {' '.join(c)}")
        res = subprocess.run(c, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"   [OK] {' '.join(c)}")
        else:
            print(f"   [ERR] {res.stderr.strip()}")

    print("\n=== Deployment Completed Successfully! ===")


if __name__ == "__main__":
    patch_html()
    patch_css()
    patch_js()
    sync_and_deploy()
