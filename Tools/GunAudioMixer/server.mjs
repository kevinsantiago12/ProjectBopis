#!/usr/bin/env node
// Gun Audio Mixer: a local web panel for tuning each weapon's fire sound in the
// running editor, through the editor's MCP bridge (http://127.0.0.1:8000/mcp).
//
//   node Tools/GunAudioMixer/server.mjs      then open http://localhost:8123
//
// Edits apply to the open editor immediately (unsaved, like editing by hand);
// the page's Save button saves the touched assets (and the player/enemy gunshot
// volume, to Config/DefaultGame.ini). Previews play the recordings
// in the browser straight from the .uasset files on disk.
//
// No dependencies -- Node 18+ (global fetch).

import { createServer } from "node:http";
import { readFileSync, readdirSync, existsSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const PROJECT = join(HERE, "..", "..");
const CONTENT = join(PROJECT, "Content");
const WEAPON_DIR = join(CONTENT, "ThirdPerson", "Blueprints");
const ATT_DIR = join(CONTENT, "Audio", "Weapons");
const PORT = Number(process.env.PORT || 8123);
const UPSTREAM = process.env.UNREAL_MCP_URL || "http://127.0.0.1:8000/mcp";

const GAME_INI = join(PROJECT, "Config", "DefaultGame.ini");
// UWeaponAudioSettings (Project Settings > Game > Weapon Audio): the player's and the enemies' gunshot volume.
const SHOT_SECTION = "/Script/ProjectBopis.WeaponAudioSettings";
const SHOT_CDO = "/Script/ProjectBopis.Default__WeaponAudioSettings";
const SHOT_KEYS = ["PlayerShotVolume", "EnemyShotVolume"];

const OBJ = "editor_toolset.toolsets.object.ObjectTools";
const ASSET = "editor_toolset.toolsets.asset.AssetTools";

// ---------------------------------------------------------------- bridge

let sessionId = null;
let rpcId = 1;
let queue = Promise.resolve();

async function rpc(method, params, notify = false) {
	const headers = { "Content-Type": "application/json", Accept: "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18" };
	if (sessionId) headers["Mcp-Session-Id"] = sessionId;
	const body = notify ? { jsonrpc: "2.0", method, params } : { jsonrpc: "2.0", id: rpcId++, method, params };
	const res = await fetch(UPSTREAM, { method: "POST", headers, body: JSON.stringify(body) });
	if (sessionId && (res.status === 404 || res.status === 400)) { sessionId = null; throw new Error("session expired"); }
	sessionId = res.headers.get("mcp-session-id") || sessionId;
	const text = await res.text();
	if (notify) return null;
	if (!(res.headers.get("content-type") || "").includes("event-stream")) return JSON.parse(text);
	for (const ev of text.split(/\r?\n\r?\n/)) {
		const data = ev.split(/\r?\n/).filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trimStart()).join("\n");
		if (data) { const msg = JSON.parse(data); if (msg.id === body.id) return msg; }
	}
	throw new Error("no response from editor");
}

async function connect() {
	await rpc("initialize", { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "gun-audio-mixer", version: "1" } });
	await rpc("notifications/initialized", {}, true);
}

// One call at a time; reconnects once if the editor restarted.
function tool(toolset, name, args) {
	const run = async () => {
		for (let attempt = 0; ; attempt++) {
			try {
				if (!sessionId) await connect();
				const r = await rpc("tools/call", { name: "call_tool", arguments: { toolset_name: toolset, tool_name: name, arguments: args } });
				if (r.error) throw new Error(r.error.message);
				const text = (r.result.content || []).map((c) => c.text).join("");
				if (r.result.isError) throw new Error(text);
				const ret = JSON.parse(text).returnValue;
				return typeof ret === "string" && /^[[{]/.test(ret) ? JSON.parse(ret) : ret;
			} catch (e) {
				if (attempt === 0 && /session expired|fetch failed/.test(e.message)) { sessionId = null; continue; }
				if (/fetch failed|ECONNREFUSED/.test(e.message)) throw new Error("The editor isn't answering on port 8000. Is it open?");
				throw e;
			}
		}
	};
	const p = queue.then(run, run);
	queue = p.catch(() => {});
	return p;
}

const getProps = (ref, properties) => tool(OBJ, "get_properties", { instance: { refPath: ref }, properties });
const setProps = (ref, values) => tool(OBJ, "set_properties", { instance: { refPath: ref }, values: JSON.stringify(values) });

// ---------------------------------------------------------------- reading state

const objectPath = (pkg) => `${pkg}.${pkg.split("/").pop()}`;
const packageOf = (ref) => ref.split(".")[0];
const fileOf = (ref) => join(CONTENT, packageOf(ref).replace(/^\/Game\//, "") + ".uasset");

// Weapon Blueprints are the BP_*.uasset files that save a FireSound.
function weaponBlueprints() {
	return readdirSync(WEAPON_DIR)
		.filter((f) => /^BP_.*\.uasset$/.test(f) && readFileSync(join(WEAPON_DIR, f)).includes("FireSound"))
		.map((f) => f.replace(/\.uasset$/, ""));
}

async function readCue(cue) {
	const top = await getProps(cue, ["VolumeMultiplier", "AttenuationSettings", "FirstNode"]);
	const info = { volume: top.VolumeMultiplier, attenuation: top.AttenuationSettings?.refPath || null, modulator: null, waves: [] };
	const walk = async (ref) => {
		if (!ref) return;
		const kind = ref.split(":").pop();
		if (kind.startsWith("SoundNodeWavePlayer")) {
			const p = await getProps(ref, ["SoundWaveAssetPtr"]);
			if (p.SoundWaveAssetPtr?.refPath) info.waves.push(p.SoundWaveAssetPtr.refPath);
			return;
		}
		const props = ["ChildNodes"];
		const isMod = kind.startsWith("SoundNodeModulator") && !info.modulator;
		if (isMod) props.push("PitchMin", "PitchMax", "VolumeMin", "VolumeMax");
		const p = await getProps(ref, props);
		if (isMod) info.modulator = { ref, pitchMin: p.PitchMin, pitchMax: p.PitchMax, volumeMin: p.VolumeMin, volumeMax: p.VolumeMax };
		for (const c of p.ChildNodes || []) await walk(c?.refPath);
	};
	await walk(top.FirstNode?.refPath);
	return info;
}

const ATT_FIELDS = ["distanceAlgorithm", "falloffMode", "dBAttenuationAtMax", "attenuationShapeExtents", "falloffDistance",
	"bAttenuateWithLPF", "lPFRadiusMin", "lPFRadiusMax", "lPFFrequencyAtMax", "bEnableReverbSend",
	"reverbWetLevelMin", "reverbWetLevelMax", "reverbDistanceMin", "reverbDistanceMax"];

async function readAttenuation(ref) {
	const a = (await getProps(ref, ["Attenuation"])).Attenuation;
	return Object.fromEntries(ATT_FIELDS.map((k) => [k, a[k]]));
}

async function state() {
	const weapons = [];
	for (const bp of weaponBlueprints()) {
		const p = await getProps(`/Game/ThirdPerson/Blueprints/${bp}.Default__${bp}_C`, ["FireSound"]).catch(() => ({}));
		weapons.push({ bp, cue: p.FireSound?.refPath || null });
	}
	const cues = {};
	for (const w of weapons) if (w.cue && !cues[w.cue]) cues[w.cue] = await readCue(w.cue);

	const attRefs = new Set(readdirSync(ATT_DIR).filter((f) => /^ATT_.*\.uasset$/.test(f)).map((f) => objectPath(`/Game/Audio/Weapons/${f.replace(/\.uasset$/, "")}`)));
	for (const c of Object.values(cues)) if (c.attenuation) attRefs.add(c.attenuation);
	const attenuations = {};
	for (const a of attRefs) attenuations[a] = await readAttenuation(a);
	return { weapons, cues, attenuations, shotVolume: await readShotVolume() };
}

// Null until the C++ class is compiled into the editor.
async function readShotVolume() {
	try {
		const p = await getProps(SHOT_CDO, SHOT_KEYS);
		return { player: p.PlayerShotVolume, enemy: p.EnemyShotVolume };
	} catch {
		return null;
	}
}

// ---------------------------------------------------------------- writing

async function applyCue({ cue, volume, attenuation, modulator }) {
	const top = {};
	if (volume !== undefined) top.VolumeMultiplier = volume;
	if (attenuation !== undefined) top.AttenuationSettings = attenuation || "None";
	if (Object.keys(top).length) await setProps(cue, top);
	if (modulator) {
		const { ref, pitchMin, pitchMax, volumeMin, volumeMax } = modulator;
		await setProps(ref, { PitchMin: pitchMin, PitchMax: pitchMax, VolumeMin: volumeMin, VolumeMax: volumeMax });
	}
	return readCue(cue);
}

// Writes the whole struct back so fields the page doesn't show keep their values.
async function applyAttenuation({ att, fields }) {
	const a = (await getProps(att, ["Attenuation"])).Attenuation;
	for (const k of Object.keys(fields)) if (ATT_FIELDS.includes(k)) a[k] = fields[k];
	await setProps(att, { Attenuation: a });
	return readAttenuation(att);
}

// Live in the editor; written to DefaultGame.ini on Save.
async function applyShotVolume({ player, enemy }) {
	await setProps(SHOT_CDO, { PlayerShotVolume: player, EnemyShotVolume: enemy });
	return readShotVolume();
}

// Rewrites just the Weapon Audio section of DefaultGame.ini, as Project Settings would.
function writeShotVolumeIni({ player, enemy }) {
	const eol = readFileSync(GAME_INI, "utf8").includes("\r\n") ? "\r\n" : "\n";
	const lines = readFileSync(GAME_INI, "utf8").split(/\r?\n/);
	const body = [`PlayerShotVolume=${player}`, `EnemyShotVolume=${enemy}`];
	const start = lines.indexOf(`[${SHOT_SECTION}]`);
	if (start < 0) {
		while (lines.length && lines[lines.length - 1] === "") lines.pop();
		lines.push("", `[${SHOT_SECTION}]`, ...body, "");
	} else {
		let end = start + 1;
		while (end < lines.length && !lines[end].startsWith("[")) end++;
		const kept = lines.slice(start + 1, end).filter((l) => l.trim() && !SHOT_KEYS.some((k) => l.startsWith(`${k}=`)));
		lines.splice(start + 1, end - start - 1, ...kept, ...body, "");
	}
	writeFileSync(GAME_INI, lines.join(eol));
}

async function save({ refs, shotVolume }) {
	const assets = refs.filter((r) => r !== "shotVolume");
	if (assets.length) await tool(ASSET, "save_assets", { asset_paths: [...new Set(assets.map(packageOf))] });
	if (shotVolume) writeShotVolumeIni(shotVolume);
	return true;
}

// The editor keeps each imported wav whole inside its .uasset; serve that RIFF.
function waveBytes(ref) {
	const file = fileOf(ref);
	if (!existsSync(file)) return null;
	const b = readFileSync(file);
	const i = b.indexOf("RIFF");
	if (i < 0 || b.toString("latin1", i + 8, i + 12) !== "WAVE") return null;
	return b.subarray(i, i + 8 + b.readUInt32LE(i + 4));
}

// ---------------------------------------------------------------- http

const json = (res, code, body) => { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(body)); };
const readBody = (req) => new Promise((ok) => { let s = ""; req.on("data", (d) => (s += d)); req.on("end", () => ok(s ? JSON.parse(s) : {})); });

const routes = {
	"GET /api/state": () => state(),
	"POST /api/cue": (b) => applyCue(b),
	"POST /api/attenuation": (b) => applyAttenuation(b),
	"POST /api/shot-volume": (b) => applyShotVolume(b),
	"POST /api/save": (b) => save(b),
};

createServer(async (req, res) => {
	const url = new URL(req.url, "http://localhost");
	try {
		if (url.pathname === "/") {
			res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
			return res.end(readFileSync(join(HERE, "index.html")));
		}
		if (url.pathname === "/wave") {
			const bytes = waveBytes(url.searchParams.get("ref") || "");
			if (!bytes) return json(res, 404, { error: "No playable wav in that asset." });
			res.writeHead(200, { "Content-Type": "audio/wav" });
			return res.end(bytes);
		}
		const route = routes[`${req.method} ${url.pathname}`];
		if (!route) return json(res, 404, { error: "Not found" });
		json(res, 200, await route(req.method === "POST" ? await readBody(req) : {}));
	} catch (e) {
		json(res, 502, { error: e.message });
	}
}).listen(PORT, "127.0.0.1", () => console.log(`Gun Audio Mixer: http://localhost:${PORT}`));
