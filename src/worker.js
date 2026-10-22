// 40000steps.com — Worker
// Strona to pliki statyczne z ./public. Worker obsługuje wyłącznie /api/*:
// zapis anonimowych odpowiedzi z ankiety „Jak szukasz pomocy”.
// Odpowiedzi trafiają do Durable Object (SQLite) w jurysdykcji UE.
// Nie zapisujemy adresu IP, nagłówków ani dokładnej godziny — tylko datę.

import { DurableObject } from "cloudflare:workers";

const EDITIONS = {
  1: {
    // 21 października – 30 listopada 2026 (czas polski)
    start: Date.parse("2026-10-21T00:00:00+02:00"),
    end: Date.parse("2026-11-30T23:59:59+01:00"),
  },
};
const GRACE_MS = 60 * 60 * 1000; // godzina zapasu na wysłanie formularza otwartego przed końcem
const VERSION = "v1";
const MAX_BODY = 20000;
const MAX_TEXT = 2000;

// Dozwolone klucze odpowiedzi i ich kształt
const SHAPE = {
  q1: "one", q2: "many", q3: "one", q4: "one", q5: "many", q6: "one",
  q7: "groups", q8: "one", q9: "one", q10: "one", q11: "one",
  q12: "many", q13: "many", q14: "one", q15: "text", meta: "groups",
};
const GROUP_KEYS = { q7: ["ter", "psy"], meta: ["wiek", "plec", "miejsce"] };

export class SurveyStore extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.sql.exec(
      "CREATE TABLE IF NOT EXISTS responses (" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT, edition INTEGER NOT NULL, " +
        "day TEXT NOT NULL, version TEXT NOT NULL, answers TEXT NOT NULL)"
    );
  }
  async add(edition, day, version, answers) {
    this.sql.exec(
      "INSERT INTO responses (edition, day, version, answers) VALUES (?, ?, ?, ?)",
      edition, day, version, answers
    );
    return true;
  }
  async all() {
    return this.sql.exec("SELECT id, edition, day, version, answers FROM responses ORDER BY id").toArray();
  }
  async ping() {
    return true;
  }
}

function store(env) {
  // Lokalny `wrangler dev` nie obsługuje jurysdykcji; LOCAL_DEV ustawiany jest tylko w .dev.vars.
  const ns = env.LOCAL_DEV === "1" ? env.SURVEY : env.SURVEY.jurisdiction("eu");
  return ns.get(ns.idFromName("ankieta"));
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-robots-tag": "noindex",
    },
  });
}

function isStr(v, max) {
  return typeof v === "string" && v.length > 0 && v.length <= max;
}

// Zwraca oczyszczone odpowiedzi albo null, jeśli coś nie pasuje
function clean(answers) {
  if (!answers || typeof answers !== "object" || Array.isArray(answers)) return null;
  const out = {};
  for (const [k, v] of Object.entries(answers)) {
    const shape = SHAPE[k];
    if (!shape) return null;
    if (v === null || v === undefined || v === "") continue;
    if (shape === "one") {
      if (!isStr(v, 200)) return null;
      out[k] = v;
    } else if (shape === "many") {
      if (!Array.isArray(v) || v.length > 10 || !v.every((x) => isStr(x, 200))) return null;
      if (v.length) out[k] = v;
    } else if (shape === "text") {
      if (typeof v !== "string" || v.length > MAX_TEXT) return null;
      if (v.trim()) out[k] = v.trim();
    } else if (shape === "groups") {
      if (typeof v !== "object" || Array.isArray(v)) return null;
      const g = {};
      for (const [gk, gv] of Object.entries(v)) {
        if (!GROUP_KEYS[k].includes(gk)) return null;
        if (gv === null || gv === undefined || gv === "") continue;
        if (!isStr(gv, 200)) return null;
        g[gk] = gv;
      }
      if (Object.keys(g).length) out[k] = g;
    }
  }
  return out;
}

function warsawDay(ms) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Warsaw" }).format(new Date(ms));
}

async function submit(request, env, url) {
  const origin = request.headers.get("origin");
  if (!origin || new URL(origin).host !== url.host) return json({ ok: false, error: "origin" }, 403);
  if (!(request.headers.get("content-type") || "").includes("application/json")) {
    return json({ ok: false, error: "type" }, 415);
  }
  const text = await request.text();
  if (text.length > MAX_BODY) return json({ ok: false, error: "size" }, 413);
  let body;
  try { body = JSON.parse(text); } catch { return json({ ok: false, error: "json" }, 400); }

  if (body.hp) return json({ ok: true }); // pułapka na boty: udajemy sukces, nic nie zapisujemy
  if (body.consent !== true) return json({ ok: false, error: "consent" }, 400);
  const ed = EDITIONS[body.edition];
  if (!ed) return json({ ok: false, error: "edition" }, 400);
  const now = Date.now();
  if (now < ed.start || now > ed.end + GRACE_MS) return json({ ok: false, error: "closed" }, 409);

  const answers = clean(body.answers);
  if (!answers) return json({ ok: false, error: "answers" }, 400);
  if (!Object.keys(answers).length) return json({ ok: false, error: "empty" }, 400);

  await store(env).add(body.edition, warsawDay(now), VERSION, JSON.stringify(answers));
  return json({ ok: true });
}

function csvCell(v) {
  const s = v === undefined || v === null ? "" : Array.isArray(v) ? v.join(" | ") : String(v);
  return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

async function exportAll(request, env, url) {
  const token = env.EXPORT_TOKEN;
  if (!token) return json({ ok: false }, 404); // eksport wyłączony, dopóki nie ustawisz sekretu
  const auth = request.headers.get("authorization") || "";
  if (auth !== "Bearer " + token) return json({ ok: false }, 401);

  const rows = await store(env).all();
  if (url.searchParams.get("format") === "json") {
    return json(rows.map((r) => ({ ...r, answers: JSON.parse(r.answers) })));
  }
  const cols = ["q1", "q2", "q3", "q4", "q5", "q6", "q7.ter", "q7.psy", "q8", "q9", "q10", "q11",
    "q12", "q13", "q14", "q15", "meta.wiek", "meta.plec", "meta.miejsce"];
  const lines = [["id", "edycja", "dzien", "wersja"].concat(cols).join(",")];
  for (const r of rows) {
    const a = JSON.parse(r.answers);
    const vals = cols.map((c) => {
      const [k, sub] = c.split(".");
      return csvCell(sub ? (a[k] || {})[sub] : a[k]);
    });
    lines.push([r.id, r.edition, r.day, r.version].concat(vals).join(","));
  }
  return new Response("﻿" + lines.join("\r\n"), {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": 'attachment; filename="ankieta-jak-szukasz-pomocy.csv"',
      "cache-control": "no-store",
      "x-robots-tag": "noindex",
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/ankieta" && request.method === "POST") return submit(request, env, url);
    if (url.pathname === "/api/ankieta/eksport" && request.method === "GET") return exportAll(request, env, url);
    if (url.pathname === "/api/ankieta/status" && request.method === "GET") {
      await store(env).ping();
      const ed = EDITIONS[1], now = Date.now();
      return json({ ok: true, open: now >= ed.start && now <= ed.end });
    }
    if (url.pathname.startsWith("/api/")) return json({ ok: false }, 404);
    return env.ASSETS.fetch(request);
  },
};
