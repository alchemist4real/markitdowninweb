document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const batchQueue = document.getElementById("batchQueue");
  const batchList = document.getElementById("batchList");
  const batchCountLabel = document.getElementById("batchCountLabel");
  const clearBatchBtn = document.getElementById("clearBatchBtn");
  const convertBatchZipBtn = document.getElementById("convertBatchZipBtn");

  const urlInput = document.getElementById("urlInput");
  const convertUrlBtn = document.getElementById("convertUrlBtn");

  const rawTextInput = document.getElementById("rawTextInput");
  const textExtHint = document.getElementById("textExtHint");
  const convertTextBtn = document.getElementById("convertTextBtn");

  const statusBar = document.getElementById("statusBar");
  const statusText = document.getElementById("statusText");

  const outputSection = document.getElementById("outputSection");
  const docTitleBadge = document.getElementById("docTitleBadge");
  const charCountEl = document.getElementById("charCount");
  const wordCountEl = document.getElementById("wordCount");
  const tokenCountEl = document.getElementById("tokenCount");

  const markdownSource = document.getElementById("markdownSource");
  const markdownPreview = document.getElementById("markdownPreview");
  const copyMdBtn = document.getElementById("copyMdBtn");
  const downloadMdBtn = document.getElementById("downloadMdBtn");

  const logWindow = document.getElementById("logWindow");
  const clearLogsBtn = document.getElementById("clearLogsBtn");

  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const settingsToggleBtn = document.getElementById("settingsToggleBtn");
  const closeSettingsBtn = document.getElementById("closeSettingsBtn");
  const settingsDrawer = document.getElementById("settingsDrawer");

  const enablePluginsCheckbox = document.getElementById("enablePluginsCheckbox");
  const keepDataUrisCheckbox = document.getElementById("keepDataUrisCheckbox");
  const llmProviderSelect = document.getElementById("llmProviderSelect");
  const openaiApiKeyInput = document.getElementById("openaiApiKeyInput");
  const llmModelInput = document.getElementById("llmModelInput");
  const docintelEndpointInput = document.getElementById("docintelEndpointInput");
  const cuEndpointInput = document.getElementById("cuEndpointInput");

  const tabBtns = document.querySelectorAll(".tab-btn, .mobile-nav-btn[data-tab]");
  const tabContents = document.querySelectorAll(".tab-content");

  let queueFiles = [];
  let currentActiveFilename = "converted.md";

  // Configure Marked renderer
  if (typeof marked !== "undefined") {
    marked.setOptions({
      highlight: function (code, lang) {
        if (typeof hljs !== "undefined" && lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return code;
      },
      gfm: true,
      breaks: true
    });
  }

  // Logger Helper
  function log(msg, type = "info") {
    if (!logWindow) return;
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${msg}`;
    logWindow.appendChild(line);
    logWindow.scrollTop = logWindow.scrollHeight;
  }

  if (clearLogsBtn) {
    clearLogsBtn.addEventListener("click", () => {
      if (logWindow) logWindow.innerHTML = "";
      log("Logs cleared.", "info");
    });
  }

  // Theme Toggle
  themeToggleBtn.addEventListener("click", () => {
    const isDark = document.body.getAttribute("data-theme") === "dark";
    if (isDark) {
      document.body.removeAttribute("data-theme");
      log("Switched to Light theme.", "info");
    } else {
      document.body.setAttribute("data-theme", "dark");
      log("Switched to Dark theme.", "info");
    }
  });

  // Settings Drawer Toggle
  function toggleSettings() {
    settingsDrawer.classList.toggle("hidden");
  }
  settingsToggleBtn.addEventListener("click", toggleSettings);
  closeSettingsBtn.addEventListener("click", toggleSettings);
  const mobileSettingsBtn = document.getElementById("mobileSettingsBtn");
  if (mobileSettingsBtn) mobileSettingsBtn.addEventListener("click", toggleSettings);

  // Tab Switching
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      if (!targetTab) return;

      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      document.querySelectorAll(`[data-tab="${targetTab}"]`).forEach(b => b.classList.add("active"));
      const contentEl = document.getElementById(targetTab);
      if (contentEl) contentEl.classList.add("active");
    });
  });

  // Dropzone Events
  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files));
    }
  });

  // Handle Files Addition
  function handleFiles(files) {
    queueFiles = queueFiles.concat(files);
    updateBatchQueueUI();

    if (files.length === 1) {
      log(`Selected file: ${files[0].name}. Initiating single conversion...`, "info");
      convertSingleFile(files[0]);
    } else {
      log(`Added ${files.length} files to batch queue. Total: ${queueFiles.length}.`, "info");
    }
  }

  function updateBatchQueueUI() {
    if (queueFiles.length === 0) {
      batchQueue.classList.add("hidden");
      return;
    }

    batchQueue.classList.remove("hidden");
    batchCountLabel.textContent = `BATCH QUEUE (${queueFiles.length} FILES)`;
    batchList.innerHTML = "";

    queueFiles.forEach((file, index) => {
      const item = document.createElement("div");
      item.className = "batch-item";
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      item.innerHTML = `
        <div class="batch-item-info">
          <span class="item-status pending">READY</span>
          <strong>${escapeHtml(file.name)}</strong>
          <span class="muted">(${sizeMb} MB)</span>
        </div>
        <button class="text-btn" data-index="${index}">&times; Remove</button>
      `;
      batchList.appendChild(item);
    });

    batchList.querySelectorAll("button[data-index]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.target.getAttribute("data-index"));
        queueFiles.splice(idx, 1);
        updateBatchQueueUI();
      });
    });
  }

  clearBatchBtn.addEventListener("click", () => {
    queueFiles = [];
    updateBatchQueueUI();
    log("Cleared batch queue.", "info");
  });

  // Single File Conversion
  async function convertSingleFile(file) {
    showStatus(`Converting ${file.name} through MarkItDown engine...`);
    log(`Starting stream conversion for ${file.name}...`, "info");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("enable_plugins", enablePluginsCheckbox.checked);
    formData.append("keep_data_uris", keepDataUrisCheckbox.checked);
    if (llmProviderSelect && llmProviderSelect.value) formData.append("llm_provider", llmProviderSelect.value);

    if (openaiApiKeyInput && openaiApiKeyInput.value) formData.append("openai_api_key", openaiApiKeyInput.value);
    if (llmModelInput && llmModelInput.value) formData.append("llm_model", llmModelInput.value);
    if (docintelEndpointInput && docintelEndpointInput.value) formData.append("docintel_endpoint", docintelEndpointInput.value);
    if (cuEndpointInput && cuEndpointInput.value) formData.append("cu_endpoint", cuEndpointInput.value);

    try {
      const resp = await fetch("/api/convert/file", {
        method: "POST",
        body: formData
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "Server error");
      }

      const data = await resp.json();
      currentActiveFilename = `${file.name.split('.')[0]}.md`;
      displayOutput(data.markdown, data.title || file.name, data.char_count, data.word_count, data.estimated_tokens);
      log(`Successfully converted ${file.name} (${data.char_count} chars).`, "success");
    } catch (err) {
      log(`Error converting ${file.name}: ${err.message}`, "error");
      alert(`Conversion error: ${err.message}`);
    } finally {
      hideStatus();
    }
  }

  // URL Conversion
  convertUrlBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) return alert("Please enter a valid URL.");

    showStatus(`Fetching & converting URI: ${url}...`);
    log(`Sending URL convert request for ${url}...`, "info");

    try {
      const resp = await fetch("/api/convert/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url,
          enable_plugins: enablePluginsCheckbox.checked,
          keep_data_uris: keepDataUrisCheckbox.checked,
          openai_api_key: openaiApiKeyInput.value || null,
          llm_model: llmModelInput.value || "gpt-4o"
        })
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "URL conversion failed");
      }

      const data = await resp.json();
      currentActiveFilename = "web_converted.md";
      displayOutput(data.markdown, data.title || url, data.char_count, data.word_count, data.estimated_tokens);
      log(`URL successfully converted (${data.char_count} chars).`, "success");
    } catch (err) {
      log(`URL conversion error: ${err.message}`, "error");
      alert(`URL error: ${err.message}`);
    } finally {
      hideStatus();
    }
  });

  // Direct Text Conversion
  convertTextBtn.addEventListener("click", async () => {
    const text = rawTextInput.value;
    if (!text.trim()) return alert("Please paste some HTML or text snippet.");

    showStatus("Converting text snippet to Markdown...");
    log("Sending raw text conversion request...", "info");

    try {
      const resp = await fetch("/api/convert/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          extension_hint: textExtHint.value,
          enable_plugins: enablePluginsCheckbox.checked
        })
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || "Text conversion failed");
      }

      const data = await resp.json();
      currentActiveFilename = "snippet.md";
      displayOutput(data.markdown, "Text Snippet", data.char_count, data.word_count, data.estimated_tokens);
      log(`Text snippet converted successfully (${data.char_count} chars).`, "success");
    } catch (err) {
      log(`Text conversion error: ${err.message}`, "error");
      alert(`Text error: ${err.message}`);
    } finally {
      hideStatus();
    }
  });

  // Batch ZIP Conversion
  convertBatchZipBtn.addEventListener("click", async () => {
    if (queueFiles.length === 0) return alert("Batch queue is empty.");

    showStatus(`Processing batch of ${queueFiles.length} files into ZIP archive...`);
    log(`Starting batch ZIP conversion for ${queueFiles.length} files...`, "info");

    const formData = new FormData();
    queueFiles.forEach(f => formData.append("files", f));
    formData.append("enable_plugins", enablePluginsCheckbox.checked);
    formData.append("keep_data_uris", keepDataUrisCheckbox.checked);
    if (openaiApiKeyInput.value) formData.append("openai_api_key", openaiApiKeyInput.value);

    try {
      const resp = await fetch("/api/convert/batch", {
        method: "POST",
        body: formData
      });

      if (!resp.ok) throw new Error("Batch conversion server error");

      const blob = await resp.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = "markitdowninweb_batch_export.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      log(`Batch ZIP exported successfully (${queueFiles.length} files).`, "success");
    } catch (err) {
      log(`Batch conversion error: ${err.message}`, "error");
      alert(`Batch error: ${err.message}`);
    } finally {
      hideStatus();
    }
  });

  // Preset Buttons
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const preset = btn.getAttribute("data-preset");
      if (preset === "sample.pdf") {
        urlInput.value = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf";
        document.querySelector('[data-tab="urlTab"]').click();
        log("Loaded Preset: Sample PDF URL.", "info");
      } else if (preset === "table.xlsx" || preset === "doc.docx" || preset === "slide.pptx") {
        rawTextInput.value = "<h1>Sample Data Table</h1><table><tr><th>Name</th><th>Role</th></tr><tr><td>Alice</td><td>Developer</td></tr><tr><td>Bob</td><td>Designer</td></tr></table>";
        document.querySelector('[data-tab="textTab"]').click();
        log(`Loaded Preset: ${preset} snippet mockup.`, "info");
      }
    });
  });

  // Display Output
  function displayOutput(markdown, title, charCount, wordCount, tokenCount) {
    markdownSource.value = markdown;

    if (typeof marked !== "undefined") {
      markdownPreview.innerHTML = marked.parse(markdown);
    } else {
      markdownPreview.textContent = markdown;
    }

    docTitleBadge.textContent = title;
    charCountEl.textContent = charCount.toLocaleString();
    wordCountEl.textContent = wordCount.toLocaleString();
    tokenCountEl.textContent = tokenCount.toLocaleString();

    outputSection.classList.remove("hidden");
    outputSection.scrollIntoView({ behavior: "smooth" });
  }

  // Copy & Download Actions
  copyMdBtn.addEventListener("click", () => {
    if (!markdownSource.value) return;
    navigator.clipboard.writeText(markdownSource.value).then(() => {
      const origText = copyMdBtn.textContent;
      copyMdBtn.textContent = "COPIED!";
      setTimeout(() => copyMdBtn.textContent = origText, 2000);
      log("Markdown copied to clipboard.", "info");
    });
  });

  downloadMdBtn.addEventListener("click", () => {
    if (!markdownSource.value) return;
    const blob = new Blob([markdownSource.value], { type: "text/markdown;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = currentActiveFilename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    log(`Downloaded ${currentActiveFilename}.`, "info");
  });

  function showStatus(text) {
    statusText.textContent = text;
    statusBar.classList.remove("hidden");
  }

  function hideStatus() {
    statusBar.classList.add("hidden");
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
