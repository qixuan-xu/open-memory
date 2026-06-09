const today = new Date().toISOString().slice(0, 10);

const byId = (id) => document.getElementById(id);

async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function item(meta, text) {
  const el = document.createElement("div");
  el.className = "item";
  el.innerHTML = `<div class="meta">${meta}</div><div>${escapeHtml(text)}</div>`;
  return el;
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
  const [events, summaries, memories] = await Promise.all([
    request("/events?limit=20"),
    request("/summaries?limit=3"),
    request("/memories?limit=20"),
  ]);

  byId("events").replaceChildren(...events.map((event) =>
    item(`${event.category} / importance ${event.importance}`, event.text)
  ));
  byId("summaries").replaceChildren(...summaries.map((summary) =>
    item(summary.day, summary.summary)
  ));
  byId("memories").replaceChildren(...memories.map((memory) =>
    item(`${memory.memory_type} / confidence ${memory.confidence}`, memory.text)
  ));
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
  const data = await request("/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  byId("answer").textContent = data.answer;
});

refresh().catch((error) => {
  byId("answer").textContent = error.message;
});
