const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const statusText = $("statusText");
const toastEl = $("toast");

const SEGMENTS = 10;

const MODE_UNIT = { temp: "°C", gpu: "°C", clock: "", volume: "" };
const MODE_LABEL = { temp: "CPU", gpu: "GPU", clock: "часы", volume: "громкость" };
const CLOCK_FRAME_SECONDS = 2.0;
const ANIM_LABEL = {
  wave: "волна", pingpong: "пинг-понг", breathe: "дыхание",
  cputemp: "шкала CPU", gputemp: "шкала GPU",
  volume: "шкала громкости", eq: "эквалайзер", none: "пусто",
};

let server = {
  version: "?",
  mode: "temp",
  animation: "none",
  display_on: true,
  animation_params: {},
  sensors: {},
};
let busy = false;
let toastTimer = 0;

function toast(text, bad = false) {
  toastEl.textContent = text;
  toastEl.classList.toggle("bad", bad);
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2200);
}

async function api(path, body) {
  const token = localStorage.getItem("jkm-token") || "";
  const headers = { "Content-Type": "application/json", "X-JKM-Token": token };
  const opts = body
    ? { method: "POST", headers, body: JSON.stringify(body) }
    : { cache: "no-store", headers };
  const r = await fetch(path, opts);
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  if (!r.ok) {
    const msg = (data && (data.error || data.detail)) || `${path}: ${r.status}`;
    throw new Error(msg);
  }
  return data;
}

function vibrate(ms = 12) {
  if (navigator.vibrate) navigator.vibrate(ms);
}

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function fmt(v, digits = 0) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return "—";
  const n = Number(v);
  return digits ? n.toFixed(digits) : String(Math.round(n));
}

function setActive(attr, value) {
  document.querySelectorAll(`[${attr}]`).forEach((b) => {
    b.classList.toggle("active", b.getAttribute(attr) === value);
  });
}

/* ---------- превью панели: те же тайминги, что в server/animations.py ---------- */

function clampPct(x) { return Math.max(0, Math.min(100, Math.round(x))); }

function waveLoad(t, p) {
  const steps = p.steps || SEGMENTS;
  const step = p.step_seconds || 0.2;
  const hold = p.hold_seconds || 0.15;
  const gap = p.gap_seconds || 0.35;
  const period = p.period || (steps * step + hold + gap);
  const phase = t % period;
  const fill = steps * step;
  if (phase >= fill + hold) return 0;
  if (phase >= fill) return 100;
  return Math.max(10, Math.min(100, Math.floor(phase / step + 1) * Math.round(100 / steps)));
}

function pingpongLoad(t, p) {
  const steps = p.steps || SEGMENTS;
  const step = p.step_seconds || 0.18;
  const hold = p.hold_seconds || 0.15;
  const gap = p.gap_seconds || 0.3;
  const up = steps * step;
  const period = p.period || (2 * up + 2 * hold + gap);
  let phase = t % period;
  if (phase < up) {
    return Math.max(10, Math.min(100, Math.floor(phase / step + 1) * Math.round(100 / steps)));
  }
  phase -= up;
  if (phase < hold) return 100;
  phase -= hold;
  if (phase < up) {
    const left = steps - Math.floor(phase / step);
    return Math.max(0, Math.min(90, left * Math.round(100 / steps)));
  }
  return 0;
}

function breatheOn(t, p) {
  const on = p.on_seconds || 1.4;
  const period = p.period || (on + (p.off_seconds || 0.9));
  return (t % period) < on;
}

function tempBar(temp, p) {
  if (temp === null || temp === undefined) return 0;
  const lo = p.min_c || 20;
  const hi = p.max_c || 90;
  return clampPct((temp - lo) / (hi - lo) * 100);
}

function paintPreview(nowSec) {
  const s = server.sensors || {};
  const mode = server.mode;
  const anim = server.animation;
  const params = server.animation_params || {};
  const snd = server.sound || {};

  const screenOff = !server.display_on;
  let load = clampPct(s.load || 0);
  let blackout = false;

  if (!screenOff) {
    if (anim === "wave") load = waveLoad(nowSec, params.wave || {});
    else if (anim === "pingpong") load = pingpongLoad(nowSec, params.pingpong || {});
    else if (anim === "cputemp" || anim === "gputemp") {
      const p = params[anim] || {};
      const value = anim === "cputemp" ? s.temp : s.gpu;
      load = tempBar(value, p);
      const alert = p.alert_c || 80;
      const period = p.alert_period || 1.6;
      if (value >= alert && (nowSec % period) >= period / 2) load = 0;
    }
    else if (anim === "volume") load = snd.volume || 0;
    else if (anim === "eq") load = snd.level || 0;
    else if (anim === "none" && mode !== "clock") {
      load = 0;
    } else if (anim === "breathe") {
      // На реальном LCD дыхание мигает только нижней шкалой.
      load = breatheOn(nowSec, params.breathe || {}) ? 100 : 0;
    }
  } else {
    blackout = true;
    load = 0;
  }

  let value = mode === "gpu" ? s.gpu : s.temp;
  if (mode === "volume") {
    value = snd.volume;  // шкала живёт своей жизнью, здесь просто цифра
  }
  if (mode === "clock") {
    const d = new Date();
    value = (nowSec % (2 * CLOCK_FRAME_SECONDS)) < CLOCK_FRAME_SECONDS
      ? d.getHours() : d.getMinutes();
    if (anim === "none") load = Math.round((d.getMinutes() / 59) * 100);
  }
  setText("p-big", blackout ? "" : fmt(value));
  setText("p-big-unit", blackout ? "" : (MODE_UNIT[mode] || ""));
  setText("p-mode", MODE_LABEL[mode] || mode);
  setText("p-anim", anim === "eq"
    ? `эквалайзер ${(snd.level || 0)}%`
    : (ANIM_LABEL[anim] || anim));

  let tabs = server.tab || "center";
  if (mode === "clock") {
    tabs = (nowSec % (2 * CLOCK_FRAME_SECONDS)) < CLOCK_FRAME_SECONDS ? "left" : "right";
    setText("p-mode", tabs === "left" ? "часы" : "минуты");
  }
  const tabIndex = tabs === "left" ? 0 : tabs === "center" ? 1 : 2;
  $("p-tabs").querySelectorAll("span").forEach((t, i) => {
    t.classList.toggle("on", !blackout && i === tabIndex);
  });

  const lit = Math.round(load / 100 * SEGMENTS);
  $("p-bar").querySelectorAll("span").forEach((seg, i) => {
    seg.classList.toggle("on", !blackout && i < lit);
  });
  $("device").classList.toggle("dark", screenOff);
  $("previewState").textContent = screenOff ? "экран выключен"
    : (s.connected ? "на связи" : "нет связи с кулером");
  $("previewState").classList.toggle("bad", !s.connected);
}

/* ---------- состояние ---------- */

function applyStatus(s) {
  if (!s) return;
  server = { ...server, ...s, sensors: s.sensors || {} };
  setText("v-temp", fmt(server.sensors.temp));
  setText("v-power", fmt(server.sensors.power, 1));
  setText("v-load", fmt(server.sensors.load));
  setText("v-gpu", fmt(server.sensors.gpu));
  setText("v-clock", fmt(server.sensors.clock));
  setText("ver", `v${server.version}`);

  setActive("data-mode", server.mode);
  setActive("data-anim", server.animation);

  const online = !!server.sensors.connected;
  statusEl.classList.toggle("online", online);
  statusEl.classList.toggle("offline", !online);
  statusText.textContent = online
    ? `online · ${server.sensors.port || "ttyACM"}`
    : "нет связи с кулером";

  const on = server.display_on !== false;
  const btn = $("powerBtn");
  btn.textContent = on ? "Выключить экран" : "Включить экран";
  btn.classList.toggle("off", !on);
  $("powerHint").textContent = on
    ? "Включён — идут кадры с датчиками."
    : "Выключен — кадры не отправляются, экран гаснет.";
}

async function refresh() {
  try {
    applyStatus(await api("/api/status"));
  } catch (e) {
    statusEl.classList.remove("online");
    statusEl.classList.add("offline");
    statusText.textContent = "сервер недоступен";
  }
}

async function command(path, body, okText) {
  if (busy) return;
  busy = true;
  vibrate();
  try {
    const res = await api(path, body);
    if (res && res.mode) server.mode = res.mode;
    if (res && res.animation) server.animation = res.animation;
    if (res && typeof res.display_on === "boolean") server.display_on = res.display_on;
    setActive("data-mode", server.mode);
    setActive("data-anim", server.animation);
    if (okText) toast(okText);
    await refresh();
  } catch (e) {
    toast(`не применилось: ${e.message}`, true);
    await refresh();
  } finally {
    busy = false;
  }
}

document.querySelectorAll("[data-mode]").forEach((b) => {
  b.addEventListener("click", () => command("/api/mode", { mode: b.getAttribute("data-mode") }));
});

document.querySelectorAll("[data-anim]").forEach((b) => {
  b.addEventListener("click", () => command("/api/animation", { animation: b.getAttribute("data-anim") }));
});

$("powerBtn").addEventListener("click", () => {
  const next = !(server.display_on !== false);
  command("/api/display", { on: next }, next ? "экран включён" : "экран выключен");
});

const modal = $("settingsModal");
$("settingsBtn").addEventListener("click", () => {
  $("setServer").value = serverBase();
  modal.hidden = false;
});
$("closeSettings").addEventListener("click", () => { modal.hidden = true; });
modal.addEventListener("click", (e) => { if (e.target === modal) modal.hidden = true; });

function serverBase() {
  return location.origin.startsWith("http") ? location.origin : "http://192.168.31.100:8090";
}

$("saveServer").addEventListener("click", () => {
  const url = $("setServer").value.trim().replace(/\/+$/, "");
  if (!url.startsWith("http")) { toast("нужен адрес вида http://host:8090", true); return; }
  localStorage.setItem("jkm-server", url);
  toast("адрес сохранён");
  hardReload();
});

$("doPair").addEventListener("click", async () => {
  const code = $("setCode").value.trim();
  if (code.length !== 4) { toast("введи 4 цифры с компьютера", true); return; }
  try {
    const r = await fetch("/api/pair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, label: "PWA" }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || r.status);
    localStorage.setItem("jkm-token", data.token);
    toast("компьютер привязан");
    modal.hidden = true;
    refresh();
  } catch (e) { toast(`не привязалось: ${e.message}`, true); }
});

async function hardReload() {
  try {
    if ("serviceWorker" in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map((r) => r.unregister()));
    }
    if (window.caches) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
  } catch (e) { /* не критично */ }
  location.replace(`/?v=${Date.now()}`);
}
$("doReload").addEventListener("click", hardReload);

/* ---------- запуск ---------- */

refresh();
setInterval(refresh, 1500);

(function loop() {
  paintPreview(performance.now() / 1000);
  requestAnimationFrame(loop);
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
