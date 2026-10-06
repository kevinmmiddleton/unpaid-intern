// Checks the hook's matcher the way Claude Code runs it (a JavaScript regex), against the same tool names
// the Python tests use. Run: node tools/hook_check.mjs
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";

const hooks = JSON.parse(readFileSync(new URL("../hooks/hooks.json", import.meta.url), "utf8"));
const rx = new RegExp(hooks.hooks.PreToolUse[0].matcher);
const py = process.platform === "win32" ? "python" : "python3";
const lists = JSON.parse(execFileSync(py, ["-c",
  "import json,sys; sys.path.insert(0,'tools'); import hook_rules as h; print(json.dumps([h.MUST_ASK, h.MUST_PASS]))"],
  { cwd: new URL("..", import.meta.url) }).toString());
const [ask, pass] = lists;
const missed = ask.filter((n) => !rx.test(n));
const leaked = pass.filter((n) => rx.test(n));
for (const n of missed) console.log("should ask:", n);
for (const n of leaked) console.log("should pass:", n);
console.log(`JavaScript matcher: ${ask.length - missed.length}/${ask.length} asked, ${pass.length - leaked.length}/${pass.length} passed`);
process.exit(missed.length || leaked.length ? 1 : 0);
