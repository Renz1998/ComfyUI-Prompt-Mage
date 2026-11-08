# Tag filter presets

[Open the complete workflow example](../workflows/start-here/07-tag-filter-presets.json). It shares a Full color recipe with DART Generate and Archmage; the original main graph is unchanged.

Add **Prompt Mage · Tag Filters**. Connect **filters** to both **DART Generate.filters** and **Archmage.filters**. Use the same recipe to discourage tags during generation, clean final tags and guide the assistant's prose/JSON.

Presets: **Full color**, **No text / watermarks**, **Photography**, their combined **Full color + clean photo**, and **Custom only**. Lists use curated exact tags and known aliases from the bundled vocabulary snapshot. They are not exhaustive semantic categories. Black hair and black clothing are not excluded by Full color.

- **Prevent during generation** bans preset tags in DART's continuation. Tags already in its input require cleanup too.
- **Clean final output** removes preset tags from the decoded DART result and Archmage's incoming source tags.
- **Extra banned tags** and **Remove tags** work independently of preset switches. Enter comma-separated exact tags, not regex.
- **Protected tags** are retained/appended in DART; they are not an allow-only whitelist. Conflicts with exclusions or Generate's Keep tags produce an actionable error.

The string outputs can be wired manually to existing ban/remove/keep inputs, including advanced workflows. The recipe input also checks conflicts and passes instructions downstream, so it is preferred. Inspect **report** for resolved lists. No model call or network request is used to build a filter.

Archmage removes matching incoming tags and receives the exclusions as writing instructions. This is not a semantic guarantee or a hard prose filter; inspect generated prose/JSON. An explicitly monochrome style conflicts with Full color and must be changed. Free-form instructions and visual results can still conflict. This does not remove writing or watermarks from image pixels.
