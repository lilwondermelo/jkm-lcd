const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const statusText = $("statusText");
const toastEl = $("toast");
const SEGMENTS = 10;
const CLOCK_FRAME_SECONDS = 2.0;

const MODE_LABEL = { temp: "CPU", gpu: "GPU", clock: "часы", volume: "громкость" };
const MODE_UNIT = { temp: "°C", gpu: "°C", clock: "", volume: "" };
const ANIM_LABEL = {
  wave: "волна", pingpong: "пинг-понг", breathe: "дыхание",
  cputemp: "шкала CPU", gputemp: "шкала GPU", volume: "шкала громкости",
  eq: "эквалайзер", none: "пусто",
};

let server = {
  version: "?", mode: "temp", animation: "wave", display_on: true,
  animation_params: {}, sensors: {}, sound: {},
};
let busy = false;
let toastTimer = 0;
let scanStream = null;
let scanLoop = 0;

function setText(id, text) {
  const el = $(id);
  if (el) el.textContent = text;
}

function toast(text, bad = false) {
  toastEl.textContent = text;
  toastEl.classList.toggle("bad", bad);
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2200);
}

function baseUrl() {
  return localStorage.getItem("jkm-server") || "";
}

function token() {
  return localStorage.getItem("jkm-token") || "";
}

async function api(path, body) {
  const headers = { "Content-Type": "application/json", "X-JKM-Token": token() };
  const opts = body
    ? { method: "POST", headers, body: JSON.stringify(body) }
    : { cache: "no-store", headers };
  const r = await fetch(baseUrl() + path, opts);
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  if (!r.ok) {
    const msg = (data && (data.error || data.detail)) || `${path}: ${r.status}`;
    const err = new Error(msg);
    err.status = r.status;
    throw err;
  }
  return data;
}

function vibrate(ms = 12) {
  if (navigator.vibrate) navigator.vibrate(ms);
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

/* ---------- превью ---------- */

const clampPct = (x) => Math.max(0, Math.min(100, Math.round(x)));

function tempBar(temp, p) {
  if (temp === null || temp === undefined) return 0;
  const lo = p.min_c || 20;
  const hi = p.max_c || 90;
  return clampPct((temp - lo) / (hi - lo) * 100);
}

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

function paintPreview(nowSec) {
  const s = server.sensors || {};
  const snd = server.sound || {};
  const mode = server.mode;
  const anim = server.animation;
  const params = server.animation_params || {};
  const screenOff = !server.display_on;
  let load = 0;

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
    } else if (anim === "volume") load = snd.volume || 0;
    else if (anim === "eq") load = snd.level || 0;
    else if (anim === "breathe") {
      load = breatheOn(nowSec, params.breathe || {}) ? 100 : 0;
    } else if (anim === "none" && mode !== "clock") load = 0;
  }

  let value = s.temp;
  let unit = "°C";
  let tab = "center";
  if (mode === "gpu") { value = s.gpu; }
  if (mode === "clock") {
    const d = new Date();
    const hoursPhase = (nowSec % (2 * CLOCK_FRAME_SECONDS)) < CLOCK_FRAME_SECONDS;
    value = hoursPhase ? d.getHours() : d.getMinutes();
    unit = "";
    tab = hoursPhase ? "left" : "right";
    if (anim === "none") load = Math.round((d.getMinutes() / 59) * 100);
  }
  if (mode === "volume") { value = snd.volume; unit = ""; }

  setText("p-big", screenOff ? "" : fmt(value));
  setText("p-big-unit", screenOff ? "" : unit);
  setText("p-mode", mode === "clock" ? (tab === "left" ? "часы" : "минуты") : MODE_LABEL[mode]);
  setText("p-anim", anim === "eq"
    ? `эквалайзер ${snd.level || 0}%`
    : ANIM_LABEL[anim]);

  const tabIndex = tab === "left" ? 0 : tab === "right" ? 2 : 1;
  $("p-tabs").querySelectorAll("span").forEach((el, i) => {
    el.classList.toggle("on", !screenOff && i === tabIndex);
  });

  const lit = Math.round(load / 100 * SEGMENTS);
  $("p-bar").querySelectorAll("span").forEach((seg, i) => {
    seg.classList.toggle("on", !screenOff && i < lit);
  });
  $("device").classList.toggle("dark", screenOff);
  setText("previewState", screenOff ? "экран выключен" : (s.connected ? "на связи" : "нет связи"));
  $("previewState").classList.toggle("bad", !s.connected);
}

/* ---------- состояние ---------- */

function applyStatus(data) {
  if (!data) return;
  server = { ...server, ...data, sensors: data.sensors || {}, sound: data.sound || {} };
  document.body.classList.remove("unpaired");

  setText("v-temp", fmt(server.sensors.temp));
  setText("v-gpu", fmt(server.sensors.gpu));
  setText("v-power", fmt(server.sensors.power, 1));
  setText("v-load", fmt(server.sensors.load));
  setText("ver", `v${server.version}`);

  setActive("data-mode", server.mode);
  setActive("data-anim", server.animation);

  const online = !!server.sensors.connected;
  statusEl.classList.toggle("online", online);
  statusEl.classList.toggle("offline", !online);
  setText("statusText", online ? "на связи" : "нет связи");

  const on = server.display_on !== false;
  const btn = $("powerBtn");
  btn.textContent = on ? "Выключить" : "Включить";
  btn.classList.toggle("off", !on);
  setText("powerHint", on ? "включён — идут кадры" : "выключен — кадры не идут");
}

async function refresh() {
  if (!token()) { showLogin(); return; }
  try {
    applyStatus(await api("/api/status"));
  } catch (e) {
    statusEl.classList.remove("online");
    statusEl.classList.add("offline");
    if (e.status === 401) {
      setText("statusText", "нужна привязка");
      showLogin();
    } else {
      setText("statusText", "сервер недоступен");
    }
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

/* ---------- вход по QR ---------- */

function showLogin() {
  document.body.classList.add("unpaired");
  $("loginScreen").hidden = false;
  stopScan();
}
function hideLogin() {
  document.body.classList.remove("unpaired");
  $("loginScreen").hidden = true;
}

async function pairWith(url, code) {
  const origin = new URL(url).origin;
  const r = await fetch(origin + "/api/pair", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, label: "PWA" }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.status);
  localStorage.setItem("jkm-server", origin);
  localStorage.setItem("jkm-token", data.token);
  hideLogin();
  refresh();
}

async function handleQrText(text) {
  try {
    const u = new URL(text);
    const code = u.searchParams.get("code") || "";
    if (!/^\d{4}$/.test(code)) throw new Error("в QR нет кода привязки");
    setText("scanHint", "привязываю…");
    await pairWith(u.toString(), code);
    toast("компьютер привязан");
  } catch (e) {
    setText("scanHint", `не получилось: ${e.message}`);
  }
}

async function startScan() {
  const video = $("scanVideo");
  setText("scanHint", "");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setText("scanHint", "камера недоступна — открой ссылку из QR на телефоне");
    return;
  }
  try {
    scanStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" }, audio: false,
    });
  } catch (e) {
    setText("scanHint", "нет доступа к камере: " + e.message);
    return;
  }
  video.srcObject = scanStream;
  video.hidden = false;
  await video.play();
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const tick = () => {
    if (!scanStream) return;
    if (video.videoWidth) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const found = window.jsQR ? window.jsQR(img.data, img.width, img.height) : null;
      if (found && found.data) {
        stopScan();
        handleQrText(found.data);
        return;
      }
    }
    scanLoop = requestAnimationFrame(tick);
  };
  tick();
}

function stopScan() {
  cancelAnimationFrame(scanLoop);
  if (scanStream) {
    scanStream.getTracks().forEach((t) => t.stop());
    scanStream = null;
  }
  const video = $("scanVideo");
  if (video) { video.hidden = true; video.srcObject = null; }
}

$("scanBtn").addEventListener("click", startScan);

/* ---------- настройки ---------- */

const modal = $("settingsModal");
$("settingsBtn").addEventListener("click", () => {
  $("setServer").value = baseUrl() || location.origin;
  modal.hidden = false;
});
$("closeSettings").addEventListener("click", () => { modal.hidden = true; });
modal.addEventListener("click", (e) => { if (e.target === modal) modal.hidden = true; });

$("doUnpair").addEventListener("click", () => {
  localStorage.removeItem("jkm-token");
  modal.hidden = true;
  showLogin();
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

(function boot() {
  const params = new URLSearchParams(location.search);
  const code = params.get("code");
  if (token()) {
    hideLogin();
    refresh();
  } else if (code) {
    pairWith(location.origin, code).catch((e) => {
      setText("scanHint", "не привязалось: " + e.message);
      showLogin();
    });
    history.replaceState(null, "", "/");
  } else {
    showLogin();
  }
})();

setInterval(refresh, 1500);
(function loop() {
  paintPreview(performance.now() / 1000);
  requestAnimationFrame(loop);
})();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
