fn main() {
    // Empty build script to avoid icon issues
    println!("cargo:rerun-if-changed=tauri.conf.json");
}
