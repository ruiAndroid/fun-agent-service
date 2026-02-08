const express = require("express");
const { spawn } = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.json({ limit: "1mb" }));

const PORT = Number(process.env.PORT || 4010);
const PYTHON_BIN = process.env.PYTHON_BIN || "python";
const LLM_CONFIG_PATH =
  process.env.LLM_CONFIG_PATH || path.join(__dirname, "agents", "configs", "llm.json");

app.use((req, res, next) => {
  const incoming = req.headers["x-trace-id"];
  const traceId = typeof incoming === "string" && incoming.trim()
    ? incoming
    : crypto.randomUUID();
  req.traceId = traceId;
  res.setHeader("x-trace-id", traceId);
  next();
});

function runPython(args, input) {
  return new Promise((resolve, reject) => {
    const proc = spawn(PYTHON_BIN, args, {
      stdio: ["pipe", "pipe", "pipe"],
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
      },
    });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    proc.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    proc.on("error", reject);
    proc.on("close", (code) => {
      if (code !== 0) {
        return reject(new Error(stderr || `python exited with code ${code}`));
      }
      resolve(stdout.trim());
    });

    if (input) {
      proc.stdin.write(input);
    }
    proc.stdin.end();
  });
}

function readLlmConfig() {
  try {
    const raw = fs.readFileSync(LLM_CONFIG_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return {
      base_url: "http://localhost:8000",
      api_key: "",
      model: "gpt-4o-mini",
      timeout: 30,
    };
  }
}

function writeLlmConfig(next) {
  const dir = path.dirname(LLM_CONFIG_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(LLM_CONFIG_PATH, JSON.stringify(next, null, 2), "utf-8");
}

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.get("/agents", async (_req, res) => {
  try {
    const out = await runPython(["agent_runtime.py", "--list"]);
    const data = out ? JSON.parse(out) : [];
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : String(err) });
  }
});

app.get("/config/llm", (_req, res) => {
  res.json(readLlmConfig());
});

app.put("/config/llm", (req, res) => {
  const current = readLlmConfig();
  const body = req.body && typeof req.body === "object" ? req.body : {};
  const timeoutValue =
    typeof body.timeout === "number" ? body.timeout : Number(body.timeout);
  const next = {
    base_url: typeof body.base_url === "string" ? body.base_url : current.base_url,
    api_key: typeof body.api_key === "string" ? body.api_key : current.api_key,
    model: typeof body.model === "string" ? body.model : current.model,
    timeout: Number.isFinite(timeoutValue) ? timeoutValue : current.timeout,
  };
  writeLlmConfig(next);
  res.json(next);
});

app.post("/agents/:agent/execute", async (req, res) => {
  const agent = req.params.agent;
  const payload = {
    agent,
    input: req.body?.input ?? "",
    context: { ...(req.body?.context ?? {}), trace_id: req.traceId },
  };
  try {
    const out = await runPython(["agent_runtime.py"], JSON.stringify(payload));
    const data = out ? JSON.parse(out) : { output: "" };
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err instanceof Error ? err.message : String(err) });
  }
});

app.listen(PORT, () => {
  console.log(`fun-agent-service listening on http://localhost:${PORT}`);
});
