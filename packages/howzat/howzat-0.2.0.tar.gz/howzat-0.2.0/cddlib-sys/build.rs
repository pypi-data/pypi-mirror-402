use std::collections::BTreeSet;
use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::num::NonZeroUsize;
use std::path::{Path, PathBuf};
use std::process::Command;

use flate2::read::GzDecoder;
use tar::Archive;

const CDDLIB_TAG: &str = "0.94n";
const BACKEND_FEATURES: &[&str] = &[
    "CARGO_FEATURE_F64",
    "CARGO_FEATURE_GMP",
    "CARGO_FEATURE_GMPRATIONAL",
];
const GMP_TAG: &str = "6.3.0";
const M4_TAG: &str = "1.4.20";
const PERF_FLAGS: &[&str] = &[
    "-O3",
    "-DNDEBUG",
    "-g0",
    "-fomit-frame-pointer",
];
const NATIVE_CPU_FLAGS: &[&str] = &["-march=native", "-mtune=native"];

fn vendor_dir() -> PathBuf {
    PathBuf::from(
        env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be provided by cargo"),
    )
    .join("vendor")
}

#[derive(Clone)]
struct CddLayout {
    archive_path: PathBuf,
    source_dir: PathBuf,
    build_dir: PathBuf,
    install_dir: PathBuf,
}

#[derive(Clone)]
struct GmpLayout {
    tag: String,
    archive_path: PathBuf,
    source_dir: PathBuf,
    build_dir: PathBuf,
    install_dir: PathBuf,
}

#[derive(Clone)]
struct GmpInstall {
    include_dir: PathBuf,
    lib_dir: PathBuf,
}

#[derive(Clone)]
struct M4Layout {
    archive_path: PathBuf,
    source_dir: PathBuf,
    build_dir: PathBuf,
    install_dir: PathBuf,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Backend {
    F64,
    GmpFloat,
    GmpRational,
}

impl Backend {
    fn cache_component(self) -> &'static str {
        match self {
            Backend::F64 => "f64",
            Backend::GmpFloat => "gmpfloat",
            Backend::GmpRational => "gmprational",
        }
    }

    fn lib_flavor(self) -> LibFlavor {
        match self {
            Backend::F64 => LibFlavor::F64,
            Backend::GmpFloat | Backend::GmpRational => LibFlavor::Gmp,
        }
    }
}

fn enabled_backends() -> Vec<Backend> {
    let mut backends = Vec::new();
    if env::var("CARGO_FEATURE_F64").is_ok() {
        backends.push(Backend::F64);
    }
    if env::var("CARGO_FEATURE_GMP").is_ok() {
        backends.push(Backend::GmpFloat);
    }
    if env::var("CARGO_FEATURE_GMPRATIONAL").is_ok() {
        backends.push(Backend::GmpRational);
    }
    backends
}

fn tools_backend(backends: &[Backend]) -> Option<Backend> {
    if env::var("CARGO_FEATURE_TOOLS").is_err() {
        return None;
    }
    if backends.contains(&Backend::GmpRational) {
        return Some(Backend::GmpRational);
    }
    if backends.contains(&Backend::GmpFloat) {
        return Some(Backend::GmpFloat);
    }
    if backends.contains(&Backend::F64) {
        return Some(Backend::F64);
    }
    None
}

fn main() {
    for feature in BACKEND_FEATURES {
        println!("cargo:rerun-if-env-changed={feature}");
    }
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_TOOLS");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_PIC");
    println!("cargo:rerun-if-env-changed=CARGO_ENCODED_RUSTFLAGS");
    println!("cargo:rerun-if-changed=build.rs");

    let backends = enabled_backends();
    if backends.is_empty() {
        panic!(
            "cddlib-sys: no numeric backend enabled; enable at least one of: f64, gmp, gmprational"
        );
    }
    let tools_backend = tools_backend(&backends);

    let needs_gmp = backends
        .iter()
        .any(|b| matches!(b, Backend::GmpFloat | Backend::GmpRational));

    let gmp_layout = needs_gmp.then_some(gmp_layout());
    if let Some(layout) = &gmp_layout {
        println!("cargo:rerun-if-changed={}", layout.archive_path.display());
    }
    let gmp_install = gmp_layout.as_ref().map(ensure_gmp);

    let header = "\
typedef __UINT8_TYPE__ uint8_t;\n\
typedef __UINT64_TYPE__ uint64_t;\n\
#include <stdint.h>\n\
#include <cddlib/setoper.h>\n\
#include <cddlib/cdd.h>\n";
    let out_dir = PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR must be provided by cargo"));

    println!("cargo:rustc-link-search=native={}", out_dir.display());

    if let Some(gmp) = &gmp_install {
        println!("cargo:rustc-link-search=native={}", gmp.lib_dir.display());
        println!("cargo:rustc-link-lib=gmp");
    }

    if env::var("CARGO_CFG_TARGET_FAMILY").as_deref() == Ok("unix") {
        println!("cargo:rustc-link-lib=m");
    }

    for backend in backends {
        let gmp_layout_ref = match backend {
            Backend::F64 => None,
            Backend::GmpFloat | Backend::GmpRational => gmp_layout.as_ref(),
        };
        let layout = cdd_layout(backend, gmp_layout_ref);
        println!("cargo:rerun-if-changed={}", layout.archive_path.display());

        let install_dir = ensure_cddlib(&layout, backend, gmp_install.as_ref());
        if tools_backend == Some(backend) {
            build_tools(&layout, backend, &install_dir, gmp_install.as_ref());
        }

        let include_root = install_dir.join("include");
        let mut builder = bindgen::Builder::default()
            .header_contents("cddlib_rs.h", header)
            .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
            .allowlist_function("dd_.*")
            .allowlist_type("dd_.*")
            .allowlist_var("dd_.*")
            .allowlist_function("set_.*")
            .allowlist_type("set_.*")
            .allowlist_var("set_.*")
            .allowlist_function("ddd_.*")
            .allowlist_function("mpq_.*")
            .allowlist_function("mpf_.*")
            .allowlist_function("__gmp.*")
            .allowlist_var("GMPRATIONAL");

        builder = builder
            .clang_arg("-x")
            .clang_arg("c")
            .clang_arg("-std=gnu99")
            .clang_arg(format!("--target={}", target_triple()));

        builder = apply_system_includes(builder);
        builder = apply_macos_sysroot(builder);
        builder = builder.clang_arg(format!("-I{}", include_root.display()));
        if let Some(gmp) = &gmp_install {
            builder = builder.clang_arg(format!("-I{}", gmp.include_dir.display()));
        }
        match backend {
            Backend::F64 => {}
            Backend::GmpFloat => {
                builder = builder.clang_arg("-DGMPFLOAT");
            }
            Backend::GmpRational => {
                builder = builder.clang_arg("-DGMPRATIONAL");
            }
        }

        let bindings = builder
            .generate()
            .expect("Unable to generate cddlib bindings with bindgen");

        let prefix = backend_symbol_prefix(backend);
        let bindings = add_link_name_attributes(&bindings.to_string(), prefix);
        let bindings_path = out_dir.join(bindings_filename(backend));
        fs::write(&bindings_path, bindings)
            .unwrap_or_else(|e| panic!("Couldn't write bindings {}: {e}", bindings_path.display()));

        let input_lib = cddlib_archive_path(&install_dir, backend);
        let output_lib = out_dir.join(format!("lib{}.a", backend_lib_name(backend)));
        prefix_archive_symbols(&input_lib, &output_lib, prefix);
        println!("cargo:rustc-link-lib=static={}", backend_lib_name(backend));
    }
}

fn build_tools(layout: &CddLayout, backend: Backend, install_dir: &Path, gmp: Option<&GmpInstall>) {
    let src_dir = layout.source_dir.join("src");
    let bin_dir = install_dir.join("bin");
    fs::create_dir_all(&bin_dir).expect("failed to create cddlib tools directory");
    let compiler = env::var("CC").unwrap_or_else(|_| "cc".to_string());
    let include_dir = install_dir.join("include");
    let cdd_lib_dir = cddlib_lib_dir(install_dir, backend);
    let mut base_args = vec![
        "-O2".to_string(),
        "-std=c99".to_string(),
        format!("-I{}", include_dir.display()),
        format!("-L{}", cdd_lib_dir.display()),
    ];
    if let Some(gmp) = gmp {
        base_args.push(format!("-I{}", gmp.include_dir.display()));
        base_args.push(format!("-L{}", gmp.lib_dir.display()));
    }
    let libs: Vec<String> = match backend {
        Backend::F64 => vec!["-lcdd".to_string()],
        Backend::GmpFloat | Backend::GmpRational => {
            vec!["-lcddgmp".to_string(), "-lgmp".to_string()]
        }
    };
    let tools = [
        "cddexec",
        "redcheck",
        "redexter",
        "redundancies",
        "redundancies_clarkson",
        "adjacency",
        "allfaces",
        "fourier",
        "lcdd",
        "projection",
        "scdd",
        "testcdd1",
        "testcdd2",
        "testlp1",
        "testlp2",
        "testlp3",
        "testshoot",
    ];
    for tool in tools {
        let src = src_dir.join(format!("{tool}.c"));
        if !src.exists() {
            continue;
        }
        let out = bin_dir.join(tool);
        let mut cmd = Command::new(&compiler);
        cmd.args(&base_args);
        cmd.arg(src);
        cmd.args(&libs);
        cmd.arg("-lm");
        cmd.arg("-o");
        cmd.arg(&out);
        let status = cmd
            .status()
            .unwrap_or_else(|e| panic!("failed to compile {tool}: {e}"));
        if !status.success() {
            panic!("{tool} build failed with status {status}");
        }
    }
    println!("cargo:rustc-env=CDDLIB_TOOLS_DIR={}", bin_dir.display());
}

fn bindings_filename(backend: Backend) -> &'static str {
    match backend {
        Backend::F64 => "bindings_f64.rs",
        Backend::GmpFloat => "bindings_gmpfloat.rs",
        Backend::GmpRational => "bindings_gmprational.rs",
    }
}

fn backend_lib_name(backend: Backend) -> &'static str {
    match backend {
        Backend::F64 => "cdd_f64",
        Backend::GmpFloat => "cdd_gmpfloat",
        Backend::GmpRational => "cdd_gmprational",
    }
}

fn backend_symbol_prefix(backend: Backend) -> &'static str {
    match backend {
        Backend::F64 => "cdd_f64_",
        Backend::GmpFloat => "cdd_gmpfloat_",
        Backend::GmpRational => "cdd_gmprational_",
    }
}

fn cddlib_lib_dir(install_dir: &Path, backend: Backend) -> PathBuf {
    let filename = match backend {
        Backend::F64 => "libcdd.a",
        Backend::GmpFloat | Backend::GmpRational => "libcddgmp.a",
    };
    for dir in ["lib", "lib64"] {
        let candidate = install_dir.join(dir);
        if candidate.join(filename).exists() {
            return candidate;
        }
    }
    panic!("missing {filename} under {}", install_dir.display());
}

fn cddlib_archive_path(install_dir: &Path, backend: Backend) -> PathBuf {
    let lib_dir = cddlib_lib_dir(install_dir, backend);
    match backend {
        Backend::F64 => lib_dir.join("libcdd.a"),
        Backend::GmpFloat | Backend::GmpRational => lib_dir.join("libcddgmp.a"),
    }
}

fn prefix_archive_symbols(input: &Path, output: &Path, prefix: &str) {
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent).expect("failed to create output directory for prefixed cddlib");
    }

    let symbols = defined_symbols(input);
    let redefine_path = output.with_extension("redefine.txt");
    let mut file = File::create(&redefine_path).unwrap_or_else(|e| {
        panic!(
            "failed to create symbol redefine file {}: {e}",
            redefine_path.display()
        )
    });
    for symbol in &symbols {
        writeln!(file, "{symbol} {prefix}{symbol}")
            .unwrap_or_else(|e| panic!("failed to write {}: {e}", redefine_path.display()));
    }

    let status = Command::new(objcopy_tool())
        .arg(format!("--redefine-syms={}", redefine_path.display()))
        .arg(input)
        .arg(output)
        .status()
        .unwrap_or_else(|e| panic!("failed to run objcopy: {e}"));
    if !status.success() {
        panic!("objcopy failed with status {status}");
    }

    let status = Command::new("ranlib")
        .arg(output)
        .status()
        .unwrap_or_else(|e| panic!("failed to run ranlib: {e}"));
    if !status.success() {
        panic!("ranlib failed with status {status}");
    }

    fs::remove_file(&redefine_path)
        .unwrap_or_else(|e| panic!("failed to remove {}: {e}", redefine_path.display()));
}

fn defined_symbols(archive: &Path) -> BTreeSet<String> {
    let output = Command::new(nm_tool())
        .arg("-g")
        .arg("--defined-only")
        .arg(archive)
        .output()
        .unwrap_or_else(|e| panic!("failed to run nm on {}: {e}", archive.display()));
    if !output.status.success() {
        panic!(
            "nm failed on {} with status {}",
            archive.display(),
            output.status
        );
    }
    let stdout = String::from_utf8(output.stdout).expect("nm output contained non-UTF8 bytes");

    let mut symbols = BTreeSet::new();
    for line in stdout.lines() {
        let line = line.trim();
        if line.is_empty() || line.ends_with(':') {
            continue;
        }
        let Some(symbol) = line.split_whitespace().last() else {
            continue;
        };
        symbols.insert(symbol.to_string());
    }

    symbols
}

fn objcopy_tool() -> &'static str {
    if env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        require_tool("llvm-objcopy");
        return "llvm-objcopy";
    }
    "objcopy"
}

fn nm_tool() -> &'static str {
    if env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        require_tool("llvm-nm");
        return "llvm-nm";
    }
    "nm"
}

fn require_tool(tool: &str) {
    if Command::new(tool).arg("--version").status().is_ok() {
        return;
    }
    panic!(
        "{tool} is required for cddlib-sys on this platform (install LLVM, e.g. `brew install llvm`)."
    );
}

fn apply_system_includes(mut builder: bindgen::Builder) -> bindgen::Builder {
    if env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        return builder;
    }
    for dir in system_include_dirs() {
        builder = builder
            .clang_arg("-isystem")
            .clang_arg(dir.display().to_string());
    }
    builder
}

fn apply_macos_sysroot(mut builder: bindgen::Builder) -> bindgen::Builder {
    if env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("macos") {
        return builder;
    }
    let Some(sdkroot) = macos_sdk_root() else {
        return builder;
    };
    builder = builder
        .clang_arg("-isysroot")
        .clang_arg(sdkroot.display().to_string());
    builder
}

fn macos_sdk_root() -> Option<PathBuf> {
    if let Ok(sdkroot) = env::var("SDKROOT") {
        let sdkroot = PathBuf::from(sdkroot);
        if sdkroot.exists() {
            return Some(sdkroot);
        }
    }
    let output = Command::new("xcrun")
        .args(["--sdk", "macosx", "--show-sdk-path"])
        .output()
        .ok()?;
    if !output.status.success() {
        return None;
    }
    let sdkroot = String::from_utf8(output.stdout).ok()?;
    let sdkroot = sdkroot.trim();
    if sdkroot.is_empty() {
        return None;
    }
    let sdkroot = PathBuf::from(sdkroot);
    sdkroot.exists().then_some(sdkroot)
}

fn system_include_dirs() -> Vec<PathBuf> {
    let mut dirs = Vec::new();
    for flag in ["-print-file-name=include", "-print-file-name=include-fixed"] {
        let path = gcc_include_path(flag);
        if path.exists() {
            dirs.push(path);
        }
    }
    if dirs.is_empty() {
        panic!(
            "failed to locate system include directories via gcc; install clang headers or a \
             working gcc toolchain"
        );
    }
    dirs
}

fn gcc_include_path(flag: &str) -> PathBuf {
    let output = Command::new("gcc")
        .arg(flag)
        .output()
        .unwrap_or_else(|e| panic!("failed to invoke gcc {flag}: {e}"));
    if !output.status.success() {
        panic!("gcc {flag} exited with {}", output.status);
    }
    let path = String::from_utf8_lossy(&output.stdout);
    let trimmed = path.trim();
    if trimmed.is_empty() {
        panic!("gcc {flag} returned an empty include path");
    }
    PathBuf::from(trimmed)
}

fn target_triple() -> String {
    env::var("TARGET").expect("TARGET must be provided by cargo for build scripts")
}

fn add_link_name_attributes(bindings: &str, prefix: &str) -> String {
    let mut out = String::with_capacity(bindings.len());
    let mut brace_depth: i32 = 0;
    let mut extern_depth: Option<i32> = None;

    for line in bindings.lines() {
        let trimmed = line.trim_start();
        let indent = &line[..line.len() - trimmed.len()];

        let in_extern = extern_depth.is_some_and(|depth| brace_depth >= depth);
        if in_extern {
            if let Some(name) = trimmed
                .strip_prefix("pub fn ")
                .and_then(|rest| rest.split_once('(').map(|(name, _)| name.trim()))
            {
                if is_cddlib_symbol(name) {
                    out.push_str(indent);
                    out.push_str(&format!("#[link_name = \"{prefix}{name}\"]\n"));
                }
            } else if trimmed.starts_with("pub static") {
                let mut parts = trimmed.split_whitespace();
                let _pub = parts.next();
                let _static = parts.next();
                let next = parts.next();
                let name = match next {
                    Some("mut") => parts.next(),
                    other => other,
                };
                if let Some(name) = name.map(|s| s.trim_end_matches(':'))
                    && is_cddlib_symbol(name)
                {
                    out.push_str(indent);
                    out.push_str(&format!("#[link_name = \"{prefix}{name}\"]\n"));
                }
            }
        }

        out.push_str(line);
        out.push('\n');

        brace_depth += line.bytes().filter(|&b| b == b'{').count() as i32;
        brace_depth -= line.bytes().filter(|&b| b == b'}').count() as i32;

        if trimmed.starts_with("extern \"C\" {") || trimmed.starts_with("unsafe extern \"C\" {") {
            extern_depth = Some(brace_depth);
        }
        if extern_depth.is_some_and(|depth| brace_depth < depth) {
            extern_depth = None;
        }
    }
    out
}

fn is_cddlib_symbol(name: &str) -> bool {
    name.starts_with("dd_") || name.starts_with("set_") || name.starts_with("ddd_")
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum LibFlavor {
    F64,
    Gmp,
}

fn ensure_cddlib(layout: &CddLayout, backend: Backend, gmp: Option<&GmpInstall>) -> PathBuf {
    if has_backend_lib(&layout.install_dir, backend) {
        return layout.install_dir.clone();
    }
    ensure_cdd_source(layout);
    if backend == Backend::GmpFloat {
        patch_gmpfloat_sources(&layout.source_dir);
    }
    build_cddlib(layout, backend, gmp)
}

fn ensure_cdd_source(layout: &CddLayout) -> PathBuf {
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    if let Some(parent) = layout.source_dir.parent() {
        fs::create_dir_all(parent).expect("failed to create cddlib source parent directory");
    }
    let root = layout
        .source_dir
        .parent()
        .unwrap_or_else(|| panic!("missing parent for {}", layout.source_dir.display()));
    extract_archive(&layout.archive_path, root);
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    panic!(
        "cddlib source tree not found under {} after extraction",
        layout.source_dir.display()
    );
}

fn patch_gmpfloat_sources(root: &Path) {
    let lib_src = root.join("lib-src");
    let replacements = [
        (
            lib_src.join("cddmp.c"),
            "mpf_set_si(dd_minusone,-1L,1U);",
            "mpf_set_si(dd_minusone,-1L);",
        ),
        (
            lib_src.join("cddmp_f.c"),
            "mpf_set_si(ddf_minusone,-1L,1U);",
            "mpf_set_si(ddf_minusone,-1L);",
        ),
        (
            lib_src.join("cddmp.h"),
            "#define dd_set_si2(a, b, c)     mpf_set_si(a,b,c)    /* gmp 3.1 or higher */",
            "#define dd_set_si2(a, b, c)     do { mpf_set_si(a,b); mpf_div_ui(a,a,c); } while (0)",
        ),
        (
            lib_src.join("cddmp_f.h"),
            "#define ddf_set_si2(a, b, c)     mpf_set_si(a,b,c)    /* gmp 3.1 or higher */",
            "#define ddf_set_si2(a, b, c)     do { mpf_set_si(a,b); mpf_div_ui(a,a,c); } while (0)",
        ),
    ];
    for (path, needle, replacement) in replacements {
        if path.exists() {
            replace_once(&path, needle, replacement);
        }
    }
}

fn build_cddlib(layout: &CddLayout, backend: Backend, gmp: Option<&GmpInstall>) -> PathBuf {
    if has_backend_lib(&layout.install_dir, backend) {
        return layout.install_dir.clone();
    }

    fs::create_dir_all(&layout.build_dir).expect("failed to create cddlib build directory");

    let mut configure = Command::new(layout.source_dir.join("configure"));
    let needs_pic = env::var_os("CARGO_FEATURE_PIC").is_some();
    let perf_flags = if needs_pic {
        format!("{} -fPIC", perf_flag_string())
    } else {
        perf_flag_string()
    };
    configure
        .arg(format!("--prefix={}", layout.install_dir.display()))
        .arg("--enable-shared=no")
        .arg("--enable-static=yes")
        .args(needs_pic.then_some("--with-pic"))
        .current_dir(&layout.build_dir)
        .env("CFLAGS", &perf_flags)
        .env("CXXFLAGS", &perf_flags);
    if matches!(backend, Backend::GmpFloat | Backend::GmpRational) {
        let gmp = gmp.expect("GMP backend requested without GMP build info");
        let cppflags = extend_with_env("CPPFLAGS", format!("-I{}", gmp.include_dir.display()));
        configure.env("CPPFLAGS", cppflags);
        let ldflags = extend_with_env("LDFLAGS", format!("-L{}", gmp.lib_dir.display()));
        configure.env("LDFLAGS", ldflags);
    }
    run(&mut configure, "cddlib configure failed");

    if backend == Backend::GmpFloat {
        patch_gmpfloat_sources(&layout.build_dir);
        rewrite_gmp_makefiles(&layout.build_dir);
    }

    let jobs = parallel_jobs();
    let mut make = Command::new("make");
    apply_parallel(&mut make, jobs);
    make.current_dir(&layout.build_dir);
    run(&mut make, "cddlib make failed");

    let mut make_install = Command::new("make");
    make_install
        .arg("install")
        .current_dir(&layout.build_dir)
        .env("CMAKE_BUILD_PARALLEL_LEVEL", jobs.to_string());
    apply_parallel(&mut make_install, jobs);
    run(&mut make_install, "cddlib make install failed");

    if !has_backend_lib(&layout.install_dir, backend) {
        panic!(
            "cddlib build did not produce the requested backend ({:?}) under {}",
            backend,
            layout.install_dir.display()
        );
    }

    layout.install_dir.clone()
}

fn cdd_layout(backend: Backend, gmp: Option<&GmpLayout>) -> CddLayout {
    let archive_path = vendor_dir().join(format!("cddlib-{CDDLIB_TAG}.tar.gz"));
    if !archive_path.is_file() {
        panic!(
            "missing vendored cddlib archive at {}",
            archive_path.display()
        );
    }
    let cache_root = cache_root();
    let needs_pic = env::var_os("CARGO_FEATURE_PIC").is_some();
    let dir_key = match gmp {
        Some(gmp_layout) => format!(
            "{}-{}-{}{}",
            sanitize_component(CDDLIB_TAG),
            backend.cache_component(),
            sanitize_component(&gmp_layout.tag),
            if needs_pic { "-pic" } else { "" },
        ),
        None => format!(
            "{}-{}{}",
            sanitize_component(CDDLIB_TAG),
            backend.cache_component(),
            if needs_pic { "-pic" } else { "" },
        ),
    };
    let root = cache_root.join(dir_key);
    CddLayout {
        archive_path,
        source_dir: root.join(format!("cddlib-{CDDLIB_TAG}")),
        build_dir: root.join("build"),
        install_dir: root.join("install"),
    }
}

fn gmp_layout() -> GmpLayout {
    let archive_path = vendor_dir().join(format!("gmp-{GMP_TAG}.tar.gz"));
    if !archive_path.is_file() {
        panic!("missing vendored gmp archive at {}", archive_path.display());
    }
    let cache_root = cache_root();
    let root = cache_root.join(format!("gmp-{}", sanitize_component(GMP_TAG)));
    GmpLayout {
        tag: GMP_TAG.to_string(),
        archive_path,
        source_dir: root.join(format!("gmp-{GMP_TAG}")),
        build_dir: root.join("build"),
        install_dir: root.join("install"),
    }
}

fn ensure_m4() -> PathBuf {
    if let Some(bin) = find_in_path("m4") {
        return bin;
    }
    let layout = m4_layout();
    println!("cargo:rerun-if-changed={}", layout.archive_path.display());
    if let Some(bin) = m4_install_if_present(&layout.install_dir) {
        return bin;
    }
    ensure_m4_source(&layout);
    build_m4(&layout)
}

fn m4_layout() -> M4Layout {
    let archive_path = vendor_dir().join(format!("m4-{M4_TAG}.tar.gz"));
    if !archive_path.is_file() {
        panic!("missing vendored m4 archive at {}", archive_path.display());
    }
    let cache_root = cache_root();
    let dir_key = format!("m4-{}", sanitize_component(M4_TAG));
    let root = cache_root.join(dir_key);
    M4Layout {
        archive_path,
        source_dir: root.join(format!("m4-{M4_TAG}")),
        build_dir: root.join("build"),
        install_dir: root.join("install"),
    }
}

fn m4_install_if_present(root: &Path) -> Option<PathBuf> {
    let bin = root.join("bin").join("m4");
    bin.is_file().then_some(bin)
}

fn ensure_m4_source(layout: &M4Layout) -> PathBuf {
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    if let Some(parent) = layout.source_dir.parent() {
        fs::create_dir_all(parent).expect("failed to create m4 source parent directory");
    }
    let root = layout
        .source_dir
        .parent()
        .unwrap_or_else(|| panic!("missing parent for {}", layout.source_dir.display()));
    extract_archive(&layout.archive_path, root);
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    panic!(
        "m4 source tree not found under {} after extraction",
        layout.source_dir.display()
    );
}

fn build_m4(layout: &M4Layout) -> PathBuf {
    if let Some(bin) = m4_install_if_present(&layout.install_dir) {
        return bin;
    }

    fs::create_dir_all(&layout.build_dir).expect("failed to create m4 build directory");

    let mut configure = Command::new(layout.source_dir.join("configure"));
    configure
        .arg(format!("--prefix={}", layout.install_dir.display()))
        .arg("--enable-shared=no")
        .arg("--enable-static=yes")
        .current_dir(&layout.build_dir)
        .env("CFLAGS", perf_flag_string());
    run(&mut configure, "m4 configure failed");

    let jobs = parallel_jobs();
    let mut make = Command::new("make");
    apply_parallel(&mut make, jobs);
    make.current_dir(&layout.build_dir);
    run(&mut make, "m4 make failed");

    let mut make_install = Command::new("make");
    make_install
        .arg("install")
        .current_dir(&layout.build_dir)
        .env("CMAKE_BUILD_PARALLEL_LEVEL", jobs.to_string());
    apply_parallel(&mut make_install, jobs);
    run(&mut make_install, "m4 make install failed");

    m4_install_if_present(&layout.install_dir).unwrap_or_else(|| {
        panic!(
            "m4 build did not produce m4 under {}",
            layout.install_dir.display()
        )
    })
}

fn ensure_gmp(layout: &GmpLayout) -> GmpInstall {
    if let Some(install) = gmp_install_if_present(&layout.install_dir) {
        return install;
    }
    ensure_gmp_source(layout);
    let m4 = ensure_m4();
    build_gmp(layout, &m4)
}

fn gmp_install_if_present(root: &Path) -> Option<GmpInstall> {
    let include_dir = root.join("include");
    if !include_dir.join("gmp.h").exists() {
        return None;
    }
    gmp_available_lib_dir(root).map(|lib_dir| GmpInstall {
        include_dir,
        lib_dir,
    })
}

fn gmp_available_lib_dir(root: &Path) -> Option<PathBuf> {
    ["lib", "lib64"]
        .into_iter()
        .map(|dir| root.join(dir))
        .find(|path| path.join("libgmp.a").exists())
}

fn ensure_gmp_source(layout: &GmpLayout) -> PathBuf {
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    if let Some(parent) = layout.source_dir.parent() {
        fs::create_dir_all(parent).expect("failed to create gmp source parent directory");
    }
    let root = layout
        .source_dir
        .parent()
        .unwrap_or_else(|| panic!("missing parent for {}", layout.source_dir.display()));
    extract_archive(&layout.archive_path, root);
    if layout.source_dir.join("configure").exists() {
        return layout.source_dir.clone();
    }
    panic!(
        "gmp source tree not found under {} after extraction",
        layout.source_dir.display()
    );
}

fn build_gmp(layout: &GmpLayout, m4: &Path) -> GmpInstall {
    if let Some(install) = gmp_install_if_present(&layout.install_dir) {
        return install;
    }

    fs::create_dir_all(&layout.build_dir).expect("failed to create gmp build directory");

    let mut configure = Command::new(layout.source_dir.join("configure"));
    configure
        .arg(format!("--prefix={}", layout.install_dir.display()))
        .arg("--enable-shared=no")
        .arg("--enable-static=yes")
        .arg("--with-pic")
        .current_dir(&layout.build_dir)
        .env("CFLAGS", gmp_cflag_string())
        .env("M4", m4);
    run(&mut configure, "gmp configure failed");

    let jobs = parallel_jobs();
    let mut make = Command::new("make");
    apply_parallel(&mut make, jobs);
    make.current_dir(&layout.build_dir).env("M4", m4);
    run(&mut make, "gmp make failed");

    let mut make_install = Command::new("make");
    make_install
        .arg("install")
        .current_dir(&layout.build_dir)
        .env("CMAKE_BUILD_PARALLEL_LEVEL", jobs.to_string())
        .env("M4", m4);
    apply_parallel(&mut make_install, jobs);
    run(&mut make_install, "gmp make install failed");

    gmp_install_if_present(&layout.install_dir).unwrap_or_else(|| {
        panic!(
            "gmp build did not produce libgmp.a under {}",
            layout.install_dir.display()
        )
    })
}

fn cache_root() -> PathBuf {
    let target_root = target_root();
    let pkg = sanitize_component(
        &env::var("CARGO_PKG_NAME").expect("CARGO_PKG_NAME must be provided by cargo"),
    );
    let target_triple = sanitize_component(
        &env::var("TARGET").expect("TARGET must be provided by cargo for build scripts"),
    );
    target_root.join("build-deps").join(pkg).join(target_triple)
}

fn target_root() -> PathBuf {
    if let Ok(dir) = env::var("CARGO_TARGET_DIR") {
        return PathBuf::from(dir);
    }
    let out_dir = PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR must be provided by cargo"));
    if let Some(target_dir) = out_dir
        .ancestors()
        .find(|p| p.file_name().is_some_and(|name| name == "target"))
    {
        return target_dir.to_path_buf();
    }
    PathBuf::from(
        env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be provided by cargo"),
    )
    .join("target")
}

fn sanitize_component(value: &str) -> String {
    value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch } else { '-' })
        .collect()
}

fn find_in_path(tool: &str) -> Option<PathBuf> {
    env::var_os("PATH").and_then(|paths| {
        env::split_paths(&paths)
            .map(|dir| dir.join(tool))
            .find(|candidate| candidate.is_file())
    })
}

fn available_lib_dirs(root: &Path) -> Vec<(LibFlavor, PathBuf)> {
    let mut dirs = Vec::new();
    for dir in ["lib", "lib64"] {
        let path = root.join(dir);
        if path.join("libcdd.a").exists() {
            dirs.push((LibFlavor::F64, path.clone()));
        }
        if path.join("libcddgmp.a").exists() {
            dirs.push((LibFlavor::Gmp, path.clone()));
        }
    }
    dirs
}

fn has_backend_lib(root: &Path, backend: Backend) -> bool {
    let flavor = backend.lib_flavor();
    available_lib_dirs(root)
        .into_iter()
        .any(|(found, _)| found == flavor)
}

fn replace_once(path: &Path, needle: &str, replacement: &str) {
    let contents = fs::read_to_string(path)
        .unwrap_or_else(|e| panic!("failed to read {}: {e}", path.display()));
    if contents.contains(needle) {
        let updated = contents.replace(needle, replacement);
        fs::write(path, updated)
            .unwrap_or_else(|e| panic!("failed to write {}: {e}", path.display()));
    } else if !contents.contains(replacement) {
        panic!(
            "expected to replace {needle} in {}, but it was not found",
            path.display()
        );
    }
}

fn rewrite_gmp_makefiles(build_dir: &Path) {
    let lib_src_makefile = build_dir.join("lib-src/Makefile");
    rewrite_makefile_flag(&lib_src_makefile, "-DGMPRATIONAL", "-DGMPFLOAT");

    let src_makefile = build_dir.join("src/Makefile");
    rewrite_makefile_flag(&src_makefile, "-DGMPRATIONAL", "-DGMPFLOAT");
}

fn rewrite_makefile_flag(path: &Path, needle: &str, replacement: &str) {
    replace_once(path, needle, replacement);
}

fn extend_with_env(key: &str, value: String) -> String {
    match env::var(key) {
        Ok(existing) if !existing.is_empty() => format!("{value} {existing}"),
        _ => value,
    }
}

fn gmp_cflag_string() -> String {
    let mut flags = Vec::with_capacity(1 + PERF_FLAGS.len() + native_cpu_flags().len());
    flags.push("-std=gnu99");
    flags.extend(perf_flags());
    flags.join(" ")
}

fn perf_flag_string() -> String {
    perf_flags().collect::<Vec<_>>().join(" ")
}

fn perf_flags() -> impl Iterator<Item = &'static str> {
    PERF_FLAGS
        .iter()
        .copied()
        .chain(native_cpu_flags().iter().copied())
}

fn native_cpu_flags() -> &'static [&'static str] {
    if wants_native_cpu_flags() {
        NATIVE_CPU_FLAGS
    } else {
        &[]
    }
}

fn wants_native_cpu_flags() -> bool {
    let Ok(flags) = env::var("CARGO_ENCODED_RUSTFLAGS") else {
        return false;
    };

    let mut last_target_cpu = None;
    let mut saw_dash_c = false;

    for token in flags.split('\u{1f}') {
        if saw_dash_c {
            if let Some(cpu) = token.strip_prefix("target-cpu=") {
                last_target_cpu = Some(cpu);
            }
            saw_dash_c = false;
        }

        if token == "-C" {
            saw_dash_c = true;
            continue;
        }

        if let Some(cpu) = token.strip_prefix("-Ctarget-cpu=") {
            last_target_cpu = Some(cpu);
            continue;
        }
        if let Some(cpu) = token.strip_prefix("target-cpu=") {
            last_target_cpu = Some(cpu);
        }
    }

    last_target_cpu == Some("native")
}

fn parallel_jobs() -> usize {
    env::var("NUM_JOBS")
        .ok()
        .and_then(|s| s.parse::<NonZeroUsize>().ok())
        .map(NonZeroUsize::get)
        .or_else(|| {
            std::thread::available_parallelism()
                .ok()
                .map(NonZeroUsize::get)
        })
        .unwrap_or(1)
}

fn apply_parallel(cmd: &mut Command, jobs: usize) {
    if jobs > 1 {
        cmd.arg(format!("-j{jobs}"));
    }
}

fn extract_archive(archive_path: &Path, out_dir: &Path) {
    let file = File::open(archive_path)
        .unwrap_or_else(|e| panic!("failed to open {}: {e}", archive_path.display()));
    let gz = GzDecoder::new(file);
    let mut archive = Archive::new(gz);
    archive.unpack(out_dir).unwrap_or_else(|e| {
        panic!(
            "failed to extract archive {} into {}: {e}",
            archive_path.display(),
            out_dir.display()
        )
    });
}

fn run(cmd: &mut Command, err: &str) {
    let status = cmd.status().unwrap_or_else(|e| panic!("{err}: {e}"));
    if !status.success() {
        panic!("{err}: status {status}");
    }
}
