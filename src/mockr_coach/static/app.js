"use strict";
const $ = (id) => document.getElementById(id);
const stages = {dsa: ["approach", "code", "complexity"], design: ["requirements", "estimates", "api", "data-model", "scaling", "trade-offs"], behavioural: ["situation", "task", "action", "result", "reflection"]};
let config, current, historyData;
let recognition;
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
async function api(path, payload) {
  const options = payload === undefined ? {} : {method: "POST", headers: {"Content-Type": "application/json", "X-Mockr-Token": config.token}, body: JSON.stringify(payload)};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function error(err) { $("status").textContent = err.message; }
function questionOptions() {
  $("question").replaceChildren(...config.questions.filter(q => q.kind === $("kind").value).map(q => {
    const option = node("option", q.title + " / " + q.topic);
    option.value = q.id;
    return option;
  }));
}
function renderTranscript(transcript) {
  $("transcript").replaceChildren(...transcript.flatMap(t => [node("h4", t.stage), node("p", t.prompt || "Candidate answer"), node("pre", t.answer)]));
  $("transcript-box").hidden = false;
}
function showScore(record) {
  const box = $("scorecard");
  box.hidden = false;
  box.replaceChildren(node("p", "EVIDENCE SCORECARD", "eyebrow"), node("h2", `${record.scorecard.overall.toFixed(2)} / 5`, "score"));
  if (record.title) box.append(node("p", record.title));
  if (record.execution) box.append(node("p", `Hidden tests: ${record.execution.passed}/${record.execution.total} · ${record.execution.status}`));
  for (const criterion of record.scorecard.criteria) {
    const row = node("article", undefined, "criterion");
    row.append(node("h3", `${criterion.id.replaceAll("_", " ")} · ${criterion.score}/5`));
    const dots = node("div", undefined, "score-dots");
    dots.setAttribute("aria-hidden", "true");
    for (let n = 1; n <= 5; n++) dots.append(node("span", "", n <= criterion.score ? "filled" : ""));
    row.append(dots, node("blockquote", criterion.quote), node("p", criterion.feedback));
    box.append(row);
  }
  renderTranscript(record.transcript);
}
function renderTrend() {
  const records = historyData.trend.filter(r => r.kind === $("trend-kind").value);
  const container = $("trend");
  container.replaceChildren();
  if (!records.length) { container.append(node("p", "No rounds of this type yet.", "hint")); return; }
  const plot = node("div", undefined, "trend-plot");
  plot.setAttribute("role", "img");
  plot.setAttribute("aria-label", records.map((r,i) => `Round ${i+1}: ${r.score}/5 (${r.provider})`).join("; "));
  for (const r of records) {
    const column = node("div", undefined, "trend-column");
    const bar = node("span", undefined, "trend-bar");
    // Five classes avoid inline style under the strict Content Security Policy.
    bar.classList.add(`level-${Math.max(1,Math.min(5,Math.round(r.score)))}`);
    bar.title = `${r.created_at}: ${r.score}/5 (${r.provider})`;
    column.append(bar, node("small", String(r.score)));
    plot.append(column);
  }
  container.append(plot, node("p", "Oldest → newest · hover for date and provider", "hint"));
}
async function refreshHistory() {
  historyData = await api("/api/history");
  $("count").textContent = historyData.count;
  $("topics").replaceChildren();
  if (!historyData.weak_topics.length) $("topics").append(node("p", "No scores yet. Complete a round to find your next focus.", "hint"));
  for (const topic of historyData.weak_topics.slice(0,6)) {
    const row = node("div", undefined, "topic");
    row.append(node("span", `${topic.topic} · ${topic.kind}`), node("strong", `${topic.mean.toFixed(2)} / 5`), node("small", `${topic.sessions} round${topic.sessions === 1 ? "" : "s"}`));
    $("topics").append(row);
  }
  renderTrend();
  $("history").replaceChildren();
  if (!historyData.sessions.length) $("history").append(node("p", "Your completed rounds will appear here.", "hint"));
  for (const session of historyData.sessions) {
    const button = node("button", `${session.title} · ${session.score}/5`, "history-item");
    button.disabled = Boolean(current && !current.done);
    button.append(node("small", `${session.kind} / ${session.provider} / ${new Date(session.created_at).toLocaleDateString()}`));
    button.onclick = async () => {
      try { showScore(await api("/api/session?id=" + encodeURIComponent(session.id))); $("scorecard").scrollIntoView({block: "start"}); }
      catch (err) { error(err); }
    };
    $("history").append(button);
  }
}
function renderRound() {
  $("round").hidden = current.done;
  $("start-form").hidden = !current.done;
  $("round-title").textContent = current.done ? "Choose your next round" : current.title;
  $("prompt").textContent = current.prompt;
  $("stages").replaceChildren(...stages[current.kind].map(stage => {
    const item = node("li", stage);
    if (stage === current.stage) item.setAttribute("aria-current", "step");
    return item;
  }));
  $("dictate").disabled = !Recognition || current.stage === "code";
  if (current.done) showScore(current);
  else renderTranscript(current.transcript);
}
function stopVoice() {
  if (recognition) recognition.stop();
  if (window.speechSynthesis) window.speechSynthesis.cancel();
}
$("kind").onchange = questionOptions;
$("trend-kind").onchange = renderTrend;
$("start-form").onsubmit = async event => {
  event.preventDefault();
  const button = $("start-form").querySelector("button");
  button.disabled = true;
  try {
    stopVoice();
    current = await api("/api/start", {question_id: $("question").value});
    $("scorecard").hidden = true; $("answer").value = ""; $("status").textContent = "";
    renderRound(); await refreshHistory(); $("answer").focus();
  } catch (err) { error(err); }
  finally { button.disabled = false; }
};
$("answer-form").onsubmit = async event => {
  event.preventDefault(); stopVoice(); $("send").disabled = true;
  $("status").textContent = current.stage === "code" ? "Running hidden tests in the OS sandbox…" : "Reading your answer…";
  try {
    current = await api("/api/answer", {id: current.id, answer: $("answer").value});
    $("answer").value = ""; $("status").textContent = current.done ? "Round saved locally." : "";
    renderRound(); await refreshHistory();
    if (!current.done) $("answer").focus();
  } catch (err) { error(err); }
  finally { $("send").disabled = false; }
};
$("speak").disabled = !window.speechSynthesis;
$("speak").onclick = () => {
  stopVoice();
  const utterance = new SpeechSynthesisUtterance($("prompt").textContent);
  utterance.lang = "en-US"; window.speechSynthesis.speak(utterance);
};
$("dictate").disabled = !Recognition;
$("dictate").title = Recognition ? "Starts microphone only when clicked" : "Speech recognition is unavailable; use typed answers";
$("dictate").onclick = () => {
  stopVoice(); recognition = new Recognition(); recognition.lang = "en-US"; recognition.interimResults = false;
  recognition.onstart = () => { $("status").textContent = "Listening… Your answer will not be sent automatically."; };
  recognition.onresult = event => { $("answer").value += ($("answer").value ? " " : "") + event.results[0][0].transcript; };
  recognition.onerror = event => { $("status").textContent = `Speech recognition: ${event.error}. You can type your answer instead.`; };
  recognition.onend = () => { if ($("status").textContent.startsWith("Listening")) $("status").textContent = "Dictation stopped. Review your answer before sending."; };
  recognition.start();
};
$("stop-voice").onclick = stopVoice;
window.addEventListener("pagehide", stopVoice);
(async () => { try { config = await api("/api/config"); $("provider").textContent = config.provider === "mock" ? "OFFLINE MOCK · NOT AN LLM" : "OPENAI-COMPATIBLE JUDGE"; questionOptions(); await refreshHistory(); } catch (err) { error(err); } })();
