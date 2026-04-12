import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export default definePluginEntry({
  id: "job-search",
  name: "Job Search",
  description: "Skill-first job-search package. Bundled skills live under skills/ and are declared in openclaw.plugin.json.",
  register() {
    // Intentionally minimal.
    // This package ships bundled skills; workflow behavior lives in skills/, scripts/, and references/.
  },
});
