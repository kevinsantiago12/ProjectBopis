#!/usr/bin/env node
// Stdio <-> HTTP proxy for the Unreal editor's MCP server (ModelContextProtocol
// plugin, http://127.0.0.1:8000/mcp).
//
// Why this exists: Claude Code talks to an HTTP MCP server directly, so if the
// editor is closed when a session starts -- or is closed mid-session for a
// rebuild -- the session marks the server `failed` and the tools vanish until
// someone runs /mcp. This proxy is a local process Claude Code always manages
// to start. It answers `initialize` and `tools/list` itself (the editor's tool
// list is three static meta-tools, snapshotted in unreal-mcp-tools.json), and
// opens or reopens the upstream editor session lazily on each call. An editor
// restart becomes invisible; a closed editor becomes a readable tool error.
//
// No dependencies -- Node 18+ (global fetch).

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline";

const UPSTREAM = process.env.UNREAL_MCP_URL || "http://127.0.0.1:8000/mcp";
const PROTOCOL_VERSION = "2025-06-18";
const TOOLS_SNAPSHOT = join(dirname(fileURLToPath(import.meta.url)), "unreal-mcp-tools.json");

const log = (...a) => process.stderr.write(`[unreal-mcp-proxy] ${a.join(" ")}\n`);
const send = (msg) => process.stdout.write(JSON.stringify(msg) + "\n");

// ---------------------------------------------------------------- upstream

let sessionId = null;
let sessionPromise = null;
let nextUpstreamId = 1;

class UpstreamDown extends Error {}
class SessionExpired extends Error {}

async function post(body, withSession = true) {
	const headers = {
		"Content-Type": "application/json",
		Accept: "application/json, text/event-stream",
		"MCP-Protocol-Version": PROTOCOL_VERSION,
	};
	if (withSession && sessionId) headers["Mcp-Session-Id"] = sessionId;

	let res;
	try {
		res = await fetch(UPSTREAM, { method: "POST", headers, body: JSON.stringify(body) });
	} catch (e) {
		throw new UpstreamDown(e.cause?.code || e.message);
	}

	// The editor answers an unknown/stale session with 404 (and a missing one
	// with 400) plus "client should reinitialize".
	if (withSession && (res.status === 404 || res.status === 400)) {
		await res.text().catch(() => {});
		throw new SessionExpired(`HTTP ${res.status}`);
	}
	return res;
}

// Reads a JSON-RPC response from either a plain JSON body or an SSE stream.
async function readResponse(res, id) {
	const type = res.headers.get("content-type") || "";
	const text = await res.text();
	if (!type.includes("text/event-stream")) return text ? JSON.parse(text) : null;

	for (const event of text.split(/\r?\n\r?\n/)) {
		const data = event
			.split(/\r?\n/)
			.filter((l) => l.startsWith("data:"))
			.map((l) => l.slice(5).trimStart())
			.join("\n");
		if (!data) continue;
		const msg = JSON.parse(data);
		if (msg.id === id) return msg;
	}
	throw new Error("SSE stream ended without a response");
}

async function openSession() {
	sessionId = null;
	const id = `proxy-${nextUpstreamId++}`;
	const res = await post(
		{
			jsonrpc: "2.0",
			id,
			method: "initialize",
			params: {
				protocolVersion: PROTOCOL_VERSION,
				capabilities: {},
				clientInfo: { name: "unreal-mcp-proxy", version: "1.0" },
			},
		},
		false
	);
	const msg = await readResponse(res, id);
	if (msg?.error) throw new Error(`initialize failed: ${msg.error.message}`);
	sessionId = res.headers.get("mcp-session-id");
	await post({ jsonrpc: "2.0", method: "notifications/initialized" }).then((r) => r.text());
	log(`upstream session opened (${sessionId})`);
}

function ensureSession() {
	if (sessionId) return Promise.resolve();
	sessionPromise ??= openSession().finally(() => (sessionPromise = null));
	return sessionPromise;
}

// Forwards one request upstream, reopening the session once if the editor
// restarted underneath us.
async function forward(method, params) {
	for (let attempt = 0; attempt < 2; attempt++) {
		await ensureSession();
		const id = `proxy-${nextUpstreamId++}`;
		try {
			const res = await post({ jsonrpc: "2.0", id, method, params });
			return await readResponse(res, id);
		} catch (e) {
			if (e instanceof SessionExpired || e instanceof UpstreamDown) {
				sessionId = null;
				if (e instanceof SessionExpired) {
					log("upstream session expired, reopening");
					continue;
				}
			}
			throw e;
		}
	}
	throw new Error("upstream rejected a freshly opened session");
}

// ---------------------------------------------------------------- tools list

function snapshotTools() {
	try {
		return JSON.parse(readFileSync(TOOLS_SNAPSHOT, "utf8"));
	} catch {
		return [];
	}
}

async function listTools() {
	try {
		const msg = await forward("tools/list", {});
		const tools = msg?.result?.tools;
		if (Array.isArray(tools) && tools.length) {
			const json = JSON.stringify(tools, null, 2) + "\n";
			if (json !== JSON.stringify(snapshotTools(), null, 2) + "\n") {
				writeFileSync(TOOLS_SNAPSHOT, json);
				log("tool snapshot updated");
			}
			return tools;
		}
	} catch (e) {
		log(`tools/list from snapshot (${e.message})`);
	}
	return snapshotTools();
}

// ---------------------------------------------------------------- dispatch

const editorDownResult = (why) => ({
	content: [
		{
			type: "text",
			text:
				`Unreal editor MCP server not reachable at ${UPSTREAM} (${why}). ` +
				"Open the editor (the server auto-starts at launch) or run " +
				"`ModelContextProtocol.StartServer` in its console, then retry. " +
				"No /mcp reconnect is needed.",
		},
	],
	isError: true,
});

async function handle(msg) {
	const { id, method, params } = msg;
	const isRequest = id !== undefined && method;
	if (!isRequest) return; // notifications / stray responses: nothing to do

	const reply = (result) => send({ jsonrpc: "2.0", id, result });
	const fail = (code, message) => send({ jsonrpc: "2.0", id, error: { code, message } });

	try {
		switch (method) {
			case "initialize":
				return reply({
					protocolVersion: params?.protocolVersion || PROTOCOL_VERSION,
					capabilities: { tools: { listChanged: false } },
					serverInfo: { name: "unreal-mcp-proxy", version: "1.0" },
				});
			case "ping":
				return reply({});
			case "tools/list":
				return reply({ tools: await listTools() });
			case "tools/call":
				try {
					const up = await forward(method, params);
					return up.error ? fail(up.error.code, up.error.message) : reply(up.result);
				} catch (e) {
					if (e instanceof UpstreamDown) return reply(editorDownResult(e.message));
					throw e;
				}
			case "resources/list":
			case "resources/templates/list":
			case "prompts/list": {
				const key = method === "prompts/list" ? "prompts" : method === "resources/list" ? "resources" : "resourceTemplates";
				try {
					const up = await forward(method, params);
					if (up?.result) return reply(up.result);
				} catch {}
				return reply({ [key]: [] });
			}
			default: {
				const up = await forward(method, params);
				return up.error ? fail(up.error.code, up.error.message) : reply(up.result);
			}
		}
	} catch (e) {
		log(`${method} failed: ${e.message}`);
		fail(-32603, e instanceof UpstreamDown ? editorDownResult(e.message).content[0].text : e.message);
	}
}

createInterface({ input: process.stdin }).on("line", (line) => {
	if (!line.trim()) return;
	let msg;
	try {
		msg = JSON.parse(line);
	} catch {
		return log(`unparseable input: ${line.slice(0, 200)}`);
	}
	handle(msg);
});
process.stdin.on("end", () => process.exit(0));
log(`started, upstream ${UPSTREAM}`);
