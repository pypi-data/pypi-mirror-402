// main.rs
use pdflinkcheck_rust::analyze_pdf; // Matches the new [lib] name

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: pdflinkcheck-rust-cli <pdf_path>");
        std::process::exit(1);
    }

    match analyze_pdf(&args[1]) {
        Ok(result) => {
            if let Ok(json) = serde_json::to_string_pretty(&result) {
                println!("{}", json);
            }
        }
        Err(e) => {
            eprintln!("Error: {}", e);
            std::process::exit(1);
        }
    }
}
