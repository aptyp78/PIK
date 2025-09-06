var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);

// main.ts
var main_exports = {};
__export(main_exports, {
  default: () => GPTImageOCRPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian5 = require("obsidian");

// types.ts
var DEFAULT_PROMPT_TEXT = "Extract only the raw text from this image. Do not add commentary or explanations. Do not prepend anything. Return only the transcribed text in markdown format. Do not put a markdown codeblock around the returned text.";
var DEFAULT_BATCH_PROMPT_TEXT = "Extract only the raw text from each image. Do not add commentary or explanations. Do not prepend anything. Return only the transcribed text in markdown format for each image. Do not put a markdown codeblock around the returned text.";
var FRIENDLY_PROVIDER_NAMES = {
  "openai": "OpenAI",
  "openai-mini": "OpenAI",
  "openai-4.1": "OpenAI",
  "openai-4.1-mini": "OpenAI",
  "openai-4.1-nano": "OpenAI",
  "gemini": "Google",
  "gemini-lite": "Google",
  "gemini-pro": "Google",
  "ollama": "Ollama",
  "lmstudio": "LMStudio",
  "custom": "Custom Provider"
};
var FRIENDLY_MODEL_NAMES = {
  "gpt-4o": "GPT-4o",
  "gpt-4o-mini": "GPT-4o Mini",
  "gpt-4.1": "GPT-4.1",
  "gpt-4.1-mini": "GPT-4.1 Mini",
  "gpt-4.1-nano": "GPT-4.1 Nano",
  "llama3.2-vision": "Llama 3.2 Vision",
  "gemma3": "Gemma 3",
  "gemini-2.5-flash": "Gemini Flash 2.5",
  "models/gemini-2.5-flash": "Gemini Flash 2.5",
  "models/gemini-2.5-flash-lite-preview-06-17": "Gemini Flash-Lite Preview 06-17",
  "models/gemini-2.5-pro": "Gemini Pro 2.5"
  // Add more as needed
};
var DEFAULT_SETTINGS = {
  providerType: "openai",
  provider: "openai",
  openaiApiKey: "",
  geminiApiKey: "",
  ollamaUrl: "http://localhost:11434",
  ollamaModel: "llama3.2-vision",
  lmstudioUrl: "http://localhost:1234",
  lmstudioModel: "google/gemma-3-4b",
  customProviderFriendlyName: "Custom Provider",
  customApiUrl: "",
  customApiModel: "",
  customApiKey: "",
  customPrompt: "",
  outputToNewNote: false,
  noteFolderPath: "OCR Notes",
  noteNameTemplate: "Extracted OCR {{YYYY-MM-DD HH-mm-ss}}",
  appendIfExists: false,
  headerTemplate: "",
  footerTemplate: "",
  // Batch image settings
  batchCustomPrompt: "",
  batchOutputToNewNote: false,
  batchNoteFolderPath: "OCR Notes",
  batchNoteNameTemplate: "Batch OCR {{YYYY-MM-DD HH-mm-ss}}",
  batchAppendIfExists: false,
  batchHeaderTemplate: "",
  batchImageHeaderTemplate: "",
  batchImageFooterTemplate: "",
  batchFooterTemplate: "",
  ollamaModelFriendlyName: "",
  lmstudioModelFriendlyName: "",
  customModelFriendlyName: ""
};

// providers/openai-provider.ts
var import_obsidian3 = require("obsidian");

// utils/helpers.ts
var import_obsidian2 = require("obsidian");

// providers/gemini-provider.ts
var import_obsidian = require("obsidian");

// utils/ocr-utils.ts
async function processSingleImage(provider, base64, mime = "image/jpeg", prompt = "What does this say?") {
  const image = {
    name: "image.jpg",
    base64,
    mime,
    size: base64.length * 0.75,
    source: "inline"
  };
  if (provider.process) {
    return await provider.process([image], prompt);
  } else {
    const result = await provider.extractTextFromBase64(base64);
    return result ?? "";
  }
}

// providers/gemini-provider.ts
var GeminiProvider = class {
  constructor(apiKey, model = "models/gemini-2.5-flash", prompt = DEFAULT_PROMPT_TEXT, nameOverride) {
    this.apiKey = apiKey;
    this.model = model;
    this.prompt = prompt;
    __publicField(this, "id", "gemini");
    __publicField(this, "name");
    this.name = nameOverride ?? model.replace(/^models\//, "");
  }
  async process(images, prompt) {
    try {
      const contents = [
        {
          role: "user",
          parts: [
            ...images.map((img) => ({
              inline_data: {
                mime_type: img.mime,
                data: img.base64
              }
            })),
            {
              text: prompt
            }
          ]
        }
      ];
      const response = await (0, import_obsidian.requestUrl)({
        url: `https://generativelanguage.googleapis.com/v1beta/${this.model}:generateContent?key=${this.apiKey}`,
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ contents })
      });
      const data = parseJsonResponse(
        response,
        (d) => Array.isArray(d.candidates) && !!d.candidates[0]?.content?.parts
      );
      const part = data.candidates[0]?.content?.parts?.[0]?.text?.trim();
      if (part) return part;
      console.warn("Gemini response did not contain expected text:", data);
      return "";
    } catch (err) {
      console.error("Gemini fetch error:", err);
      return "";
    }
  }
  async extractTextFromBase64(image) {
    return await processSingleImage(this, image, "image/jpeg", this.prompt);
  }
};

// utils/helpers.ts
function getFriendlyProviderNames(settings) {
  return {
    ...FRIENDLY_PROVIDER_NAMES,
    ...settings.customProviderFriendlyName?.trim() ? { "custom": settings.customProviderFriendlyName.trim() } : {}
  };
}
function moveCursorToEnd(editor) {
  requestAnimationFrame(() => {
    const lastLine = editor.lastLine();
    const lastCh = editor.getLine(lastLine)?.length || 0;
    editor.setCursor({ line: lastLine, ch: lastCh });
    scrollEditorToCursor(editor);
  });
}
function scrollEditorToCursor(editor) {
  try {
    const maybeCM = editor.cm;
    if (maybeCM && typeof maybeCM === "object" && "scrollIntoView" in maybeCM && typeof maybeCM.scrollIntoView === "function") {
      maybeCM.scrollIntoView(editor.getCursor(), 100);
    }
  } catch (e) {
    console.warn("scrollIntoView failed or is unsupported in this version.", e);
  }
}
function parseJsonResponse(response, validator) {
  try {
    const data = JSON.parse(response.text);
    if (validator && !validator(data)) {
      throw new Error("Response format validation failed.");
    }
    return data;
  } catch (e) {
    console.error("Failed to parse API response:", response.text);
    throw new Error("Invalid JSON or unexpected structure in API response.");
  }
}
function formatTemplate(template, context = {}) {
  const getValue = (path) => {
    const parts = path.split(".");
    let value = context;
    for (const part of parts) {
      if (value && part in value) {
        value = value[part];
      } else {
        value = void 0;
        break;
      }
    }
    if (value !== void 0) return value;
    switch (path) {
      case "model.id":
        return context.model?.id ?? context.modelId ?? context.model ?? "";
      case "model.name":
        return context.model?.name ?? context.modelName ?? context.model ?? "";
      case "provider.name":
        return context.provider?.name ?? context.providerName ?? "";
      case "provider.id":
        return context.provider?.id ?? context.providerId ?? context.provider ?? "";
      case "provider.type":
        return context.provider?.type ?? context.providerType ?? "";
      case "image.filename":
        return context.image?.filename ?? context.image?.name ?? "";
      case "image.name": {
        const fname = context.image?.filename ?? context.image?.name ?? "";
        return fname.replace(/\.[^.]*$/, "");
      }
      case "image.extension": {
        const fname = context.image?.filename ?? context.image?.name ?? "";
        const m = fname.match(/\.([^.]+)$/);
        return m ? m[1] : "";
      }
      case "image.path":
        return context.image?.path ?? context.image?.source ?? "";
      case "image.size":
        return context.image?.size ?? "";
      case "image.dimensions":
        if (context.image?.width && context.image?.height) {
          return `${context.image.width}x${context.image.height}`;
        }
        return "";
      case "image.width":
        return context.image?.width ?? "";
      case "image.height":
        return context.image?.height ?? "";
      case "image.created":
        return context.image?.created ?? "";
      case "image.modified":
        return context.image?.modified ?? "";
      case "image.camera.make":
        return context.image?.camera?.make ?? "";
      case "image.camera.model":
        return context.image?.camera?.model ?? "";
      case "image.lens.model":
        return context.image?.lens?.model ?? "";
      case "image.iso":
        return context.image?.iso ?? "";
      case "image.exposure":
        return context.image?.exposure ?? "";
      case "image.aperture":
        return context.image?.aperture ?? "";
      case "image.focalLength":
        return context.image?.focalLength ?? "";
      case "image.orientation":
        return context.image?.orientation ?? "";
      case "image.gps.latitude":
        return context.image?.gps?.latitude ?? "";
      case "image.gps.longitude":
        return context.image?.gps?.longitude ?? "";
      case "image.gps.altitude":
        return context.image?.gps?.altitude ?? "";
      case "embed.altText":
        return context.embed?.altText ?? "";
      case "embed.url":
        return context.embed?.path ?? context.embed?.url ?? "";
      default:
        return "";
    }
  };
  return template.replace(/{{(.*?)}}/g, (_, expr) => {
    expr = expr.trim();
    if (expr.startsWith("date:")) {
      const fmt = expr.slice(5).trim();
      return window.moment ? window.moment().format(fmt) : "";
    }
    if (window.moment && /^[YMDHms\-:/ ]+$/.test(expr)) {
      return window.moment().format(expr);
    }
    const val = getValue(expr);
    return val != null ? String(val) : "";
  });
}
function applyFormatting(plugin, content, context) {
  if (Array.isArray(context.images) && Array.isArray(content)) {
    const batchHeader = formatTemplate(plugin.settings.batchHeaderTemplate || "", context);
    const batchFooter = formatTemplate(plugin.settings.batchFooterTemplate || "", context);
    const formattedImages = content.map((imgText, i) => {
      const imgContext = {
        ...context,
        image: context.images[i],
        imageIndex: i + 1,
        imageTotal: context.images.length
      };
      const imgHeader = formatTemplate(plugin.settings.batchImageHeaderTemplate || "", imgContext);
      const imgFooter = formatTemplate(plugin.settings.batchImageFooterTemplate || "", imgContext);
      return [imgHeader, imgText, imgFooter ? "\n" + imgFooter : ""].filter(Boolean).join("");
    });
    return [batchHeader, ...formattedImages, batchFooter].filter(Boolean).join("");
  }
  const header = formatTemplate(plugin.settings.headerTemplate || "", context);
  const footer = formatTemplate(plugin.settings.footerTemplate || "", context);
  return [header, content, footer ? "\n" + footer : ""].filter(Boolean).join("");
}
async function handleExtractedContent(plugin, content, editor, context = {}) {
  if (!editor) {
    editor = plugin.app.workspace.activeEditor?.editor ?? null;
  }
  const finalContent = applyFormatting(plugin, content, context);
  const isBatch = Array.isArray(context.images);
  const outputToNewNote = isBatch ? plugin.settings.batchOutputToNewNote : plugin.settings.outputToNewNote;
  if (!outputToNewNote) {
    if (editor) {
      const cursor = editor.getCursor();
      editor.replaceSelection(finalContent);
      const newPos = editor.offsetToPos(
        editor.posToOffset(cursor) + finalContent.length
      );
      editor.setCursor(newPos);
      scrollEditorToCursor(editor);
    } else {
      new import_obsidian2.Notice("No active editor to paste into.");
    }
    return;
  }
  const name = formatTemplate(
    isBatch ? plugin.settings.batchNoteNameTemplate : plugin.settings.noteNameTemplate,
    context
  );
  const folder = formatTemplate(
    isBatch ? plugin.settings.batchNoteFolderPath : plugin.settings.noteFolderPath,
    context
  ).trim();
  const path = folder ? `${folder}/${name}.md` : `${name}.md`;
  if (folder) {
    const folderExists = plugin.app.vault.getAbstractFileByPath(folder);
    if (!folderExists) {
      try {
        await plugin.app.vault.createFolder(folder);
      } catch (err) {
        new import_obsidian2.Notice(`Failed to create folder "${folder}".`);
        console.error(err);
        return;
      }
    }
  }
  let file = plugin.app.vault.getAbstractFileByPath(path);
  const appendIfExists = isBatch ? plugin.settings.batchAppendIfExists : plugin.settings.appendIfExists;
  if (file instanceof import_obsidian2.TFile) {
    if (appendIfExists) {
      const existing = await plugin.app.vault.read(file);
      const updatedContent = existing + "\n\n" + finalContent;
      await plugin.app.vault.modify(file, updatedContent);
      const leaf = plugin.app.workspace.getLeaf(true);
      await leaf.openFile(file);
      const activeEditor = plugin.app.workspace.activeEditor?.editor;
      if (activeEditor) {
        const pos = activeEditor.offsetToPos(updatedContent.length);
        activeEditor.setCursor(pos);
        scrollEditorToCursor(activeEditor);
      }
      return;
    } else {
      let base = name;
      let ext = ".md";
      let counter = 1;
      let uniqueName = `${base}${ext}`;
      let uniquePath = folder ? `${folder}/${uniqueName}` : uniqueName;
      while (plugin.app.vault.getAbstractFileByPath(uniquePath)) {
        uniqueName = `${base} ${counter}${ext}`;
        uniquePath = folder ? `${folder}/${uniqueName}` : uniqueName;
        counter++;
      }
      file = await plugin.app.vault.create(uniquePath, finalContent);
    }
  } else {
    try {
      file = await plugin.app.vault.create(path, finalContent);
    } catch (err) {
      new import_obsidian2.Notice(`Failed to create note at "${path}".`);
      console.error(err);
      return;
    }
  }
  if (!(file instanceof import_obsidian2.TFile)) return;
  await plugin.app.workspace.getLeaf(true).openFile(file);
  setTimeout(() => {
    const activeEditor = plugin.app.workspace.activeEditor?.editor;
    if (activeEditor) {
      moveCursorToEnd(activeEditor);
    }
  }, 10);
}
function findRelevantImageEmbed(editor) {
  const sel = editor.getSelection();
  let match = sel.match(/!\[\[(.+?)\]\]/);
  if (match) {
    const link = match[1].split("|")[0].trim();
    return { link, isExternal: false, embedType: "internal", embedText: match[0] };
  }
  match = sel.match(/!\[.*?\]\((.+?)\)/);
  if (match) {
    const link = match[1].split(" ")[0].replace(/["']/g, "");
    return {
      link,
      isExternal: /^https?:\/\//i.test(link),
      embedType: "external",
      embedText: match[0]
    };
  }
  for (let i = editor.getCursor().line; i >= 0; i--) {
    const line = editor.getLine(i);
    let embedMatch = line.match(/!\[\[(.+?)\]\]/);
    if (embedMatch) {
      const link = embedMatch[1].split("|")[0].trim();
      return { link, isExternal: false, embedType: "internal", embedText: embedMatch[0] };
    }
    embedMatch = line.match(/!\[.*?\]\((.+?)\)/);
    if (embedMatch) {
      const link = embedMatch[1].split(" ")[0].replace(/["']/g, "");
      return {
        link,
        isExternal: /^https?:\/\//i.test(link),
        embedType: "external",
        embedText: embedMatch[0]
      };
    }
  }
  return null;
}
function resolveInternalImagePath(app, link) {
  let file = app.vault.getAbstractFileByPath(link);
  if (file instanceof import_obsidian2.TFile) return file;
  return app.vault.getFiles().find((f) => f.name === link) || null;
}
async function fetchExternalImageAsArrayBuffer(url) {
  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.arrayBuffer();
  } catch (e) {
    try {
      const proxyUrl = `https://corsproxy.rootiest.com/proxy?url=${encodeURIComponent(url)}`;
      const resp = await fetch(proxyUrl);
      if (!resp.ok) throw new Error(`HTTP ${resp.status} from proxy`);
      return await resp.arrayBuffer();
    } catch (e2) {
      console.error("Failed to fetch image.");
      new import_obsidian2.Notice(
        "Failed to fetch image.\nIf you can see the image in preview, right-click and 'Save image to vault',\nthen run OCR on the saved copy."
      );
      return null;
    }
  }
}
function arrayBufferToBase64(buffer) {
  const binary = new Uint8Array(buffer).reduce(
    (acc, byte) => acc + String.fromCharCode(byte),
    ""
  );
  return btoa(binary);
}
async function getImageDimensionsFromArrayBuffer(buffer) {
  return new Promise((resolve) => {
    const blob = new Blob([buffer]);
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const dims = { width: img.width, height: img.height };
      URL.revokeObjectURL(url);
      resolve(dims);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}
async function selectImageFile() {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = () => {
      const file = input.files?.[0] || null;
      resolve(file);
    };
    input.click();
  });
}
async function selectFolder() {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.webkitdirectory = true;
    input.onchange = () => {
      resolve(input.files || null);
    };
    input.click();
  });
}
function getImageMimeType(fileName) {
  const ext = fileName.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "png":
      return "image/png";
    case "jpg":
    case "jpeg":
      return "image/jpeg";
    case "webp":
      return "image/webp";
    case "gif":
      return "image/gif";
    case "bmp":
      return "image/bmp";
    case "svg":
      return "image/svg+xml";
    default:
      return "application/octet-stream";
  }
}
function getProviderType(providerId) {
  return providerId.startsWith("gemini") ? "gemini" : "openai";
}
function buildOCRContext({
  providerId,
  providerName,
  providerType,
  modelId,
  modelName,
  prompt,
  images,
  singleImage
}) {
  const base = {
    provider: {
      id: providerId,
      name: providerName,
      type: providerType
    },
    model: {
      id: modelId,
      name: modelName
    },
    prompt
  };
  if (images && images.length > 1) {
    return {
      ...base,
      images: images.map((img, i) => ({
        name: img.name.replace(/\.[^.]*$/, ""),
        extension: img.name.split(".").pop() || "",
        path: img.path,
        size: img.size,
        mime: img.mime,
        width: img.width,
        height: img.height,
        index: i + 1,
        total: images.length
      }))
    };
  } else if (singleImage || images && images.length === 1) {
    const img = singleImage || images[0];
    return {
      ...base,
      image: {
        name: img.name.replace(/\.[^.]*$/, ""),
        extension: img.name.split(".").pop() || "",
        path: img.path,
        size: img.size,
        mime: img.mime,
        width: img.width,
        height: img.height,
        index: 1,
        total: 1
      }
    };
  } else {
    return base;
  }
}
function parseEmbedInfo(embedMarkdown, link) {
  let altText = "";
  let url = link;
  const mdMatch = embedMarkdown.match(/!\[([^\]]*)\]\(([^)]+)\)/);
  if (mdMatch) {
    altText = mdMatch[1];
    url = mdMatch[2];
  } else {
    const obsMatch = embedMarkdown.match(/!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/);
    if (obsMatch) {
      url = obsMatch[1];
      altText = obsMatch[2] || "";
    }
  }
  let extension = "";
  let name = url;
  const lastSlash = url.lastIndexOf("/");
  const lastDot = url.lastIndexOf(".");
  if (lastDot > -1 && lastDot > lastSlash) {
    extension = url.slice(lastDot + 1);
    name = url.slice(lastSlash + 1, lastDot);
  } else if (lastSlash > -1) {
    name = url.slice(lastSlash + 1);
  } else if (lastDot > -1) {
    name = url.slice(0, lastDot);
    extension = url.slice(lastDot + 1);
  }
  return {
    name,
    extension,
    path: url,
    altText
  };
}
function templateHasImagePlaceholder(template) {
  return /\{\{\s*image\.[^}]+\s*\}\}/.test(template);
}

// providers/openai-provider.ts
var OpenAIProvider = class {
  constructor(apiKey, model = "gpt-4o", endpoint = "https://api.openai.com/v1/chat/completions", provider = "openai", prompt = DEFAULT_PROMPT_TEXT, nameOverride) {
    this.apiKey = apiKey;
    this.model = model;
    this.endpoint = endpoint;
    this.provider = provider;
    this.prompt = prompt;
    __publicField(this, "id");
    __publicField(this, "name");
    this.id = provider;
    this.name = nameOverride ?? model;
  }
  async process(images, prompt) {
    let payload;
    let endpoint = this.endpoint;
    const base64Images = images.map(
      (img) => img.base64.replace(/^data:image\/\w+;base64,/, "")
    );
    if (this.provider === "ollama") {
      payload = {
        model: this.model,
        messages: [
          {
            role: "user",
            content: prompt,
            images: base64Images
          }
        ],
        max_tokens: 1024,
        stream: false
      };
      endpoint = (this.endpoint ?? "http://localhost:11434") + "/api/chat";
    } else if (this.provider === "lmstudio") {
      payload = {
        model: this.model,
        messages: [
          {
            role: "system",
            content: [
              { type: "text", text: "You are an AI assistant that analyzes images." }
            ]
          },
          {
            role: "user",
            content: [
              { type: "text", text: prompt },
              ...images.map((img) => ({
                type: "image_url",
                image_url: {
                  url: `data:${img.mime};base64,${img.base64}`
                }
              }))
            ]
          }
        ],
        max_tokens: 1024
      };
      endpoint = (this.endpoint ?? "http://localhost:1234") + "/api/v0/chat/completions";
    } else {
      payload = {
        model: this.model,
        messages: [
          {
            role: "user",
            content: [
              ...images.map((img) => ({
                type: "image_url",
                image_url: {
                  url: `data:${img.mime};base64,${img.base64}`
                }
              })),
              {
                type: "text",
                text: prompt
              }
            ]
          }
        ],
        max_tokens: 1024
      };
    }
    const headers = {
      "Content-Type": "application/json"
    };
    if (this.provider === "openai") {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }
    try {
      const response = await (0, import_obsidian3.requestUrl)({
        url: endpoint,
        method: "POST",
        headers,
        body: JSON.stringify(payload)
      });
      const data = parseJsonResponse(
        response,
        (d) => this.provider === "ollama" ? !!d.message?.content : Array.isArray(d.choices)
      );
      const content = this.provider === "ollama" ? data.message?.content?.trim() : data.choices?.[0]?.message?.content?.trim();
      if (content) return content;
      console.warn(`${this.provider} response did not contain expected text:`, data);
      return "";
    } catch (err) {
      console.error(`${this.provider} fetch error:`, err);
      return "";
    }
  }
  async extractTextFromBase64(image) {
    const prepared = {
      name: "image.jpg",
      base64: image,
      mime: "image/jpeg",
      size: image.length * 0.75,
      source: "inline"
    };
    return await this.process([prepared], this.prompt);
  }
};

// settings-tab.ts
var import_obsidian4 = require("obsidian");
var GPTImageOCRSettingTab = class extends import_obsidian4.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    __publicField(this, "plugin");
    this.plugin = plugin;
  }
  /**
   * Renders the settings UI in the Obsidian settings panel.
   */
  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "OCR Plugin Settings" });
    new import_obsidian4.Setting(containerEl).setName("Provider").setDesc("Choose which OCR provider to use.").addDropdown(
      (dropdown) => dropdown.addOption("openai", "OpenAI GPT-4o").addOption("openai-mini", "OpenAI GPT-4o Mini").addOption("openai-4.1", "OpenAI GPT-4.1").addOption("openai-4.1-mini", "OpenAI GPT-4.1 Mini").addOption("openai-4.1-nano", "OpenAI GPT-4.1 Nano").addOption("gemini", "Google Gemini 2.5 Flash").addOption("gemini-lite", "Google Gemini 2.5 Flash-Lite Preview 06-17").addOption("gemini-pro", "Google Gemini 2.5 Pro").addOption("ollama", "Ollama (local)").addOption("lmstudio", "LMStudio (local)").addOption("custom", "Custom OpenAI-compatible").setValue(this.plugin.settings.provider).onChange(async (value) => {
        this.plugin.settings.provider = value;
        await this.plugin.saveSettings();
        this.display();
      })
    );
    if (this.plugin.settings.provider === "openai") {
      new import_obsidian4.Setting(containerEl).setDesc("A fast and highly accurate model. API requires payment.");
    } else if (this.plugin.settings.provider === "gemini") {
      new import_obsidian4.Setting(containerEl).setDesc("A model with good speed and accuracy. Free tier available.");
    } else if (this.plugin.settings.provider === "gemini-lite") {
      new import_obsidian4.Setting(containerEl).setDesc("A lightweight, experimental model. Free tier available. Generous rate-limits.");
    } else if (this.plugin.settings.provider === "gemini-pro") {
      new import_obsidian4.Setting(containerEl).setDesc("A slower but extremely powerful model. Requires paid tier API.");
    } else if (this.plugin.settings.provider === "openai-mini") {
      new import_obsidian4.Setting(containerEl).setDesc("A lower cost and lower latency model, slightly lower quality. API requires payment.");
    } else if (this.plugin.settings.provider === "openai-4.1") {
      new import_obsidian4.Setting(containerEl).setDesc("A powerful GPT-4-tier model. API requires payment.");
    } else if (this.plugin.settings.provider === "openai-4.1-mini") {
      new import_obsidian4.Setting(containerEl).setDesc("Smaller GPT-4.1 variant for faster responses, lower cost. API requires payment.");
    } else if (this.plugin.settings.provider === "openai-4.1-nano") {
      new import_obsidian4.Setting(containerEl).setDesc("Minimal GPT-4.1 variant for lowest cost and latency. API requires payment.");
    } else if (this.plugin.settings.provider === "ollama") {
      new import_obsidian4.Setting(containerEl).setDesc("A locally-hosted Ollama server. Ollama models must be installed separately.");
    } else if (this.plugin.settings.provider === "lmstudio") {
      new import_obsidian4.Setting(containerEl).setDesc("A locally-hosted LMStudio server. LMStudio models must be installed separately.");
    } else if (this.plugin.settings.provider === "custom") {
      new import_obsidian4.Setting(containerEl).setDesc("Any OpenAI-compatible API provider. Must use OpenAI API structure.");
    }
    if (this.plugin.settings.provider.startsWith("openai")) {
      new import_obsidian4.Setting(containerEl).setName("OpenAI API key").setDesc("Your OpenAI API key").addText(
        (text) => text.setPlaceholder("sk-...").setValue(this.plugin.settings.openaiApiKey).onChange(async (value) => {
          this.plugin.settings.openaiApiKey = value.trim();
          await this.plugin.saveSettings();
        })
      );
    }
    if (this.plugin.settings.provider.startsWith("gemini")) {
      new import_obsidian4.Setting(containerEl).setName("Gemini API key").setDesc("Your Google Gemini API key").addText(
        (text) => text.setPlaceholder("AIza...").setValue(this.plugin.settings.geminiApiKey).onChange(async (value) => {
          this.plugin.settings.geminiApiKey = value.trim();
          await this.plugin.saveSettings();
        })
      );
    }
    if (this.plugin.settings.provider === "ollama") {
      new import_obsidian4.Setting(containerEl).setName("Server URL").setDesc("Enter the Ollama server address.").addText(
        (text) => text.setValue(this.plugin.settings.ollamaUrl || "http://localhost:11434").onChange(async (value) => {
          this.plugin.settings.ollamaUrl = value;
          await this.plugin.saveSettings();
        })
      );
      const customUrlDesc = containerEl.createEl("div", { cls: "ai-image-ocr__setting-desc" });
      customUrlDesc.appendText("e.g. ");
      customUrlDesc.createEl("code", { text: "http://localhost:11434" });
      new import_obsidian4.Setting(containerEl).setName("Model Name").setDesc("Enter the ID of the vision model to use.").addText(
        (text) => text.setPlaceholder("llama3.2-vision").setValue(this.plugin.settings.ollamaModel || "").onChange(async (value) => {
          this.plugin.settings.ollamaModel = value;
          await this.plugin.saveSettings();
        })
      );
      const customDesc = containerEl.createEl("div", { cls: "ai-image-ocr__setting-desc" });
      customDesc.appendText("e.g. ");
      customDesc.createEl("code", { text: "llama3.2-vision" });
      customDesc.appendText(" or ");
      customDesc.createEl("code", { text: "llava" });
      if (!this.plugin.settings.ollamaModel) {
        containerEl.createEl("div", {
          text: "\u26A0\uFE0F Please specify a vision model ID for Ollama (e.g. llama3.2-vision).",
          cls: "setting-item-warning"
        });
      }
      new import_obsidian4.Setting(containerEl).setName("Model friendly name").setDesc("Optional. Friendly display name for this model (e.g. 'Llama 3.2 Vision').").addText(
        (text) => text.setPlaceholder("Llama 3.2 Vision").setValue(this.plugin.settings.ollamaModelFriendlyName || "").onChange(async (value) => {
          this.plugin.settings.ollamaModelFriendlyName = value.trim();
          await this.plugin.saveSettings();
        })
      );
    }
    if (this.plugin.settings.provider === "lmstudio") {
      new import_obsidian4.Setting(containerEl).setName("Server URL").setDesc("Enter the LMStudio server address.").addText(
        (text) => text.setValue(this.plugin.settings.lmstudioUrl || "http://localhost:1234").onChange(async (value) => {
          this.plugin.settings.lmstudioUrl = value;
          await this.plugin.saveSettings();
        })
      );
      const customUrlDesc = containerEl.createEl("div", { cls: "ai-image-ocr__setting-desc" });
      customUrlDesc.appendText("e.g. ");
      customUrlDesc.createEl("code", { text: "http://localhost:1234" });
      new import_obsidian4.Setting(containerEl).setName("Model Name").setDesc("Enter the ID of the vision model to use.").addText(
        (text) => text.setPlaceholder("google/gemma-3-4b").setValue(this.plugin.settings.lmstudioModel || "").onChange(async (value) => {
          this.plugin.settings.lmstudioModel = value;
          await this.plugin.saveSettings();
        })
      );
      const customDesc = containerEl.createEl("div", { cls: "ai-image-ocr__setting-desc" });
      customDesc.appendText("e.g. ");
      customDesc.createEl("code", { text: "google/gemma-3-4b" });
      customDesc.appendText(" or ");
      customDesc.createEl("code", { text: "qwen/qwen2.5-vl-7b" });
      if (!this.plugin.settings.lmstudioModel) {
        containerEl.createEl("div", {
          text: "\u26A0\uFE0F Please specify a vision model ID for LMStudio\n(e.g. google/gemma-3-4b, qwen/qwen2.5-vl-7b).",
          cls: "setting-item-warning"
        });
      }
      new import_obsidian4.Setting(containerEl).setName("Model friendly name").setDesc("Optional. Friendly display name for this model (e.g. 'Gemma 3').").addText(
        (text) => text.setPlaceholder("Gemma 3").setValue(this.plugin.settings.lmstudioModelFriendlyName || "").onChange(async (value) => {
          this.plugin.settings.lmstudioModelFriendlyName = value.trim();
          await this.plugin.saveSettings();
        })
      );
    }
    if (this.plugin.settings.provider === "custom") {
      new import_obsidian4.Setting(containerEl).setName("Custom provider friendly name").setDesc("Optional friendly name for your custom OpenAI-compatible provider.").addText(
        (text) => text.setPlaceholder("Custom Provider").setValue(this.plugin.settings.customProviderFriendlyName || "").onChange(async (value) => {
          this.plugin.settings.customProviderFriendlyName = value.trim() || void 0;
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("API endpoint").setDesc("The full URL to the OpenAI-compatible /chat/completions endpoint.").addText(
        (text) => text.setPlaceholder("https://example.com/v1/chat/completions").setValue(this.plugin.settings.customApiUrl).onChange(async (value) => {
          this.plugin.settings.customApiUrl = value.trim();
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Model name").setDesc("Enter the model ID to use.").addText(
        (text) => text.setPlaceholder("my-model-id").setValue(this.plugin.settings.customApiModel).onChange(async (value) => {
          this.plugin.settings.customApiModel = value.trim();
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("API key").setDesc("Optional. Leave empty for no key.").addText(
        (text) => text.setPlaceholder("sk-...").setValue(this.plugin.settings.customApiKey).onChange(async (value) => {
          this.plugin.settings.customApiKey = value.trim();
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Model friendly name").setDesc("Optional. Friendly display name for this model (e.g. 'My Custom Model').").addText(
        (text) => text.setPlaceholder("My Custom Model").setValue(this.plugin.settings.customModelFriendlyName || "").onChange(async (value) => {
          this.plugin.settings.customModelFriendlyName = value.trim();
          await this.plugin.saveSettings();
        })
      );
    }
    containerEl.createEl("hr");
    containerEl.createEl("h3", { text: "Single image extraction settings" });
    const customPromptSetting = new import_obsidian4.Setting(containerEl).setName("Custom prompt").setDesc("Optional prompt to send to the model. Leave blank to use the default.");
    const customPromptTextArea = document.createElement("textarea");
    customPromptTextArea.placeholder = `e.g., Extract any handwritten notes or text from the image.`;
    customPromptTextArea.value = this.plugin.settings.customPrompt;
    customPromptTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    customPromptTextArea.rows = 2;
    customPromptTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.customPrompt = e.target.value;
      await this.plugin.saveSettings();
    });
    customPromptSetting.infoEl.appendChild(customPromptTextArea);
    const headerSetting = new import_obsidian4.Setting(containerEl).setName("Header template").setDesc("Optional markdown placed above the extracted text.\nSupports {{placeholders}}.");
    const headerTextArea = document.createElement("textarea");
    headerTextArea.placeholder = `### Extracted on {{YYYY-MM-DD HH:mm:ss}}
---`;
    headerTextArea.value = this.plugin.settings.headerTemplate;
    headerTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    headerTextArea.rows = 3;
    headerTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.headerTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    headerSetting.infoEl.appendChild(headerTextArea);
    const footerSetting = new import_obsidian4.Setting(containerEl).setName("Footer template").setDesc("Optional markdown placed below the extracted text.\nSupports {{placeholders}}.");
    const footerTextArea = document.createElement("textarea");
    footerTextArea.placeholder = `---
### Extracted on {{YYYY-MM-DD HH:mm:ss}}
`;
    footerTextArea.value = this.plugin.settings.footerTemplate;
    footerTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    footerTextArea.rows = 3;
    footerTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.footerTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    footerSetting.infoEl.appendChild(footerTextArea);
    new import_obsidian4.Setting(containerEl).setName("Output to new note").setDesc("If enabled, extracted text will be saved to a new note.").addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.outputToNewNote).onChange(async (value) => {
        this.plugin.settings.outputToNewNote = value;
        await this.plugin.saveSettings();
        this.display();
      })
    );
    if (this.plugin.settings.outputToNewNote) {
      const folderSetting = new import_obsidian4.Setting(containerEl).setName("Note folder path").setDesc("");
      folderSetting.descEl.appendText("Relative to vault root. (e.g., 'OCR Notes')");
      folderSetting.descEl.createEl("br");
      folderSetting.descEl.appendText("Supports {{placeholders}}.");
      folderSetting.addText(
        (text) => text.setPlaceholder("OCR Notes").setValue(this.plugin.settings.noteFolderPath).onChange(async (value) => {
          this.plugin.settings.noteFolderPath = value.trim();
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Note name template").setDesc("Supports {{placeholders}}.").addText(
        (text) => text.setPlaceholder("Extracted OCR {{YYYY-MM-DD}}").setValue(this.plugin.settings.noteNameTemplate).onChange(async (value) => {
          this.plugin.settings.noteNameTemplate = value;
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Append if file exists").setDesc(
        "If enabled, appends to an existing note instead of creating a new one."
      ).addToggle(
        (toggle) => toggle.setValue(this.plugin.settings.appendIfExists).onChange(async (value) => {
          this.plugin.settings.appendIfExists = value;
          await this.plugin.saveSettings();
        })
      );
    }
    containerEl.createEl("hr");
    const descEl = containerEl.createEl("div", {
      cls: "ai-image-ocr__tip"
    });
    containerEl.createEl("hr");
    containerEl.createEl("h3", { text: "Batch image extraction settings" });
    const batchCustomPromptSetting = new import_obsidian4.Setting(containerEl).setName("Custom batched images prompt").setDesc("Optional prompt to send to the model for batch extraction. Leave blank to use the default.");
    const batchCustomPromptTextArea = document.createElement("textarea");
    batchCustomPromptTextArea.placeholder = `e.g., Extract all visible text from each image.`;
    batchCustomPromptTextArea.value = this.plugin.settings.batchCustomPrompt;
    batchCustomPromptTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    batchCustomPromptTextArea.rows = 2;
    batchCustomPromptTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.batchCustomPrompt = e.target.value;
      await this.plugin.saveSettings();
    });
    batchCustomPromptSetting.infoEl.appendChild(batchCustomPromptTextArea);
    const batchHeaderSetting = new import_obsidian4.Setting(containerEl).setName("Batch header template").setDesc("Optional markdown placed above the extraction batch.\nSupports {{placeholders}}.");
    const batchHeaderTextArea = document.createElement("textarea");
    batchHeaderTextArea.placeholder = `## Extracted on {{YYYY-MM-DD HH:mm:ss}}
---`;
    batchHeaderTextArea.value = this.plugin.settings.batchHeaderTemplate;
    batchHeaderTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    batchHeaderTextArea.rows = 3;
    batchHeaderTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.batchHeaderTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    batchHeaderSetting.infoEl.appendChild(batchHeaderTextArea);
    const batchImageHeaderSetting = new import_obsidian4.Setting(containerEl).setName("Image header template").setDesc("Optional markdown placed above the extracted text for each image.\nSupports {{placeholders}}.");
    const batchImageHeaderTextArea = document.createElement("textarea");
    batchImageHeaderTextArea.placeholder = `### Extracted from {{image.name}}
![{{image.name}}]({{image.path}})
`;
    batchImageHeaderTextArea.value = this.plugin.settings.batchImageHeaderTemplate;
    batchImageHeaderTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    batchImageHeaderTextArea.rows = 3;
    batchImageHeaderTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.batchImageHeaderTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    batchImageHeaderSetting.infoEl.appendChild(batchImageHeaderTextArea);
    const batchImageFooterSetting = new import_obsidian4.Setting(containerEl).setName("Image footer template").setDesc("Optional markdown placed below the extracted text for each image.\nSupports {{placeholders}}.");
    const batchImageFooterTextArea = document.createElement("textarea");
    batchImageFooterTextArea.placeholder = `---
`;
    batchImageFooterTextArea.value = this.plugin.settings.batchImageFooterTemplate;
    batchImageFooterTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    batchImageFooterTextArea.rows = 2;
    batchImageFooterTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.batchImageFooterTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    batchImageFooterSetting.infoEl.appendChild(batchImageFooterTextArea);
    const batchFooterSetting = new import_obsidian4.Setting(containerEl).setName("Batch footer template").setDesc("Optional markdown placed below the extraction batch.\nSupports {{placeholders}}.");
    const batchFooterTextArea = document.createElement("textarea");
    batchFooterTextArea.placeholder = `End of Batch Extraction
`;
    batchFooterTextArea.value = this.plugin.settings.batchFooterTemplate;
    batchFooterTextArea.classList.add("ai-image-ocr__template-input", "ai-image-ocr__setting-input-below");
    batchFooterTextArea.rows = 2;
    batchFooterTextArea.addEventListener("change", async (e) => {
      this.plugin.settings.batchFooterTemplate = e.target.value;
      await this.plugin.saveSettings();
    });
    batchFooterSetting.infoEl.appendChild(batchFooterTextArea);
    new import_obsidian4.Setting(containerEl).setName("Output to new note").setDesc("If enabled, batch extracted text will be saved to a new note.").addToggle(
      (toggle) => toggle.setValue(this.plugin.settings.batchOutputToNewNote).onChange(async (value) => {
        this.plugin.settings.batchOutputToNewNote = value;
        await this.plugin.saveSettings();
        this.display();
      })
    );
    if (this.plugin.settings.batchOutputToNewNote) {
      const batchFolderSetting = new import_obsidian4.Setting(containerEl).setName("Batch note folder path").setDesc("");
      batchFolderSetting.descEl.appendText("Applied per image.");
      batchFolderSetting.descEl.createEl("br");
      batchFolderSetting.descEl.appendText("Relative to vault root. (e.g., 'OCR Notes')");
      batchFolderSetting.descEl.createEl("br");
      batchFolderSetting.descEl.appendText("Supports {{placeholders}}.");
      batchFolderSetting.addText(
        (text) => text.setPlaceholder("OCR Notes").setValue(this.plugin.settings.batchNoteFolderPath).onChange(async (value) => {
          this.plugin.settings.batchNoteFolderPath = value.trim();
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Batch note name template").setDesc("Applied per image. Supports {{placeholders}}.").addText(
        (text) => text.setPlaceholder("Batch OCR {{YYYY-MM-DD}}").setValue(this.plugin.settings.batchNoteNameTemplate).onChange(async (value) => {
          this.plugin.settings.batchNoteNameTemplate = value;
          await this.plugin.saveSettings();
        })
      );
      new import_obsidian4.Setting(containerEl).setName("Batch append if file exists").setDesc(
        "If enabled, appends to an existing note instead of creating a new one for batch output."
      ).addToggle(
        (toggle) => toggle.setValue(this.plugin.settings.batchAppendIfExists).onChange(async (value) => {
          this.plugin.settings.batchAppendIfExists = value;
          await this.plugin.saveSettings();
        })
      );
    }
  }
};

// main.ts
var GPTImageOCRPlugin = class extends import_obsidian5.Plugin {
  constructor() {
    super(...arguments);
    __publicField(this, "settings");
  }
  async onload() {
    await this.loadSettings();
    this.addCommand({
      id: "extract-text-from-image",
      name: "Extract text from image",
      callback: async () => {
        const file = await selectImageFile();
        if (!file) {
          new import_obsidian5.Notice("No file selected.");
          return;
        }
        const arrayBuffer = await file.arrayBuffer();
        const base64 = arrayBufferToBase64(arrayBuffer);
        const dims = await getImageDimensionsFromArrayBuffer(arrayBuffer);
        const provider = this.getProvider();
        const providerId = this.settings.provider;
        const modelId = provider.model;
        const providerName = getFriendlyProviderNames(this.settings)[providerId];
        let modelName = FRIENDLY_MODEL_NAMES[modelId] || modelId;
        if (providerId === "ollama" && this.settings.ollamaModelFriendlyName?.trim()) {
          modelName = this.settings.ollamaModelFriendlyName.trim();
        } else if (providerId === "lmstudio" && this.settings.lmstudioModelFriendlyName?.trim()) {
          modelName = this.settings.lmstudioModelFriendlyName.trim();
        } else if (providerId === "custom" && this.settings.customModelFriendlyName?.trim()) {
          modelName = this.settings.customModelFriendlyName.trim();
        }
        const providerType = getProviderType(providerId);
        const notice = new import_obsidian5.Notice(`Using ${providerName} ${modelName}\u2026`, 0);
        try {
          const content = await provider.extractTextFromBase64(base64);
          notice.hide();
          if (content) {
            const editor = this.app.workspace.activeEditor?.editor;
            const extension = file.name.includes(".") ? file.name.split(".").pop() : "";
            const mime = file.type || getImageMimeType(file.name);
            const context = buildOCRContext({
              providerId,
              providerName,
              providerType,
              modelId,
              modelName,
              prompt: this.settings.customPrompt,
              singleImage: {
                name: file.name.replace(/\.[^.]*$/, ""),
                extension: extension || "",
                path: file.name,
                size: file.size,
                mime,
                width: dims?.width,
                height: dims?.height
              }
            });
            await handleExtractedContent(this, content, editor ?? null, context);
          } else {
            new import_obsidian5.Notice("No content returned.");
          }
        } catch (e) {
          notice.hide();
          console.error("OCR failed:", e);
          new import_obsidian5.Notice("Failed to extract text.");
        }
      }
    });
    this.addCommand({
      id: "extract-text-from-embedded-image",
      name: "Extract text from embedded image",
      editorCallback: async (editor, ctx) => {
        const sel = editor.getSelection();
        const embedMatch = sel.match(/!\[\[.*?\]\]/) || sel.match(/!\[.*?\]\(.*?\)/);
        const embed = findRelevantImageEmbed(editor);
        if (!embed) {
          new import_obsidian5.Notice("No image embed found.");
          return;
        }
        const { link, isExternal, embedText } = embed;
        let arrayBuffer = null;
        if (isExternal) {
          try {
            arrayBuffer = await fetchExternalImageAsArrayBuffer(link);
          } catch (e) {
            new import_obsidian5.Notice("Failed to fetch external image.");
            return;
          }
        } else {
          const file = resolveInternalImagePath(this.app, link);
          if (file instanceof import_obsidian5.TFile) {
            arrayBuffer = await this.app.vault.readBinary(file);
          } else {
            new import_obsidian5.Notice("Image file not found in vault.");
            return;
          }
        }
        if (!arrayBuffer) {
          new import_obsidian5.Notice("Could not read image data.");
          return;
        }
        const base64 = arrayBufferToBase64(arrayBuffer);
        const dims = await getImageDimensionsFromArrayBuffer(arrayBuffer);
        const provider = this.getProvider();
        const providerId = this.settings.provider;
        const modelId = provider.model;
        const providerName = getFriendlyProviderNames(this.settings)[providerId];
        let modelName = FRIENDLY_MODEL_NAMES[modelId] || modelId;
        if (providerId === "ollama" && this.settings.ollamaModelFriendlyName?.trim()) {
          modelName = this.settings.ollamaModelFriendlyName.trim();
        } else if (providerId === "lmstudio" && this.settings.lmstudioModelFriendlyName?.trim()) {
          modelName = this.settings.lmstudioModelFriendlyName.trim();
        } else if (providerId === "custom" && this.settings.customModelFriendlyName?.trim()) {
          modelName = this.settings.customModelFriendlyName.trim();
        }
        const providerType = getProviderType(providerId);
        const notice = new import_obsidian5.Notice(
          `Extracting from embed with ${providerName} ${modelName}\u2026`,
          0
        );
        try {
          const content = await provider.extractTextFromBase64(base64);
          notice.hide();
          if (!content) {
            new import_obsidian5.Notice("No content returned.");
            return;
          }
          const embedInfo = parseEmbedInfo(embedText, link);
          const mime = getImageMimeType(embedInfo.path);
          const context = buildOCRContext({
            providerId,
            providerName,
            providerType,
            modelId,
            modelName,
            prompt: this.settings.customPrompt,
            singleImage: {
              name: embedInfo.name,
              extension: embedInfo.extension,
              path: embedInfo.path,
              size: arrayBuffer?.byteLength ?? 0,
              mime,
              width: dims?.width,
              height: dims?.height
            }
          });
          context.embed = embedInfo;
          if (embedMatch && sel === embedMatch[0]) {
            editor.replaceSelection(content);
            return;
          }
          await handleExtractedContent(this, content, editor ?? null, context);
        } catch (e) {
          notice.hide();
          console.error("OCR failed:", e);
          new import_obsidian5.Notice("Failed to extract text.");
        }
      }
    });
    this.addCommand({
      id: "extract-text-from-image-folder",
      name: "Extract text from image folder",
      callback: () => this.extractTextFromImageFolder()
    });
    this.addSettingTab(new GPTImageOCRSettingTab(this.app, this));
  }
  /**
   * Returns the currently selected OCR provider instance based on settings.
   */
  getProvider() {
    const { provider, openaiApiKey, geminiApiKey } = this.settings;
    const name = getFriendlyProviderNames(this.settings)[provider];
    if (provider === "gemini") {
      return new GeminiProvider(
        geminiApiKey,
        "models/gemini-2.5-flash",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "gemini-lite") {
      return new GeminiProvider(
        geminiApiKey,
        "models/gemini-2.5-flash-lite-preview-06-17",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "gemini-pro") {
      return new GeminiProvider(
        geminiApiKey,
        "models/gemini-2.5-pro",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "openai-mini") {
      return new OpenAIProvider(
        openaiApiKey,
        "gpt-4o-mini",
        "https://api.openai.com/v1/chat/completions",
        "openai",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "openai") {
      return new OpenAIProvider(
        openaiApiKey,
        "gpt-4o",
        "https://api.openai.com/v1/chat/completions",
        "openai",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "openai-4.1") {
      return new OpenAIProvider(
        openaiApiKey,
        "gpt-4.1",
        "https://api.openai.com/v1/chat/completions",
        "openai",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "openai-4.1-mini") {
      return new OpenAIProvider(
        openaiApiKey,
        "gpt-4.1-mini",
        "https://api.openai.com/v1/chat/completions",
        "openai",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "openai-4.1-nano") {
      return new OpenAIProvider(
        openaiApiKey,
        "gpt-4.1-nano",
        "https://api.openai.com/v1/chat/completions",
        "openai",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "ollama") {
      return new OpenAIProvider(
        "",
        // no api key
        this.settings.ollamaModel || "llama3.2-vision",
        this.settings.ollamaUrl?.replace(/\/$/, "") || "http://localhost:11434",
        "ollama",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "lmstudio") {
      return new OpenAIProvider(
        "",
        // no api key
        this.settings.lmstudioModel || "gemma3",
        this.settings.lmstudioUrl?.replace(/\/$/, "") || "http://localhost:1234",
        "lmstudio",
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else if (provider === "custom") {
      return new OpenAIProvider(
        this.settings.customApiKey || "",
        this.settings.customApiModel || "gpt-4",
        this.settings.customApiUrl || "https://example.com/v1/chat/completions",
        "openai",
        // use openai-style response
        this.settings.customPrompt?.trim() || DEFAULT_PROMPT_TEXT,
        name
      );
    } else {
      throw new Error("Unknown provider");
    }
  }
  /**
   * Loads plugin settings from disk, merging with defaults.
   */
  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }
  /**
   * Saves current plugin settings to disk.
   */
  async saveSettings() {
    await this.saveData(this.settings);
  }
  /**
   * Collects images from a folder for text extraction
  */
  async extractTextFromImageFolder() {
    const files = await selectFolder();
    if (!files) return;
    const imageFiles = Array.from(files).filter(
      (file) => /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(file.name)
    );
    const prepared = await Promise.all(
      imageFiles.map(async (file) => {
        const arrayBuffer = await file.arrayBuffer();
        const dims = await getImageDimensionsFromArrayBuffer(arrayBuffer);
        return {
          name: file.name,
          base64: arrayBufferToBase64(arrayBuffer),
          mime: file.type,
          size: file.size,
          width: dims?.width,
          height: dims?.height,
          source: file.name
        };
      })
    );
    if (prepared.length === 0) {
      new import_obsidian5.Notice("No valid images could be prepared.");
      return;
    }
    const provider = this.getProvider();
    const providerId = this.settings.provider;
    const modelId = provider.model;
    const providerName = getFriendlyProviderNames(this.settings)[providerId];
    let modelName = FRIENDLY_MODEL_NAMES[modelId] || modelId;
    if (providerId === "ollama" && this.settings.ollamaModelFriendlyName?.trim()) {
      modelName = this.settings.ollamaModelFriendlyName.trim();
    } else if (providerId === "lmstudio" && this.settings.lmstudioModelFriendlyName?.trim()) {
      modelName = this.settings.lmstudioModelFriendlyName.trim();
    } else if (providerId === "custom" && this.settings.customModelFriendlyName?.trim()) {
      modelName = this.settings.customModelFriendlyName.trim();
    }
    const providerType = getProviderType(providerId);
    const notice = new import_obsidian5.Notice(`Extracting text from ${prepared.length} images using ${providerName} ${modelName}\u2026`, 0);
    const batchFormatInstruction = `
For each image, wrap the response using the following format:

--- BEGIN IMAGE: ---
<insert OCR text>
--- END IMAGE ---

Repeat this for each image.
`;
    const userPrompt = this.settings.batchCustomPrompt?.trim() || DEFAULT_BATCH_PROMPT_TEXT;
    const batchPrompt = `${userPrompt}
${batchFormatInstruction}`;
    try {
      let response;
      if (provider.process) {
        response = await provider.process(prepared, batchPrompt);
      } else {
        response = await provider.extractTextFromBase64(prepared[0].base64) ?? "";
      }
      notice.hide();
      const matches = Array.from(
        response.matchAll(/--- BEGIN IMAGE: ---\s*([\s\S]*?)\s*--- END IMAGE ---/g),
        (m) => m[1].trim()
      );
      let contentForFormatting;
      let contextForFormatting;
      if (matches.length > 1) {
        contentForFormatting = matches;
        contextForFormatting = buildOCRContext({
          providerId,
          providerName,
          providerType,
          modelId,
          modelName,
          prompt: batchPrompt,
          images: prepared.map((img) => ({
            name: img.name.replace(/\.[^.]*$/, ""),
            extension: img.name.includes(".") ? img.name.split(".").pop() || "" : "",
            path: img.source,
            size: img.size,
            mime: img.mime || getImageMimeType(img.name),
            width: img.width,
            height: img.height
          }))
        });
      } else {
        contentForFormatting = matches.length === 1 ? matches[0] : response.trim();
        contextForFormatting = buildOCRContext({
          providerId,
          providerName,
          providerType,
          modelId,
          modelName,
          prompt: batchPrompt,
          singleImage: {
            name: prepared[0]?.name.replace(/\.[^.]*$/, ""),
            extension: prepared[0]?.name.includes(".") ? prepared[0]?.name.split(".").pop() || "" : "",
            path: prepared[0]?.source,
            size: prepared[0]?.size,
            mime: prepared[0]?.mime || getImageMimeType(prepared[0]?.name ?? ""),
            width: prepared[0]?.width,
            height: prepared[0]?.height
          }
        });
      }
      const noteNameTemplate = this.settings.batchNoteNameTemplate || this.settings.noteNameTemplate;
      const noteFolderTemplate = this.settings.batchNoteFolderPath || this.settings.noteFolderPath;
      if (Array.isArray(contextForFormatting.images) && (templateHasImagePlaceholder(noteNameTemplate) || templateHasImagePlaceholder(noteFolderTemplate))) {
        for (let i = 0; i < contextForFormatting.images.length; i++) {
          const imgContext = {
            ...contextForFormatting,
            image: contextForFormatting.images[i],
            imageIndex: i + 1,
            imageTotal: contextForFormatting.images.length
          };
          const imgContent = Array.isArray(contentForFormatting) ? contentForFormatting[i] : contentForFormatting;
          await handleExtractedContent(this, imgContent, null, imgContext);
        }
      } else {
        await handleExtractedContent(this, contentForFormatting, null, contextForFormatting);
      }
    } catch (e) {
      notice.hide();
      new import_obsidian5.Notice("Failed to extract text from images.");
      console.error(e);
    }
  }
  async insertOutputToEditor(text) {
    const activeView = this.app.workspace.getActiveViewOfType(import_obsidian5.MarkdownView);
    if (!activeView) {
      new import_obsidian5.Notice("No active editor.");
      return;
    }
    const editor = activeView.editor;
    editor.replaceSelection(text + "\n");
  }
};

/* nosourcemap */