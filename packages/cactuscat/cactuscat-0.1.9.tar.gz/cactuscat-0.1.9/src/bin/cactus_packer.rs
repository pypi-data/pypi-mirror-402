use std::fs;
use std::path::Path;
use serde::{Deserialize, Serialize};
use goblin::pe::PE;
use std::io::Write;

#[derive(Serialize, Deserialize, Debug)]
struct ManifestItem {
    name: String,
    path: String,
    #[serde(rename = "type")]
    item_type: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct Manifest {
    scripts: Vec<ManifestItem>,
    binaries: Vec<ManifestItem>,
    datas: Vec<ManifestItem>,
}

fn strip_binary(path: &Path) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let data = fs::read(path)?;
    if let Ok(_pe) = PE::parse(&data) {
        // Here we could perform more aggressive stripping if we had a PE writer
        // For now, we are just demonstrating the "Native Power" hook point
    }
    Ok(data)
}

fn is_prunable(name: &str) -> bool {
    let lower = name.to_lowercase();
    lower.contains("test") || 
    lower.contains("example") || 
    lower.ends_with(".dist-info") || 
    lower.ends_with(".egg-info") ||
    lower.ends_with(".pyi") ||
    lower.ends_with(".pdf") ||
    lower.contains("node_modules")
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        println!("Usage: cactus_packer <manifest.json> <output_bundle.cat>");
        return Ok(());
    }

    let manifest_path = &args[1];
    let output_path = &args[2];
    
    let manifest_data = fs::read_to_string(manifest_path)?;
    let manifest: Manifest = serde_json::from_str(&manifest_data)?;
    
    println!("--- CactusCat Native Packer (Rust Power) ---");
    println!("Aggressively pruning and packing dependencies...");

    let mut bundle_data = Vec::new();
    let mut header = Vec::new();

    // 1. Process Binaries
    for item in &manifest.binaries {
        if is_prunable(&item.name) { continue; }
        let src_path = Path::new(&item.path);
        if !src_path.exists() { continue; }
        
        let processed_data = strip_binary(src_path).unwrap_or_else(|_| fs::read(src_path).unwrap());
        let start_offset = bundle_data.len();
        let length = processed_data.len();
        bundle_data.extend_from_slice(&processed_data);
        header.push(format!("bin|{}|{}|{}", item.name, start_offset, length));
    }

    // 2. Process Scripts
    for item in &manifest.scripts {
        let src_path = Path::new(&item.path);
        if !src_path.exists() { continue; }
        
        let data = fs::read(src_path)?;
        let start_offset = bundle_data.len();
        let length = data.len();
        bundle_data.extend_from_slice(&data);
        header.push(format!("scr|{}|{}|{}", item.name, start_offset, length));
    }

    // 3. Process Datas
    for item in &manifest.datas {
        if is_prunable(&item.name) { continue; }
        let src_path = Path::new(&item.path);
        if !src_path.exists() { continue; }
        
        let data = fs::read(src_path)?;
        let start_offset = bundle_data.len();
        let length = data.len();
        bundle_data.extend_from_slice(&data);
        header.push(format!("dat|{}|{}|{}", item.name, start_offset, length));
    }

    let mut header_lines = Vec::new();
    if let Some(first) = manifest.scripts.first() {
        header_lines.push(format!("ENT|{}", first.name));
    }
    header_lines.extend(header);
    let header_str = header_lines.join("\n");
    let header_bytes = header_str.as_bytes();
    
    let mut final_out = fs::File::create(output_path)?;
    final_out.write_all(b"CAT\x01")?; 
    final_out.write_all(&(header_bytes.len() as u32).to_le_bytes())?;
    final_out.write_all(header_bytes)?;
    
    let mut encoder = zstd::stream::Encoder::new(final_out, 9)?;
    encoder.write_all(&bundle_data)?;
    encoder.finish()?;

    println!("✅ Archive created: {}", output_path);
    Ok(())
}
