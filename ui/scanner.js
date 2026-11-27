/* Scanner cards: "Check with real scanners", shared by the Quiz and Scan pages.
 *
 * Talks to the optional /api/* endpoints of `python3 goat.py serve`. If the
 * server has no scanner support (or no scanner is installed) the panel says so
 * and the page keeps working; nothing here is required by Learn or Quiz.
 *
 * One card per scanner profile. Results appear inside the card.
 * All scanner text is inserted with textContent, never as HTML.
 */
(function () {
  var STYLE = [
    ".sg-scan { margin-top: 18px; }",
    ".sg-scan h3 { margin-top: 0; }",
    ".sg-scan .sg-note { color: var(--muted); font-size: .88rem; margin: 4px 0; }",
    ".sg-scan .sg-top { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin: 8px 0 14px; }",
    ".sg-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }",
    ".sg-card { background: var(--code-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px; transition: border-color .15s, box-shadow .15s; }",
    ".sg-card:hover { border-color: #2c6f66; }",
    ".sg-card.off { opacity: .6; }",
    ".sg-card.busy { border-color: var(--accent2); box-shadow: 0 0 18px rgba(91,140,255,.18); }",
    ".sg-card-h { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 6px; }",
    ".sg-card-h strong { color: #fff; }",
    ".sg-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--good); box-shadow: 0 0 8px var(--good); flex: none; }",
    ".sg-card.off .sg-dot { background: var(--muted); box-shadow: none; }",
    ".sg-card.busy .sg-dot { background: #ffcf6b; box-shadow: 0 0 8px #ffcf6b; animation: sgpulse 1s ease-in-out infinite; }",
    "@keyframes sgpulse { 50% { opacity: .35; } }",
    "@media (prefers-reduced-motion: reduce) { .sg-card.busy .sg-dot { animation: none; } }",
    ".sg-chip { font-size: .72rem; padding: 1px 8px; border-radius: 99px; border: 1px solid var(--card-border); color: var(--accent2); }",
    ".sg-card-a { margin: 10px 0 4px; }",
    ".sg-card button.small, .sg-scan button.small { padding: 6px 14px; font-size: .88rem; }",
    ".sg-banner { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--card-border); font-size: 1rem; }",
    ".sg-banner .sg-icon { font-size: 1.15rem; font-weight: 700; }",
    ".sg-banner.good { color: var(--good); border-color: var(--good); background: rgba(125,255,196,.08); }",
    ".sg-banner.bad { color: var(--bad); border-color: var(--bad); background: rgba(255,107,129,.08); }",
    ".sg-banner.err { color: #ffcf6b; border-color: #ffcf6b; background: rgba(255,207,107,.08); }",
    ".sg-scorebox { display: flex; align-items: center; gap: 10px; margin: 8px 0; font-size: .85rem; color: var(--muted); }",
    ".sg-bar { flex: 1; height: 8px; border-radius: 99px; background: #12202a; overflow: hidden; }",
    ".sg-bar i { display: block; height: 100%; }",
    ".sg-bar.ok i { background: var(--good); } .sg-bar.warn i { background: #ffcf6b; } .sg-bar.bad i { background: var(--bad); }",
    ".sg-scan ul.sg-findings { list-style: none; padding: 0; margin: 8px 0; }",
    ".sg-scan ul.sg-findings li { padding: 8px 0; border-top: 1px solid var(--card-border); }",
    ".sg-sev { display: inline-block; min-width: 4.6em; text-align: center; padding: 1px 6px; margin-right: 8px; border-radius: 6px; font-size: .72rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--card-border); color: var(--muted); }",
    ".sg-sev.high, .sg-sev.critical { color: var(--bad); border-color: var(--bad); }",
    ".sg-sev.medium { color: #ffcf6b; border-color: #ffcf6b; }",
    ".sg-where { color: var(--muted); font-size: .8rem; }",
    ".sg-msg { color: var(--muted); font-size: .82rem; margin: 4px 0 0; }",
    ".sg-scan details { margin-top: 8px; }",
    ".sg-scan details pre { max-height: 300px; overflow: auto; font-size: .78rem; }",
    ".sg-link { display: inline-block; padding: 6px 14px; font-size: .88rem; font-weight: 600; border-radius: 8px; border: 1px solid var(--card-border); color: var(--text); text-decoration: none; }",
    ".sg-link:hover { border-color: var(--accent); }",
    ".sg-actions { display: flex; flex-wrap: wrap; gap: 8px; }",
    ".sg-label { margin-top: 14px; padding: 10px 12px; border-left: 3px solid var(--accent2); background: var(--code-bg); border-radius: 0 8px 8px 0; font-size: .9rem; }",
    ".sg-label strong { color: #fff; }"
  ].join("\n");

  var scannersPromise = null, tokenPromise = null;

  function injectStyle() {
    if (document.getElementById("sg-scan-style")) return;
    var s = document.createElement("style");
    s.id = "sg-scan-style";
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function getJSON(path) {
    return fetch(path, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function loadScanners() {
    if (!scannersPromise) {
      scannersPromise = getJSON("/api/scanners")
        .catch(function () { return { unavailable: true, profiles: [], scanners: [] }; });
    }
    return scannersPromise;
  }

  function loadToken(fresh) {
    if (!tokenPromise || fresh) tokenPromise = getJSON("/api/token").then(function (d) { return d.token; });
    return tokenPromise;
  }

  function runScan(entryId, profileId, retried) {
    return loadToken(false).then(function (token) {
      return fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-SkillsGoat-Token": token },
        body: JSON.stringify({ entry: entryId, profile: profileId })
      });
    }).then(function (r) {
      if (r.status === 403 && !retried) {          // server restarted: new token
        return loadToken(true).then(function () { return runScan(entryId, profileId, true); });
      }
      if (r.status === 429) return r.json();       // server is busy: show its own message
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  // truth is the corpus label ("malicious" | "benign"); the verdict is the scanner's.
  function outcomeOf(truth, result) {
    if (result.verdict === "error") {
      return { cls: "err", icon: "⚠", label: "Scan failed",
        text: "The scan did not finish, so there is no verdict. This is not a clean result." };
    }
    var flagged = result.verdict === "flagged";
    if (truth === "malicious") {
      return flagged
        ? { cls: "good", icon: "✓", label: "Caught", text: "The scanner flagged this skill, matching the answer." }
        : { cls: "bad", icon: "✗", label: "Missed", text: "The scanner called this skill clean, but it is malicious. Scanners miss things like this, which is why labeled examples matter." };
    }
    return flagged
      ? { cls: "bad", icon: "!", label: "False alarm", text: "The scanner flagged a skill that is actually harmless." }
      : { cls: "good", icon: "✓", label: "Correct", text: "The scanner agrees this skill is harmless." };
  }

  var ADVICE = { "SAFE": "allow it", "CAUTION": "warn the user, not block it", "DO NOT INSTALL": "block it" };

  function panel(opts) {
    var el = opts.el;                       // the page's element helper
    injectStyle();
    var body = el("div", {}, [el("p", { class: "sg-note", text: "Looking for scanners…" })]);
    var root = el("div", { class: "panel sg-scan" }, [
      el("h3", { text: "Check with real scanners" }),
      body
    ]);
    function say(text) { body.textContent = ""; body.appendChild(el("p", { class: "sg-note", text: text })); }

    loadScanners().then(function (data) {
      if (data.unavailable) {
        return say("Scanner checks need the SkillsGoat server. Start it with: python3 goat.py serve");
      }
      var profiles = data.profiles || [];
      if (!profiles.length) return say("No scanner profiles are configured.");

      var label = el("div", { class: "sg-label" });
      label.hidden = true;
      var bench = el("p", { class: "sg-note" });

      function onResult(p, res) {
        label.hidden = false;
        label.textContent = "";
        label.appendChild(el("strong", { text: "Our label: " + opts.verdict + ". " }));
        if (opts.why) label.appendChild(el("span", { text: opts.why }));
        if (res.verdict === "error") return;
        getJSON("/api/results").then(function (d) {
          var c = (d.coverage || {})[p.id];
          if (c) bench.textContent = "Added to the benchmark: " + (p.scanner_name || p.scanner) + " · " + p.label +
            ", " + c.scanned + " of " + c.total + " skills scanned. See the Benchmark page.";
        }).catch(function () {});
      }

      var cards = profiles.map(function (p) { return makeCard(p, opts, onResult); });

      var allBtn = el("button", { class: "ghost small", text: "Run all static scans" });
      var runnable = cards.filter(function (c) { return c.profile.ready && c.profile.mode === "static"; });
      if (!runnable.length) allBtn.disabled = true;
      allBtn.addEventListener("click", function () {
        allBtn.disabled = true;
        runnable.reduce(function (chain, c) { return chain.then(function () { return c.run(); }); }, Promise.resolve())
          .then(function () { allBtn.disabled = false; });
      });

      var grid = el("div", { class: "sg-cards" }, cards.map(function (c) { return c.root; }));
      body.textContent = "";
      body.appendChild(el("div", { class: "sg-top" }, [
        el("p", { class: "sg-note", text: "Run real scanners on this skill and compare them with the answer." }),
        el("div", { class: "sg-actions" }, [allBtn, el("a", { class: "sg-link", href: "benchmark.html", text: "View benchmark ▸" })])
      ]));
      body.appendChild(grid);
      body.appendChild(label);
      body.appendChild(bench);
    });
    return root;

    function makeCard(p, ctx, notify) {
      var el = ctx.el;
      var busy = false, timer = null;
      var out = el("div", { "aria-live": "polite" });
      var btn = el("button", { class: "small", text: "Run" });
      if (!p.ready) btn.disabled = true;
      var privacy = p.sends_data_off_machine
        ? "Sends this skill's text to " + (p.provider || "a remote service") + "."
        : "Runs on your machine. Nothing is sent anywhere.";
      var card = el("div", { class: "sg-card" + (p.ready ? "" : " off") }, [
        el("div", { class: "sg-card-h" }, [
          el("span", { class: "sg-dot" }),
          el("strong", { text: p.scanner_name || p.scanner }),
          el("span", { class: "sg-chip", text: p.label })
        ]),
        el("p", { class: "sg-note", text: privacy }),
        p.ready ? null : el("p", { class: "sg-note", text: "Not ready: " + p.detail }),
        el("div", { class: "sg-card-a" }, [btn]),
        out
      ]);

      function run() {
        if (busy || !p.ready) return Promise.resolve();
        busy = true; btn.disabled = true; card.classList.add("busy");
        out.textContent = "";
        var note = el("p", { class: "sg-note", text: "Scanning…" });
        out.appendChild(note);
        return getJSON("/api/scan-status?profile=" + encodeURIComponent(p.id))
          .catch(function () { return { wait_seconds: 0 }; })
          .then(function (st) {
            var wait = st.wait_seconds || 0, t0 = Date.now();
            function tick() {
              var secs = (Date.now() - t0) / 1000;
              note.textContent = secs < wait
                ? "Waiting " + Math.ceil(wait - secs) + "s so the free plan's rate limit isn't hit…"
                : "Scanning… " + Math.round(secs - wait) + "s";
            }
            tick(); timer = setInterval(tick, 500);
            return runScan(ctx.entryId, p.id);
          })
          .catch(function (e) {
            return { verdict: "error", error: "could not reach the scan service (" + e.message + ")" };
          })
          .then(function (res) {
            clearInterval(timer);
            render(res);
            busy = false; btn.disabled = false; btn.textContent = "Run again";
            card.classList.remove("busy");
            notify(p, res);
          });
      }
      btn.addEventListener("click", run);

      function render(res) {
        out.textContent = "";
        var o = outcomeOf(ctx.verdict, res);
        out.appendChild(el("div", { class: "sg-banner " + o.cls }, [
          el("span", { class: "sg-icon", text: o.icon }), el("strong", { text: o.label })
        ]));
        out.appendChild(el("p", { class: "sg-note", text: o.text }));
        if (res.verdict === "error") {
          out.appendChild(el("p", { class: "sg-msg", text: res.error || "unknown error" }));
          return;
        }
        // Informational findings (e.g. a missing license) stay out of the list;
        // they remain in the raw output below.
        var shown = (res.findings || []).filter(function (f) { return f.severity !== "info"; });
        var graded = res.score !== null && res.score !== undefined;
        if (graded) {
          var tier = res.recommendation === "SAFE" ? "ok" : (res.recommendation === "CAUTION" ? "warn" : "bad");
          out.appendChild(el("div", { class: "sg-scorebox" }, [
            el("div", { class: "sg-bar " + tier }, [el("i", { style: "width:" + Math.max(2, Math.min(100, res.score)) + "%" })]),
            el("span", { text: (res.recommendation ? res.recommendation + " · " : "") + res.score + "/100" })
          ]));
          if (ADVICE[res.recommendation]) {
            out.appendChild(el("p", { class: "sg-note", text: "The scanner's own advice: " + ADVICE[res.recommendation] + "." }));
          }
        }
        var bits = [res.scanner_version ? "v" + res.scanner_version : ""];
        if (graded && res.overall_severity) bits.push("overall: " + res.overall_severity);
        bits.push("worst finding: " + (shown.length ? shown[0].severity : "none"), res.duration_seconds + "s");
        if (res.tokens && res.tokens.total_tokens) bits.push(res.tokens.total_tokens + " tokens");
        if (res.cached) bits.push("from cache");
        out.appendChild(el("p", { class: "sg-note", text: bits.filter(Boolean).join(" · ") }));

        if (!shown.length) {
          out.appendChild(el("p", { class: "sg-note", text: "No findings above informational level." }));
        } else {
          var list = el("ul", { class: "sg-findings" });
          var more = el("button", { class: "ghost small", text: "Show all " + shown.length + " findings" });
          shown.forEach(function (f, i) {
            var where = f.file ? f.rule + " · " + f.file + (f.line ? ":" + f.line : "") : f.rule;
            if (f.also_at && f.also_at.length) where += " (also at " + f.also_at.join(", ") + ")";
            var li = el("li", {}, [
              el("span", { class: "sg-sev " + f.severity, text: f.severity }),
              el("strong", { text: f.title }),
              el("div", { class: "sg-where", text: where })
            ]);
            if (f.message) li.appendChild(el("p", { class: "sg-msg", text: f.message }));
            if (i >= 3) li.hidden = true;
            list.appendChild(li);
          });
          out.appendChild(list);
          if (shown.length > 3) {
            more.addEventListener("click", function () {
              Array.prototype.forEach.call(list.children, function (li) { li.hidden = false; });
              more.remove();
            });
            out.appendChild(more);
          }
        }
        if (res.verdict === "clean") {
          out.appendChild(el("p", { class: "sg-note", text: "No findings is not a guarantee that a skill is safe. Scanners only look for patterns they know." }));
        }
        if (res.raw) {
          out.appendChild(el("details", {}, [
            el("summary", { text: "Show raw scanner output" }),
            el("pre", { text: JSON.stringify(res.raw, null, 2) })
          ]));
        }
      }
      return { root: card, run: run, profile: p };
    }
  }

  window.SkillsGoatScanner = { panel: panel, outcomeOf: outcomeOf };
})();
