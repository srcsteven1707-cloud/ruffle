from pathlib import Path

matches = list(Path.home().glob('.cargo/registry/src/*/wgpu-hal-27.0.4/src/gles/egl.rs'))
if len(matches) != 1:
    raise SystemExit(f'expected exactly one wgpu-hal 27.0.4 egl.rs, found {matches}')

p = matches[0]
s = p.read_text()

# Test14: accept presentation-only EGL configs on Linux ARM.
old_threshold = 'if cfg!(target_os = "android") || cfg!(windows) || cfg!(target_env = "ohos") {'
new_threshold = '''if cfg!(target_os = "android")
                        || cfg!(windows)
                        || cfg!(target_env = "ohos")
                        || cfg!(all(target_os = "linux", target_arch = "arm"))
                    {'''
if s.count(old_threshold) != 1:
    raise SystemExit(f'expected one EGL tier threshold condition, found {s.count(old_threshold)}')
s = s.replace(old_threshold, new_threshold, 1)

# Test17-proven 16-byte DarkFate fbdev native-window descriptor.
# The Mali r14p0 driver retains the native-window pointer after
# eglCreateWindowSurface, so the pointed-to descriptor must remain alive for
# every later eglSwapBuffers call. For this diagnostic build, leak exactly one
# 16-byte descriptor per surface configuration. This deliberately avoids
# touching upstream Swapchain ownership/layout while guaranteeing pointer
# lifetime until process exit.
old_native = '''                let mut wl_window = None;
                let (mut temp_xlib_handle, mut temp_xcb_handle);
                let native_window_ptr = match (self.wsi.kind, self.raw_window_handle) {
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xlib(handle)) => {
                        temp_xlib_handle = handle.window;
                        ptr::from_mut(&mut temp_xlib_handle).cast::<ffi::c_void>()
                    }
                    (WindowKind::AngleX11, Rwh::Xlib(handle)) => handle.window as *mut ffi::c_void,
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xcb(handle)) => {
                        temp_xcb_handle = handle.window;
                        ptr::from_mut(&mut temp_xcb_handle).cast::<ffi::c_void>()
                    }
'''
new_native = '''                let mut wl_window = None;
                let (mut temp_xlib_handle, mut temp_xcb_handle);
                #[repr(C)]
                struct DarkFateFbdevWindow {
                    width16: u16,
                    height16: u16,
                    zero: u32,
                    width32: u32,
                    height32: u32,
                }
                let use_darkfate_fbdev =
                    cfg!(all(target_os = "linux", target_arch = "arm"));
                let darkfate_fbdev_window_ptr = if use_darkfate_fbdev {
                    let leaked = alloc::boxed::Box::leak(alloc::boxed::Box::new(
                        DarkFateFbdevWindow {
                            width16: 1280,
                            height16: 960,
                            zero: 0,
                            width32: 1280,
                            height32: 960,
                        },
                    ));
                    ptr::from_mut(leaked).cast::<ffi::c_void>()
                } else {
                    ptr::null_mut()
                };
                let native_window_ptr = match (self.wsi.kind, self.raw_window_handle) {
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xlib(handle)) => {
                        if use_darkfate_fbdev {
                            darkfate_fbdev_window_ptr
                        } else {
                            temp_xlib_handle = handle.window;
                            ptr::from_mut(&mut temp_xlib_handle).cast::<ffi::c_void>()
                        }
                    }
                    (WindowKind::AngleX11, Rwh::Xlib(handle)) => handle.window as *mut ffi::c_void,
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xcb(handle)) => {
                        if use_darkfate_fbdev {
                            darkfate_fbdev_window_ptr
                        } else {
                            temp_xcb_handle = handle.window;
                            ptr::from_mut(&mut temp_xcb_handle).cast::<ffi::c_void>()
                        }
                    }
'''
if s.count(old_native) != 1:
    raise SystemExit(f'expected one X11/XCB native-window block, found {s.count(old_native)}')
s = s.replace(old_native, new_native, 1)

# Test17 created the Mali fbdev surface with no EGL_RENDER_BUFFER override.
# Match that on Linux ARM instead of forcing EGL_SINGLE_BUFFER.
old_attrs = '''                let mut attributes = vec![
                    khronos_egl::RENDER_BUFFER,
                    // We don't want any of the buffering done by the driver, because we
                    // manage a swapchain on our side.
                    // Some drivers just fail on surface creation seeing `EGL_SINGLE_BUFFER`.
                    if cfg!(any(
                        target_os = "android",
                        target_os = "macos",
                        target_env = "ohos"
                    )) || cfg!(windows)
                        || self.wsi.kind == WindowKind::AngleX11
                    {
                        khronos_egl::BACK_BUFFER
                    } else {
                        khronos_egl::SINGLE_BUFFER
                    },
                ];
'''
new_attrs = '''                let mut attributes = if cfg!(all(
                    target_os = "linux",
                    target_arch = "arm"
                )) {
                    Vec::new()
                } else {
                    vec![
                        khronos_egl::RENDER_BUFFER,
                        // We don't want any of the buffering done by the driver, because we
                        // manage a swapchain on our side.
                        // Some drivers just fail on surface creation seeing `EGL_SINGLE_BUFFER`.
                        if cfg!(any(
                            target_os = "android",
                            target_os = "macos",
                            target_env = "ohos"
                        )) || cfg!(windows)
                            || self.wsi.kind == WindowKind::AngleX11
                        {
                            khronos_egl::BACK_BUFFER
                        } else {
                            khronos_egl::SINGLE_BUFFER
                        },
                    ]
                };
'''
if s.count(old_attrs) != 1:
    raise SystemExit(f'expected one EGL surface-attributes block, found {s.count(old_attrs)}')
s = s.replace(old_attrs, new_attrs, 1)

p.write_text(s)
print(f'Patched Linux ARM EGL presentation with leaked persistent 1280x960 DarkFate fbdev window in {p}')

# Test26: detail each GLES readback fallback so hit-effect traffic can be
# correlated by target/offset/length. This changes logging only.
adapter_matches = list(Path.home().glob('.cargo/registry/src/*/wgpu-hal-27.0.4/src/gles/adapter.rs'))
if len(adapter_matches) != 1:
    raise SystemExit(f'expected exactly one wgpu-hal 27.0.4 adapter.rs, found {adapter_matches}')

ap = adapter_matches[0]
a = ap.read_text()
old_fake = '            log::error!("Fake map");\n            let length = dst_data.len();\n'
new_fake = '''            let length = dst_data.len();
            log::error!("Fake map target={target:#x} offset={offset} length={length}");
'''
if a.count(old_fake) != 1:
    raise SystemExit(f'expected one Fake map block, found {a.count(old_fake)}')
a = a.replace(old_fake, new_fake, 1)
ap.write_text(a)
print(f'Patched Fake map diagnostics with target/offset/length in {ap}')
