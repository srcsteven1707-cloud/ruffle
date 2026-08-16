from pathlib import Path

matches = list(Path.home().glob('.cargo/registry/src/*/wgpu-hal-27.0.4/src/gles/adapter.rs'))
if len(matches) != 1:
    raise SystemExit(f'expected exactly one wgpu-hal 27.0.4 adapter.rs, found {matches}')

p = matches[0]
s = p.read_text()
old = '            log::error!("Fake map");\n            let length = dst_data.len();\n'
new = '''            let length = dst_data.len();
            log::error!("Fake map target={target:#x} offset={offset} length={length}");
'''
if s.count(old) != 1:
    raise SystemExit(f'expected one Fake map block, found {s.count(old)}')
s = s.replace(old, new, 1)
p.write_text(s)
print(f'Patched Fake map diagnostics with target/offset/length in {p}')
