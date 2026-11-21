import { createServer } from "node:http";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import "./bundle.js";

const TARGET = "https://api.gigachat.local";
const KEY_HEADER = "x-gigachat-proxy-key";
const SKIP_REQUEST = new Set(["host", "connection", "content-length", KEY_HEADER]);
const SKIP_RESPONSE = new Set(["connection", "content-length", "content-encoding", "transfer-encoding"]);

function createProxy(secret) {
  return createServer(async (req, res) => {
    const controller = new AbortController();
    res.on("close", () => {
      if (!res.writableFinished) controller.abort();
    });
    try {
      if (req.headers[KEY_HEADER] !== secret) {
        res.writeHead(403).end();
        return;
      }
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const headers = new Headers();
      for (const [name, value] of Object.entries(req.headers)) {
        if (SKIP_REQUEST.has(name) || value === undefined) continue;
        headers.set(name, Array.isArray(value) ? value.join(", ") : value);
      }
      const hasBody = chunks.length > 0 && req.method !== "GET" && req.method !== "HEAD";
      const response = await globalThis.fetch(TARGET + req.url, {
        method: req.method,
        headers,
        body: hasBody ? Buffer.concat(chunks) : undefined,
        signal: controller.signal,
      });
      const out = {};
      response.headers.forEach((value, name) => {
        if (!SKIP_RESPONSE.has(name)) out[name] = value;
      });
      res.writeHead(response.status, out);
      if (response.body) {
        for await (const chunk of response.body) {
          if (!res.write(chunk)) await once(res, "drain");
        }
      }
      res.end();
    } catch (error) {
      if (controller.signal.aborted) return;
      if (res.headersSent) {
        res.destroy();
        return;
      }
      res
        .writeHead(502, { "content-type": "application/json" })
        .end(JSON.stringify({ error: { message: error instanceof Error ? error.message : String(error) } }));
    }
  });
}

export default {
  id: "gigachat",
  async setup(ctx) {
    const secret = randomUUID();
    const server = createProxy(secret);
    server.listen(0, "127.0.0.1");
    await once(server, "listening");
    const baseURL = `http://127.0.0.1:${server.address().port}/v1`;

    await ctx.session.hook(
      "model.request",
      (event) => {
        event.baseURL = baseURL;
        event.headers[KEY_HEADER] = secret;
      },
      { providerID: "gigachat" },
    );

    return () => {
      server.close();
      server.closeAllConnections?.();
    };
  },
};
