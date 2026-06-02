#!/usr/bin/env node
"use strict";

const http = require("http");
const net = require("net");

const HOST = process.env.GLAM_PROXY_HOST || "127.0.0.1";
const PORT = Number.parseInt(process.env.GLAM_PROXY_PORT || "8890", 10);
const HTTP_TARGET_HOST = process.env.GLAM_HTTP_HOST || "127.0.0.1";
const HTTP_TARGET_PORT = Number.parseInt(process.env.GLAM_HTTP_PORT || "3000", 10);
const WS_TARGET_HOST = process.env.GLAM_WS_HOST || "127.0.0.1";
const WS_TARGET_PORT = Number.parseInt(process.env.GLAM_WS_PORT || "8877", 10);
const WS_PATH = process.env.GLAM_WS_PATH || "/twilio/media";

function writeJson(res, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

function proxyHttp(req, res) {
  if (req.url === "/__proxy/health") {
    writeJson(res, 200, {
      ok: true,
      service: "glam-public-proxy",
      http_target: `http://${HTTP_TARGET_HOST}:${HTTP_TARGET_PORT}`,
      ws_target: `ws://${WS_TARGET_HOST}:${WS_TARGET_PORT}${WS_PATH}`,
    });
    return;
  }

  const headers = {
    ...req.headers,
    host: `${HTTP_TARGET_HOST}:${HTTP_TARGET_PORT}`,
    "x-glam-public-proxy": "1",
  };
  const upstream = http.request(
    {
      host: HTTP_TARGET_HOST,
      port: HTTP_TARGET_PORT,
      method: req.method,
      path: req.url,
      headers,
    },
    (upstreamRes) => {
      res.writeHead(upstreamRes.statusCode || 502, upstreamRes.headers);
      upstreamRes.pipe(res);
    },
  );

  upstream.on("error", (error) => {
    writeJson(res, 502, {
      ok: false,
      error: "glam_http_upstream_unavailable",
      detail: error.message,
    });
  });

  req.pipe(upstream);
}

function proxyWebSocket(req, socket, head) {
  const path = (req.url || "").split("?")[0];
  if (path !== WS_PATH) {
    socket.write("HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n");
    socket.destroy();
    return;
  }

  const upstream = net.connect(WS_TARGET_PORT, WS_TARGET_HOST, () => {
    const headerLines = Object.entries(req.headers)
      .map(([name, value]) => `${name}: ${Array.isArray(value) ? value.join(", ") : value}`)
      .join("\r\n");
    upstream.write(`${req.method} ${req.url} HTTP/${req.httpVersion}\r\n${headerLines}\r\n\r\n`);
    if (head && head.length > 0) {
      upstream.write(head);
    }
    upstream.pipe(socket);
    socket.pipe(upstream);
  });

  upstream.on("error", (error) => {
    if (!socket.destroyed) {
      socket.end(
        `HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\nContent-Type: text/plain\r\n\r\n${error.message}`,
      );
    }
  });
  socket.on("error", () => upstream.destroy());
}

const server = http.createServer(proxyHttp);
server.on("upgrade", proxyWebSocket);
server.on("clientError", (_error, socket) => {
  if (!socket.destroyed) {
    socket.end("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
  }
});

server.listen(PORT, HOST, () => {
  console.log(`GLAM public proxy listening on http://${HOST}:${PORT}`);
  console.log(`HTTP -> http://${HTTP_TARGET_HOST}:${HTTP_TARGET_PORT}`);
  console.log(`WS ${WS_PATH} -> ws://${WS_TARGET_HOST}:${WS_TARGET_PORT}${WS_PATH}`);
});
