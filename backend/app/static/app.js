const today = new Date().toISOString().slice(0, 10);

const byId = (id) => document.getElementById(id);
const savedLanguage = localStorage.getItem("open-memory-language");
let language = savedLanguage === "zh" ? "zh" : "en";

const text = {
  en: {
    subtitle: "Local-first AI memory cockpit with user-reviewed capture",
    summarize: "Summarize Today",
    reflect: "Reflect",
    capture: "Capture",
    capturePlaceholder: "Drop a memory, transcript, idea, decision, or todo...",
    save: "Save Memory",
    inbox: "Memory Inbox",
    timeline: "Timeline",
    dailySummary: "Daily Summary",
    longTermMemory: "Long-Term Memory",
    ask: "Ask",
    askPlaceholder: "Ask your memory...",
    llm: "LLM",
    llmPlaceholder: "none, ollama:qwen2.5, lmstudio:local-model, openai:gpt-4.1",
    askButton: "Ask",
    keep: "Keep",
    promote: "Promote",
    ignore: "Ignore",
    delete: "Delete",
    importance: "importance",
    confidence: "confidence",
    thinking: "Thinking...",
    askError: "Ask failed",
  },
  zh: {
    subtitle: "本地优先、由你审核的 AI 记忆控制台",
    summarize: "总结今天",
    reflect: "反思",
    capture: "捕捉",
    capturePlaceholder: "写下一条记忆、转录、想法、决定或待办...",
    save: "保存记忆",
    inbox: "记忆收件箱",
    timeline: "时间线",
    dailySummary: "每日总结",
    longTermMemory: "长期记忆",
    ask: "提问",
    askPlaceholder: "向你的记忆提问...",
    llm: "模型",
    llmPlaceholder: "none、ollama:qwen2.5、lmstudio:local-model、openai:gpt-4.1",
    askButton: "提问",
    keep: "保留",
    promote: "提升为长期记忆",
    ignore: "忽略",
    delete: "删除",
    importance: "重要性",
    confidence: "置信度",
    thinking: "正在思考...",
    askError: "提问失败",
  },
};

function t(key) {
  return text[language][key] || text.en[key] || key;
}

function applyLanguage(nextLanguage = language) {
  language = nextLanguage === "zh" ? "zh" : "en";
  localStorage.setItem("open-memory-language", language);
  document.documentElement.lang = language === "zh" ? "zh-Hans" : "en";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  byId("langEn").classList.toggle("active", language === "en");
  byId("langZh").classList.toggle("active", language === "zh");
}

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let message = await res.text();
    try {
      const parsed = JSON.parse(message);
      message = parsed.detail || message;
    } catch {
      // Keep the plain response text.
    }
    throw new Error(message);
  }
  return res.json();
}

function item(meta, text) {
  const el = document.createElement("div");
  el.className = "item";
  el.innerHTML = `<div class="meta">${meta}</div><div>${escapeHtml(text)}</div>`;
  return el;
}

function eventItem(event, { reviewControls = false } = {}) {
  const el = item(
    `${event.category} / ${event.review_status} / ${t("importance")} ${event.importance}`,
    event.text,
  );
  if (!reviewControls) return el;

  const actions = document.createElement("div");
  actions.className = "item-actions";
  actions.append(
    actionButton(t("keep"), () => reviewEvent(event.id, { review_status: "kept" })),
    actionButton(t("promote"), () => promoteEvent(event.id)),
    actionButton(t("ignore"), () => reviewEvent(event.id, { review_status: "ignored" }), "secondary"),
    actionButton(t("delete"), () => deleteEvent(event.id), "danger"),
  );
  el.append(actions);
  return el;
}

function actionButton(label, handler, variant = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = variant;
  button.addEventListener("click", handler);
  return button;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

async function refresh() {
  const [inbox, events, summaries, memories] = await Promise.all([
    request("/events/inbox?limit=20"),
    request("/events?limit=20"),
    request("/summaries?limit=3"),
    request("/memories?limit=20"),
  ]);

  byId("inbox").replaceChildren(...inbox.map((event) =>
    eventItem(event, { reviewControls: true })
  ));
  byId("events").replaceChildren(...events.map((event) =>
    eventItem(event)
  ));
  byId("summaries").replaceChildren(...summaries.map((summary) =>
    item(summary.day, summary.summary)
  ));
  byId("memories").replaceChildren(...memories.map((memory) =>
    item(`${memory.memory_type} / ${t("confidence")} ${memory.confidence}`, memory.text)
  ));
}

async function reviewEvent(id, body) {
  await request(`/events/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  await refresh();
}

async function promoteEvent(id) {
  await request(`/events/${id}/promote`, { method: "POST" });
  await refresh();
}

async function deleteEvent(id) {
  await request(`/events/${id}`, { method: "DELETE" });
  await refresh();
}

byId("save").addEventListener("click", async () => {
  const text = byId("eventText").value.trim();
  if (!text) return;
  await request("/events", {
    method: "POST",
    body: JSON.stringify({ text, source: "dashboard" }),
  });
  byId("eventText").value = "";
  await refresh();
});

byId("summarize").addEventListener("click", async () => {
  await request(`/summaries/${today}`, { method: "POST" });
  await refresh();
});

byId("reflect").addEventListener("click", async () => {
  const data = await request(`/reflections/${today}`, { method: "POST" });
  byId("answer").textContent = data.reflection;
  await refresh();
});

byId("ask").addEventListener("click", async () => {
  const question = byId("question").value.trim();
  if (!question) return;
  const llm = byId("llm").value.trim();
  const askButton = byId("ask");
  askButton.disabled = true;
  byId("answer").textContent = t("thinking");
  try {
    const data = await request("/query", {
      method: "POST",
      body: JSON.stringify(llm ? { question, llm } : { question }),
    });
    byId("answer").textContent = data.answer;
  } catch (error) {
    byId("answer").textContent = `${t("askError")}: ${error.message}`;
  } finally {
    askButton.disabled = false;
  }
});

byId("langEn").addEventListener("click", async () => {
  applyLanguage("en");
  await refresh();
});

byId("langZh").addEventListener("click", async () => {
  applyLanguage("zh");
  await refresh();
});

applyLanguage();
refresh().catch((error) => {
  byId("answer").textContent = error.message;
});
