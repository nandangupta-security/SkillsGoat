/* Scanner panel: "Check with a scanner", shared by the Quiz and Scan pages.
 *
 * Talks to the optional /api/* endpoints of `python3 goat.py serve`. If the
 * server has no scanner support (or no scanner is installed) the panel says so
 * and the page keeps working; nothing here is required by Learn or Quiz.
 *
 * All scanner text is inserted with textContent, never as HTML.
 */
(function () {
  var STYLE = [
    ".sg-scan { margin-top: 18px; }",
    ".sg-scan h3 { margin-top: 0; }",
    ".sg-scan .sg-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 10px 0; }",
    ".sg-scan select { background: var(--card); color: var(--text); border: 1px solid var(--card-border); border-radius: 8px; padding: 8px 10px; max-width: 100%; }",
    ".sg-scan .sg-note { color: var(--muted); font-size: .88rem; margin: 4px 0; }",
    ".sg-scan .sg-outcome { display: inline-block; padding: 3px 10px; border-radius: 99px; font-weight: 700; font-size: .85rem; letter-spacing: .03em; text-transform: uppercase; border: 1px solid var(--card-border); }",
    ".sg-scan .sg-outcome.good { color: var(--good); border-color: var(--good); }",
    ".sg-scan .sg-outcome.bad { color: var(--bad); border-color: var(--bad); }",
    ".sg-scan .sg-outcome.err { color: #ffcf6b; border-color: #ffcf6b; }",
    ".sg-scan ul.sg-findings { list-style: none; padding: 0; margin: 10px 0; }",
    ".sg-scan ul.sg-findings li { padding: 8px 0; border-top: 1px solid var(--card-border); }",
    ".sg-scan .sg-sev { display: inline-block; min-width: 4.6em; text-align: center; padding: 1px 6px; margin-right: 8px; border-radius: 6px; font-size: .75rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--card-border); color: var(--muted); }",
    ".sg-scan .sg-sev.high, .sg-scan .sg-sev.critical { color: var(--bad); border-color: var(--bad); }",
    ".sg-scan .sg-sev.medium { color: #ffcf6b; border-color: #ffcf6b; }",
    ".sg-scan .sg-where { color: var(--muted); font-size: .85rem; }",
    ".sg-scan .sg-msg { color: var(--muted); font-size: .85rem; margin: 4px 0 0; }",
    ".sg-scan details { margin-top: 10px; }",
    ".sg-scan details pre { max-height: 360px; overflow: auto; }"
  ].join("\n");

  var scannersPromise = null, tokenPromise = null;

  function injectStyle() {
    if (document.getElementById("sg-scan-style")) return;
    var s = document.createElement("style");
    s.id = "sg-scan-style";
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function loadScanners() {
    if (!scannersPromise) {
      scannersPromise = fetch("/api/scanners", { cache: "no-store" })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .catch(function () { return { unavailable: true, profiles: [], scanners: [] }; });
    }
    return scannersPromise;
  }

  function loadToken(fresh) {
    if (!tokenPromise || fresh) {
      tokenPromise = fetch("/api/token", { cache: "no-store" })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function (d) { return d.token; });
    }
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
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  // truth is the corpus label ("malicious" | "benign"); verdict is the scanner's.
  function outcomeOf(truth, result) {
    if (result.verdict === "error") {
      return { cls: "err", label: "Scan failed",
        text: "The scan did not finish, so there is no verdict. This is not a clean result." };
    }
    var flagged = result.verdict === "flagged";
    if (truth === "malicious") {
      return flagged
        ? { cls: "good", label: "Caught", text: "The scanner flagged this skill, matching the answer." }
        : { cls: "bad", label: "Missed", text: "The scanner called this skill clean, but it is malicious. Scanners miss things like this, which is why labeled examples matter." };
    }
    return flagged
      ? { cls: "bad", label: "False alarm", text: "The scanner flagged a skill that is actually harmless." }
      : { cls: "good", label: "Correct", text: "The scanner agrees this skill is harmless." };
  }

  function panel(opts) {
    var el = opts.el;                       // the page's element helper
    injectStyle();
    var body = el("div", {}, [el("p", { class: "sg-note", text: "Looking for scanners…" })]);
    var intro = el("p", { class: "sg-note", text: "Run a real scanner on this skill and compare it with the answer above." });
    var root = el("div", { class: "panel sg-scan" }, [
      el("h3", { text: "Check with a scanner" }),
      intro,
      body
    ]);

    function say(text) { body.textContent = ""; body.appendChild(el("p", { class: "sg-note", text: text })); }

    loadScanners().then(function (data) {
      if (data.unavailable) {
        return say("Scanner checks need the SkillsGoat server. Start it with: python3 goat.py serve");
      }
      var profiles = data.profiles || [];
      var ready = profiles.filter(function (p) { return p.ready; });
      if (!ready.length) {
        var why = profiles.length ? profiles[0].detail : "no profiles are configured";
        return say("No scanner is ready. " + why);
      }

      var select = el("select", { "aria-label": "Scanner profile" });
      var names = {};                       // scanner id -> display name
      profiles.forEach(function (p) { names[p.scanner] = p.scanner_name || p.scanner; });
      // Name the scanner once, in the intro. Only repeat it per option when
      // there is more than one scanner and it is needed to tell them apart.
      var distinct = Object.keys(names).map(function (k) { return names[k]; });
      var multi = distinct.length > 1;
      intro.textContent = "Run " + (multi ? "a real scanner" : distinct[0]) + " on this skill and compare it with the answer above.";
      profiles.forEach(function (p) {
        var name = multi ? names[p.scanner] + " · " + p.label : p.label;
        var o = el("option", { value: p.id, text: p.ready ? name : name + " (not ready: " + p.detail + ")" });
        if (!p.ready) o.disabled = true;
        select.appendChild(o);
      });
      select.value = ready[0].id;

      var privacy = el("p", { class: "sg-note" });
      function showPrivacy() {
        var p = profiles.filter(function (x) { return x.id === select.value; })[0];
        privacy.textContent = p && p.sends_data_off_machine
          ? "This sends the skill's text to " + (p.provider || "a remote service") + "."
          : "Runs on your machine. Nothing is sent anywhere.";
      }
      select.addEventListener("change", showPrivacy);
      showPrivacy();

      var out = el("div", { "aria-live": "polite" });
      var go = el("button", { text: "Run scan" });
      go.addEventListener("click", function () {
        go.disabled = true;
        out.textContent = "";
        out.appendChild(el("p", { class: "sg-note", text: "Scanning… the first scan of a skill can take 10 to 20 seconds." }));
        runScan(opts.entryId, select.value).then(function (res) {
          render(out, res, select.value);
        }).catch(function (e) {
          render(out, { verdict: "error", error: "could not reach the scan service (" + e.message + ")" }, select.value);
        }).then(function () { go.disabled = false; go.textContent = "Scan again"; });
      });

      body.textContent = "";
      body.appendChild(el("div", { class: "sg-row" }, [select, go]));
      body.appendChild(privacy);
      body.appendChild(out);

      function render(host, res, profileId) {
        host.textContent = "";
        var o = outcomeOf(opts.verdict, res);
        host.appendChild(el("p", {}, [
          el("span", { class: "sg-outcome " + o.cls, text: o.label }),
          el("span", { text: "  " + o.text })
        ]));
        if (res.verdict === "error") {
          host.appendChild(el("p", { class: "sg-msg", text: res.error || "unknown error" }));
          return;
        }
        // Informational findings (e.g. a missing license) are left out of the
        // list to keep it readable; they remain in the raw output below.
        var shown = (res.findings || []).filter(function (f) { return f.severity !== "info"; });
        var bits = [(multi ? (names[res.scanner] || res.scanner) + " " : "") + (res.scanner_version ? "v" + res.scanner_version : ""),
                    "severity: " + (shown.length ? shown[0].severity : "none"), res.duration_seconds + "s"];
        if (res.tokens && res.tokens.total_tokens) bits.push(res.tokens.total_tokens + " tokens");
        if (res.cached) bits.push("from cache");
        host.appendChild(el("p", { class: "sg-note", text: bits.join(" · ") }));

        var list = el("ul", { class: "sg-findings" });
        shown.forEach(function (f) {
          var where = f.file ? f.rule + " · " + f.file + (f.line ? ":" + f.line : "") : f.rule;
          if (f.also_at && f.also_at.length) where += " (also reported at " + f.also_at.join(", ") + ")";
          var li = el("li", {}, [
            el("span", { class: "sg-sev " + f.severity, text: f.severity }),
            el("strong", { text: f.title }),
            el("div", { class: "sg-where", text: where })
          ]);
          if (f.message) li.appendChild(el("p", { class: "sg-msg", text: f.message }));
          list.appendChild(li);
        });
        if (!shown.length) {
          host.appendChild(el("p", { class: "sg-note", text: "No findings above informational level." }));
        } else {
          host.appendChild(list);
        }
        if (res.verdict === "clean") {
          host.appendChild(el("p", { class: "sg-note", text: "No findings is not a guarantee that a skill is safe. Scanners only look for patterns they know." }));
        }
        if (res.raw) {
          host.appendChild(el("details", {}, [
            el("summary", { text: "Show raw scanner output" }),
            el("pre", { text: JSON.stringify(res.raw, null, 2) })
          ]));
        }
      }
    });
    return root;
  }

  window.SkillsGoatScanner = { panel: panel, outcomeOf: outcomeOf };
})();
