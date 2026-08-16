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

# Test17-proven 16-byte fbdev native window. Replace only the normal Xlib/Xcb
# native-window construction; all non-Linux-ARM paths retain upstream behavior.
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
                let mut darkfate_fbdev_window = DarkFateFbdevWindow {
                    width16: config.extent.width as u16,
                    height16: config.extent.height as u16,
                    zero: 0,
                    width32: config.extent.width,
                    height32: config.extent.height,
                };
                let use_darkfate_fbdev =
                    cfg!(all(target_os = "linux", target_arch = "arm"));
                let native_window_ptr = match (self.wsi.kind, self.raw_window_handle) {
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xlib(handle)) => {
                        if use_darkfate_fbdev {
                            ptr::from_mut(&mut darkfate_fbdev_window).cast::<ffi::c_void>()
                        } else {
                            temp_xlib_handle = handle.window;
                            ptr::from_mut(&mut temp_xlib_handle).cast::<ffi::c_void>()
                        }
                    }
                    (WindowKind::AngleX11, Rwh::Xlib(handle)) => handle.window as *mut ffi::c_void,
                    (WindowKind::Unknown | WindowKind::X11, Rwh::Xcb(handle)) => {
                        if use_darkfate_fbdev {
                            ptr::from_mut(&mut darkfate_fbdev_window).cast::<ffi::c_void>()
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
print(f'Patched Linux ARM EGL presentation for DarkFate fbdev in {p}')
