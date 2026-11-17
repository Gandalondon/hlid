## 17 Nov 2026: agreed, not built yet

New built-in rules (no settings: rules, not options). Context: from a brainstorm; Tony's 12 app idea rules are in the Google Doc "App idea rules" in his Drive Claude folder.

### 1. Mud-aware ranking
- Data: past few days' rainfall at the walk location from Open-Meteo (free, past days); bedrock from the British Geological Survey open geology map (chalk drains fast, clay stays boggy for days); plus OpenStreetMap path surface tags.
- After a wet spell, rank chalk and well-drained walks higher and clay lower. Mud is a ranking factor, never a filter: Hlid always returns a walk.
- If the best available walk is still likely muddy, show one short line on the walk screen: Likely muddy after recent rain.
- If it's wet everywhere, say it once rather than repeating on every Try another: Everywhere's wet this week. This is the driest walk nearby.
- No note means it should be fine. Never promise dry paths (rule 3 of the App idea rules: promise the experience, never the outcome).

### 2. Leave by
- Only suggest walks that can be finished before dark, based on the current time, drive time and walk length.

### Copy to add
- Homepage USP: Wet week? It picks walks that drain.
- How it works / FAQ: Hlid checks the weather where you're walking, not where you live. It also looks at how much rain has fallen over the past few days. After a wet spell, it favours chalk hills and well-drained paths over clay that stays boggy for days. It won't promise dry boots, but it'll keep you out of the worst of it.
- Dark evenings: It only suggests walks you can finish before it gets dark.
