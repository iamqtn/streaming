import concurrent.futures as cf
from datetime import datetime, timezone
from typing import Dict, List

import requests
from flask import Flask, jsonify, render_template_string, Response

DOMAINS = [
    # Dev & package registries
    "github.com",
    "npmjs.com",
    "pypi.org",
    "hub.docker.com",
    # APIs & tools
    "api.github.com",
    "httpbin.org",
    "openai.com",
    # CDN / infra
    "cdnjs.cloudflare.com",
    "jsdelivr.net",
    "unpkg.com",
    # Monitoring sanity checks
    "cloudflare.com",
    "google.com",
]

TIMEOUT = 5
MAX_WORKERS = 12
REFRESH_MS = 30_000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    )
}


def check_site(domain: str) -> Dict[str, str]:
    url = f"https://{domain}"
    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if 200 <= r.status_code < 400:
            status = "OK"
        else:
            status = "KO"
        code = str(r.status_code)
    except requests.Timeout:
        status, code = "DOWN", "timeout"
    except requests.ConnectionError:
        status, code = "DOWN", "unreachable"
    except requests.RequestException as e:
        status, code = "DOWN", type(e).__name__
    return {"domain": domain, "status": status, "code": code}


app = Flask(__name__)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Status Checker</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
      background: #0d1117;
      color: #c9d1d9;
      min-height: 100vh;
      padding: 2rem 1rem;
    }

    .wrapper {
      max-width: 640px;
      margin: 0 auto;
    }

    header {
      margin-bottom: 2rem;
    }

    header h1 {
      font-size: 1.1rem;
      font-weight: 600;
      color: #e6edf3;
      letter-spacing: .02em;
    }

    #last-updated {
      font-size: .75rem;
      color: #6e7681;
      margin-top: .35rem;
    }

    .controls {
      display: flex;
      gap: .5rem;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      align-items: center;
    }

    .filter-btn {
      background: #161b22;
      border: 1px solid #30363d;
      color: #8b949e;
      font-family: inherit;
      font-size: .75rem;
      padding: .3rem .75rem;
      border-radius: 4px;
      cursor: pointer;
      transition: all .15s;
    }
    .filter-btn:hover, .filter-btn.active {
      background: #21262d;
      border-color: #58a6ff;
      color: #e6edf3;
    }

    #search {
      margin-left: auto;
      background: #161b22;
      border: 1px solid #30363d;
      color: #c9d1d9;
      font-family: inherit;
      font-size: .75rem;
      padding: .3rem .75rem;
      border-radius: 4px;
      outline: none;
      width: 160px;
      transition: border-color .15s;
    }
    #search:focus { border-color: #58a6ff; }
    #search::placeholder { color: #6e7681; }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    thead th {
      text-align: left;
      font-size: .7rem;
      color: #6e7681;
      text-transform: uppercase;
      letter-spacing: .08em;
      padding: .5rem .75rem;
      border-bottom: 1px solid #21262d;
      cursor: pointer;
      user-select: none;
    }
    thead th:hover { color: #c9d1d9; }
    thead th .sort-arrow { margin-left: .3rem; opacity: .4; }
    thead th.sorted .sort-arrow { opacity: 1; color: #58a6ff; }

    tbody tr {
      border-bottom: 1px solid #161b22;
      transition: background .15s;
    }
    tbody tr:hover { background: #161b22; }

    td {
      padding: .6rem .75rem;
      font-size: .82rem;
    }

    td.domain a {
      color: #58a6ff;
      text-decoration: none;
      font-weight: 500;
    }
    td.domain a:hover { text-decoration: underline; }

    td.status { text-align: center; }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      font-size: .7rem;
      font-weight: 600;
      letter-spacing: .04em;
      padding: .2rem .55rem;
      border-radius: 3px;
    }
    .badge.OK   { background: rgba(35,134,54,.18); color: #3fb950; border: 1px solid rgba(63,185,80,.25); }
    .badge.KO   { background: rgba(210,153,34,.18); color: #d29922; border: 1px solid rgba(210,153,34,.25); }
    .badge.DOWN { background: rgba(248,81,73,.18);  color: #f85149; border: 1px solid rgba(248,81,73,.25); }

    .dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
    .OK .dot   { background: #3fb950; }
    .KO .dot   { background: #d29922; }
    .DOWN .dot { background: #f85149; }

    td.code { color: #6e7681; font-size: .75rem; }

    td.copy-cell { text-align: right; }
    .copy-btn {
      background: none;
      border: none;
      color: #6e7681;
      cursor: pointer;
      font-size: .75rem;
      padding: .2rem .4rem;
      border-radius: 3px;
      font-family: inherit;
      transition: color .15s;
    }
    .copy-btn:hover { color: #c9d1d9; }

    #toast {
      position: fixed;
      bottom: 1.5rem;
      left: 50%;
      transform: translateX(-50%);
      background: #21262d;
      border: 1px solid #30363d;
      color: #e6edf3;
      font-size: .78rem;
      padding: .5rem 1.1rem;
      border-radius: 5px;
      pointer-events: none;
      opacity: 0;
      transition: opacity .2s;
      z-index: 99;
    }
    #toast.show { opacity: 1; }

    .summary {
      display: flex;
      gap: 1.25rem;
      margin-bottom: 1rem;
      font-size: .75rem;
    }
    .summary span { color: #6e7681; }
    .summary b { font-weight: 600; }
    .summary .ok   { color: #3fb950; }
    .summary .ko   { color: #d29922; }
    .summary .down { color: #f85149; }
  </style>
</head>
<body>
<div class="wrapper">
  <header>
    <h1>Status Checker</h1>
    <div id="last-updated">Loading…</div>
  </header>

  <div class="summary" id="summary"></div>

  <div class="controls">
    <button class="filter-btn active" data-filter="ALL">All</button>
    <button class="filter-btn" data-filter="OK">OK</button>
    <button class="filter-btn" data-filter="KO">KO</button>
    <button class="filter-btn" data-filter="DOWN">Down</button>
    <input id="search" type="text" placeholder="Filter domains…">
  </div>

  <table id="status-table">
    <thead>
      <tr>
        <th data-col="domain">Domain <span class="sort-arrow">↕</span></th>
        <th data-col="status" style="text-align:center">Status <span class="sort-arrow">↕</span></th>
        <th data-col="code">HTTP <span class="sort-arrow">↕</span></th>
        <th></th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<div id="toast">Copied!</div>

<script>
  let allRows = [];
  let sortCol = 'domain', sortAsc = true;
  let filterStatus = 'ALL';
  let searchQuery = '';

  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      allRows = await res.json();
      document.getElementById('last-updated').textContent =
        'Last checked: ' + new Date().toLocaleTimeString();
      render();
    } catch (e) {
      document.getElementById('last-updated').textContent = 'Error fetching status.';
    }
  }

  function render() {
    let rows = [...allRows];

    // Filter by status
    if (filterStatus !== 'ALL') rows = rows.filter(r => r.status === filterStatus);

    // Filter by search
    if (searchQuery) rows = rows.filter(r =>
      r.domain.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Sort
    rows.sort((a, b) => {
      let va = a[sortCol] || '', vb = b[sortCol] || '';
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });

    // Summary
    const total = allRows.length;
    const okCount   = allRows.filter(r => r.status === 'OK').length;
    const koCount   = allRows.filter(r => r.status === 'KO').length;
    const downCount = allRows.filter(r => r.status === 'DOWN').length;
    document.getElementById('summary').innerHTML =
      `<span><b>${total}</b> domains</span>` +
      `<span class="ok"><b>${okCount}</b> up</span>` +
      `<span class="ko"><b>${koCount}</b> ko</span>` +
      `<span class="down"><b>${downCount}</b> down</span>`;

    // Render rows
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = rows.map(r => `
      <tr data-status="${r.status}">
        <td class="domain"><a href="https://${r.domain}" target="_blank" rel="noopener">${r.domain}</a></td>
        <td class="status"><span class="badge ${r.status}"><span class="dot"></span>${r.status}</span></td>
        <td class="code">${r.code}</td>
        <td class="copy-cell"><button class="copy-btn" onclick="copyDomain('${r.domain}')">copy</button></td>
      </tr>
    `).join('');

    // Update sort headers
    document.querySelectorAll('thead th[data-col]').forEach(th => {
      th.classList.toggle('sorted', th.dataset.col === sortCol);
      const arrow = th.querySelector('.sort-arrow');
      if (th.dataset.col === sortCol) arrow.textContent = sortAsc ? '↑' : '↓';
      else arrow.textContent = '↕';
    });
  }

  // Sort on header click
  document.querySelectorAll('thead th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      if (sortCol === th.dataset.col) sortAsc = !sortAsc;
      else { sortCol = th.dataset.col; sortAsc = true; }
      render();
    });
  });

  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      filterStatus = btn.dataset.filter;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      render();
    });
  });

  // Search
  document.getElementById('search').addEventListener('input', e => {
    searchQuery = e.target.value;
    render();
  });

  // Copy
  function copyDomain(text) {
    const fallback = () => {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.top = '-9999px';
      document.body.appendChild(ta); ta.focus(); ta.select();
      try { document.execCommand('copy'); } catch(e) {}
      document.body.removeChild(ta);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).catch(fallback);
    } else { fallback(); }
    showToast();
  }

  function showToast() {
    const t = document.getElementById('toast');
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 1400);
  }

  // Auto-refresh (only when tab visible)
  fetchStatus();
  setInterval(() => {
    if (document.visibilityState === 'visible') fetchStatus();
  }, {{ REFRESH_MS }});
</script>
</body>
</html>"""


@app.route("/favicon.ico")
@app.route("/apple-touch-icon.png")
@app.route("/apple-touch-icon-precomposed.png")
def favicon():
    return Response(status=204)


@app.route("/")
def index():
    return render_template_string(TEMPLATE, REFRESH_MS=REFRESH_MS)


@app.route("/api/status")
def api_status():
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        rows: List[Dict[str, str]] = list(exe.map(check_site, DOMAINS))
    rows.sort(key=lambda r: r["domain"].lower())
    rows.append({"_checked_at": datetime.now(timezone.utc).isoformat()})
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
