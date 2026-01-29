use pyo3::prelude::*;
use std::ffi::CString;
use std::fs;
use std::io::Read;
use aes_gcm::{
    aead::{Aead, KeyInit, Payload},
    Aes256Gcm, Nonce,
};
use tempfile::TempDir;

fn main() -> PyResult<()> {
    // 1. Decryption (Stage 1)
    let key_hex = option_env!("CACTUS_KEY").unwrap_or("0000000000000000000000000000000000000000000000000000000000000000");
    let key_bytes = hex::decode(key_hex).expect("Invalid hex key");
    let key = aes_gcm::Key::<Aes256Gcm>::from_slice(&key_bytes);

    let payload_bytes: &[u8] = include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/.cactuscat_payload"));
    if payload_bytes.len() < 12 { 
        if cfg!(debug_assertions) {
            println!("DEBUG: Payload missing or dummy. Skipping execution.");
            return Ok(());
        }
        panic!("Payload missing"); 
    }

    let (nonce_bytes, encrypted_data) = payload_bytes.split_at(12);
    let cipher = Aes256Gcm::new(key);
    let decrypted = cipher.decrypt(Nonce::from_slice(nonce_bytes), Payload {
        msg: encrypted_data,
        aad: b"cactuscat-native-v1",
    }).expect("Decryption failed");

    // 2. Check Magic (Stage 2: Archive or Single Script)
    if decrypted.starts_with(b"CAT\x01") {
        run_native_bundle(decrypted)
    } else {
        run_single_script(decrypted)
    }
}

fn run_single_script(decrypted: Vec<u8>) -> PyResult<()> {
    let code_str = String::from_utf8(decrypted).expect("Invalid UTF-8");
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let sys = py.import("sys")?;
        sys.getattr("path")?.call_method1("append", ("./",))?;
        py.run(CString::new(code_str).unwrap().as_c_str(), None, None)?;
        Ok(())
    })
}

fn run_native_bundle(bundle: Vec<u8>) -> PyResult<()> {
    // 3. Unpack and Prune (Visual Environment)
    let mut cursor = std::io::Cursor::new(&bundle[4..]);
    let mut hlen_buf = [0u8; 4];
    cursor.read_exact(&mut hlen_buf).unwrap();
    let hlen = u32::from_le_bytes(hlen_buf) as usize;
    
    let mut header_bytes = vec![0u8; hlen];
    cursor.read_exact(&mut header_bytes).unwrap();
    let header = String::from_utf8(header_bytes).unwrap();
    
    // Zstd Decompress bulk data
    let mut zstd_reader = zstd::stream::Decoder::new(cursor).unwrap();
    let mut bulk_data = Vec::new();
    zstd_reader.read_to_end(&mut bulk_data).unwrap();

    // Setup Temp Shielded Environment
    let temp_dir = TempDir::new().unwrap();
    let env_path = temp_dir.path();
    
    let mut entry_point = String::new();

    for line in header.lines() {
        let parts: Vec<&str> = line.split('|').collect();
        if parts[0] == "ENT" {
            entry_point = parts[1].to_string();
            continue;
        }
        
        if parts.len() < 4 { continue; }
        let (_type, name, offset_str, len_str) = (parts[0], parts[1], parts[2], parts[3]);
        let offset = offset_str.parse::<usize>().unwrap();
        let len = len_str.parse::<usize>().unwrap();
        
        let file_data = &bulk_data[offset..offset+len];
        let file_path = env_path.join(name);
        if let Some(parent) = file_path.parent() {
            fs::create_dir_all(parent).unwrap();
        }
        fs::write(&file_path, file_data).unwrap();
    }

    // 4. Runtime Injected Shield
    pyo3::prepare_freethreaded_python();
    Python::with_gil(|py| {
        let sys = py.import("sys")?;
        let os = py.import("os")?;
        
        // Inject Default Engine if bundled
        if let Some(engine) = option_env!("CACTUS_DEFAULT_ENGINE") {
            let env = os.getattr("environ")?;
            env.call_method1("__setitem__", ("CACTUS_ENGINE", engine))?;
        }

        let path = sys.getattr("path")?;
        path.call_method1("insert", (0, env_path.to_str().unwrap()))?;
        
        // Execute entry point
        let entry_file = env_path.join(&entry_point);
        let code = fs::read_to_string(entry_file).unwrap();
        py.run(CString::new(code).unwrap().as_c_str(), None, None)?;
        
        Ok(())
    })
}
