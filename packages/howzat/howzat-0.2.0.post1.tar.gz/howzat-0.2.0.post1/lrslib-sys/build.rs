use std::env;
use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::Command;

use flate2::read::GzDecoder;
use tar::Archive;

const LRSLIB_TAG: &str = "073a";
const PERF_FLAGS: &[&str] = &[
    "-O3",
    "-DNDEBUG",
    "-g0",
    "-fomit-frame-pointer",
];
const NATIVE_CPU_FLAGS: &[&str] = &["-march=native", "-mtune=native"];

#[derive(Clone)]
struct LrsLayout {
    archive_path: PathBuf,
    source_dir: PathBuf,
}

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=CARGO_FEATURE_GMP");
    println!("cargo:rerun-if-env-changed=CARGO_ENCODED_RUSTFLAGS");

    let layout = lrs_layout();
    println!("cargo:rerun-if-changed={}", layout.archive_path.display());

    ensure_lrslib_source(&layout);
    build_lrslib(&layout);
    generate_bindings(&layout);

    if env::var("CARGO_CFG_TARGET_FAMILY").as_deref() == Ok("unix") {
        println!("cargo:rustc-link-lib=m");
    }
}

fn vendor_dir() -> PathBuf {
    PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be provided"))
        .join("vendor")
}

fn lrs_layout() -> LrsLayout {
    let archive_path = vendor_dir().join(format!("lrslib-{LRSLIB_TAG}.tar.gz"));
    if !archive_path.is_file() {
        panic!(
            "missing vendored lrslib archive at {}",
            archive_path.display()
        );
    }

    let cache_root = cache_root();
    let dir_key = sanitize_component(LRSLIB_TAG);
    let root = cache_root.join(dir_key);

    LrsLayout {
        archive_path,
        source_dir: root.join(format!("lrslib-{LRSLIB_TAG}")),
    }
}

fn ensure_lrslib_source(layout: &LrsLayout) -> PathBuf {
    if layout.source_dir.join("lrslib.c").exists() {
        return layout.source_dir.clone();
    }

    if let Some(parent) = layout.source_dir.parent() {
        fs::create_dir_all(parent).expect("failed to create lrslib source parent directory");
    }

    let root = layout
        .source_dir
        .parent()
        .unwrap_or_else(|| panic!("missing parent for {}", layout.source_dir.display()));

    extract_archive(&layout.archive_path, root);

    if layout.source_dir.join("lrslib.c").exists() {
        return layout.source_dir.clone();
    }

    panic!(
        "lrslib source tree not found under {} after extraction",
        layout.source_dir.display()
    );
}

fn build_lrslib(layout: &LrsLayout) {
    let arith_dir = layout.source_dir.join("lrsarith-011");
    let use_gmp = env::var_os("CARGO_FEATURE_GMP").is_some();

    let mut sources = vec![
        layout.source_dir.join("lrslib.c"),
        layout.source_dir.join("lrsdriver.c"),
    ];
    if use_gmp {
        sources.push(arith_dir.join("lrsgmp.c"));
        sources.push(arith_dir.join("mini-gmp.c"));
    } else {
        sources.push(arith_dir.join("lrslong.c"));
    }

    for src in &sources {
        if !src.is_file() {
            panic!("missing lrslib source file {}", src.display());
        }
    }

    let mut build = cc::Build::new();
    build
        // Vendored C code: don't spam downstream builds with warnings.
        .warnings(false)
        .files(&sources)
        .include(&layout.source_dir)
        .include(&arith_dir)
        .flag_if_supported("-std=gnu99")
        // Build lrslib single-threaded: do NOT define PLRS/MPLRS or pass -fopenmp.
        .define("LRS_QUIET", None)
        // lrslib is primarily a CLI tool; it installs process-wide signal handlers
        // (SIGINT/SIGTERM/etc.) unless SIGNALS is defined. We do not want a library
        // to override the host application's signal behavior.
        .define("SIGNALS", None);

    if use_gmp {
        // Use the bundled mini-gmp backend (no external system dependency).
        build.define("GMP", None).define("MGMP", None);
    } else {
        // Exact fixed-width arithmetic (fast, but can overflow on hard instances).
        //
        // We default to 128-bit if the target supports it.
        build.define("LRSLONG", None).define("SAFE", None);
        if env::var("CARGO_CFG_TARGET_POINTER_WIDTH").as_deref() == Ok("64") {
            build.define("B128", None);
        }
    }

    for flag in PERF_FLAGS {
        build.flag(flag);
    }
    if wants_native_cpu_flags() {
        for flag in NATIVE_CPU_FLAGS {
            build.flag(flag);
        }
    }

    build.compile("lrslib");
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

fn generate_bindings(layout: &LrsLayout) {
    let arith_dir = layout.source_dir.join("lrsarith-011");
    let use_gmp = env::var_os("CARGO_FEATURE_GMP").is_some();

    let header = "\
typedef __UINT8_TYPE__ uint8_t;\n\
typedef __UINT64_TYPE__ uint64_t;\n\
#include <stdint.h>\n\
#include <stdio.h>\n\
#include \"lrsrestart.h\"\n\
#include \"lrslib.h\"\n";

    let builder = bindgen::Builder::default()
        .header_contents("lrslib_rs.h", header)
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        // Core lrslib lifecycle + enumeration.
        .allowlist_function("lrs_init")
        .allowlist_function("lrs_close")
        .allowlist_function("lrs_alloc_dat")
        .allowlist_function("lrs_free_dat")
        .allowlist_function("lrs_alloc_dic")
        .allowlist_function("lrs_free_dic")
        .allowlist_function("lrs_getfirstbasis")
        .allowlist_function("lrs_getnextbasis")
        .allowlist_function("lrs_getsolution")
        .allowlist_function("lrs_getvertex")
        .allowlist_function("lrs_getray")
        .allowlist_function("lrs_set_row")
        .allowlist_function("lrs_set_row_mp")
        // Minimal arithmetic helpers for setting/printing numbers.
        .allowlist_function("lrs_alloc_mp_vector")
        .allowlist_function("lrs_clear_mp_vector")
        .allowlist_function("lrs_alloc_mp_matrix")
        .allowlist_function("lrs_clear_mp_matrix")
        .allowlist_function("atomp")
        .allowlist_function("rattodouble")
        .allowlist_function("cpmp")
        .allowlist_function("cprat")
        // A couple of constants used when loading rows.
        .allowlist_var("GE")
        .allowlist_var("EQ")
        .allowlist_var("TRUE")
        .allowlist_var("FALSE")
        // Key lrslib data structures.
        .allowlist_type("lrs_dic")
        .allowlist_type("lrs_dat")
        .allowlist_type("lrs_restart_dat")
        .allowlist_type("lrs_mp")
        .allowlist_type("lrs_mp_t")
        .allowlist_type("lrs_mp_vector")
        .allowlist_type("lrs_mp_matrix")
        // Keep bindgen honest about our build-time configuration.
        .clang_arg("-x")
        .clang_arg("c")
        .clang_arg("-std=gnu99")
        .clang_arg(format!("--target={}", target_triple()))
        .clang_arg(format!("-I{}", layout.source_dir.display()))
        .clang_arg(format!("-I{}", arith_dir.display()))
        .clang_arg("-DLRS_QUIET")
        .clang_arg("-DSIGNALS");

    let mut builder = apply_system_includes(builder);
    builder = apply_macos_sysroot(builder);

    let builder = if use_gmp {
        builder.clang_arg("-DGMP").clang_arg("-DMGMP")
    } else {
        let builder = builder.clang_arg("-DLRSLONG").clang_arg("-DSAFE");
        if env::var("CARGO_CFG_TARGET_POINTER_WIDTH").as_deref() == Ok("64") {
            builder.clang_arg("-DB128")
        } else {
            builder
        }
    };

    let bindings = builder
        .generate()
        .expect("Unable to generate lrslib bindings with bindgen");

    let out_path = PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR must be provided"));
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
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

fn cache_root() -> PathBuf {
    let target_root = target_root();
    let pkg = sanitize_component(
        &env::var("CARGO_PKG_NAME").expect("CARGO_PKG_NAME must be provided by cargo"),
    );
    let target_triple = sanitize_component(
        &target_triple(),
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

    PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR must be provided"))
        .join("target")
}

fn sanitize_component(value: &str) -> String {
    value
        .chars()
        .map(|ch| if ch.is_ascii_alphanumeric() { ch } else { '-' })
        .collect()
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
