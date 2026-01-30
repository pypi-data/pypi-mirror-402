"""app/templates/*"""

from textwrap import dedent

APP_TEMPLATES_INDEX_CONTENT = dedent("""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <title>API Status</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />

    <style>
        :root {
            --bg: #0b0614;
            --card: #140b25;
            --purple: #8b5cf6;
            --purple-glow: rgba(139, 92, 246, 0.6);
            --text: #e9e6f2;
            --muted: #b6b1cc;
            --success: #22c55e;
            --error: #ef4444;
        }

        * {
            box-sizing: border-box;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top, #1a0f33, transparent 60%),
                var(--bg);
            color: var(--text);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card {
            background: linear-gradient(180deg, #1a1033, var(--card));
            border-radius: 16px;
            padding: 32px 36px;
            width: 100%;
            max-width: 420px;
            text-align: center;
            box-shadow:
                0 0 0 1px rgba(139, 92, 246, 0.2),
                0 20px 60px rgba(0, 0, 0, 0.7);
            position: relative;
        }

        .card::before {
            content: "";
            position: absolute;
            inset: -1px;
            border-radius: 16px;
            background: linear-gradient(120deg, transparent, var(--purple), transparent);
            opacity: 0.15;
            pointer-events: none;
        }

        h1 {
            margin: 0 0 8px;
            font-size: 1.6rem;
            letter-spacing: 0.4px;
        }

        .subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            margin-bottom: 28px;
        }

        .status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            font-size: 1.1rem;
            margin-bottom: 18px;
        }

        .dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: var(--muted);
            box-shadow: 0 0 0 0 transparent;
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }

        .online {
            color: var(--success);
        }

        .online .dot {
            background: var(--success);
            box-shadow: 0 0 12px rgba(34, 197, 94, 0.7);
        }

        .offline {
            color: var(--error);
        }

        .offline .dot {
            background: var(--error);
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.7);
        }

        .meta {
            font-size: 0.85rem;
            color: var(--muted);
            margin-top: 6px;
        }

        .footer {
            margin-top: 26px;
            font-size: 0.75rem;
            color: var(--muted);
            opacity: 0.8;
        }

        .pulse {
            animation: pulse 1.8s infinite;
        }

        .docs-btn {
            margin-top: 22px;
            padding: 10px 18px;
            border-radius: 10px;
            border: 1px solid rgba(139, 92, 246, 0.4);
            background: linear-gradient(180deg, #1e1240, #140b25);
            color: var(--text);
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.25s ease;
        }

        .docs-btn:hover {
            transform: translateY(-1px);
            border-color: var(--purple);
            box-shadow:
                0 0 0 1px rgba(139, 92, 246, 0.4),
                0 8px 30px rgba(139, 92, 246, 0.35);
        }

        .docs-btn:active {
            transform: translateY(0);
        }


        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 var(--purple-glow);
            }

            70% {
                box-shadow: 0 0 0 14px transparent;
            }

            100% {
                box-shadow: 0 0 0 0 transparent;
            }
        }
    </style>
</head>

<body>
    <div class="card">
        <h1>API Server</h1>
        <div class="subtitle">Service availability monitor</div>

        <div id="status" class="status">
            <span class="dot pulse"></span>
            <span>Checking status…</span>
        </div>

        <div id="meta" class="meta"></div>

        <button class="docs-btn" onclick="goToDocs()">
            View API Docs →
        </button>

        <div class="footer">
            © Your API · Secure · Monitored
        </div>
    </div>

    <script>
        const STATUS_ENDPOINT = "/health"; // change if needed

        async function checkStatus() {
            const statusEl = document.getElementById("status");
            const metaEl = document.getElementById("meta");

            try {
                const res = await fetch(STATUS_ENDPOINT, { cache: "no-store" });
                if (!res.ok) throw new Error("Server error");

                statusEl.className = "status online";
                statusEl.innerHTML = `
          <span class="dot"></span>
          <span>ONLINE</span>
        `;
                metaEl.textContent = "Last checked: " + new Date().toLocaleTimeString();
            } catch {
                statusEl.className = "status offline";
                statusEl.innerHTML = `
          <span class="dot"></span>
          <span>OFFLINE</span>
        `;
                metaEl.textContent = "Unable to reach server";
            }
        }

        checkStatus();
        setInterval(checkStatus, 15000); // auto refresh every 15s

        function goToDocs() {
            window.location.href = "/docs";
        }
    </script>
</body>

</html>
""")
