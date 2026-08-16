from pathlib import Path

p = Path("ruffle-src/render/wgpu/src/filters.rs")
s = p.read_text()
needle = """    ) -> CommandTarget {\n        let target = match filter {\n"""
replacement = """    ) -> CommandTarget {\n        // DarkFate ARMHF diagnostic: optionally bypass expensive Flash filters.\n        // This is disabled by default and only activates when the isolated\n        // cabinet launcher sets DARKFATE_BYPASS_FILTERS.\n        if std::env::var_os(\"DARKFATE_BYPASS_FILTERS\").is_some() {\n            let target = descriptors.filters.color_matrix.apply(\n                descriptors,\n                texture_pool,\n                draw_encoder,\n                staging_belt,\n                &source,\n                &Default::default(),\n            );\n            target.ensure_cleared(draw_encoder);\n            return target;\n        }\n\n        let target = match filter {\n"""
if needle not in s:
    raise SystemExit("expected Filters::apply insertion point not found")
s = s.replace(needle, replacement, 1)
p.write_text(s)
print("patched", p)
