mod utils;

use dotenv::dotenv;
use fers_calculations::analysis::calculate_from_file_internal_with_tier;
use fers_calculations::limits::LicenseTier;
use std::fs;
use std::io::Write;
use utoipa::OpenApi;

use utils::logging;

use fers_calculations::models::fers::fers::FERS;

#[derive(OpenApi)]
#[openapi(
    components(schemas(FERS)),
    paths(),
    info(
        title = "FERS Structural Analysis API",
        version = "0.1.0",
        description = "OpenAPI for FERS structural analysis application."
    )
)]
struct ApiDoc;

fn print_usage_and_exit(exit_code: i32) -> ! {
    eprintln!(
        "Usage:
  main [--input <path> | <path>] [--openapi [path]]

Examples:
  main CrossCheckModel.json
  main --input CrossCheckModel.json
  main --openapi
  main --openapi openapi.json

Notes:
  --openapi will generate the OpenAPI spec to the given path (default: openapi.json)
  and then exit without running an analysis."
    );
    std::process::exit(exit_code);
}

fn main() {
    logging::init_logger();
    dotenv().ok();

    let mut input_json_path_opt: Option<String> = None;
    let mut openapi_out_opt: Option<String> = None;

    let mut args = std::env::args().skip(1).peekable();
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" | "-h" => {
                print_usage_and_exit(0);
            }
            "--openapi" => {
                if let Some(next) = args.peek() {
                    if !next.starts_with("--") {
                        openapi_out_opt = Some(args.next().unwrap());
                    } else {
                        openapi_out_opt = Some("openapi.json".to_string());
                    }
                } else {
                    openapi_out_opt = Some("openapi.json".to_string());
                }
            }
            "--input" => {
                let Some(path) = args.next() else {
                    eprintln!("Error: --input requires a path.");
                    print_usage_and_exit(2);
                };
                input_json_path_opt = Some(path);
            }
            _ if !arg.starts_with("--") && input_json_path_opt.is_none() => {
                input_json_path_opt = Some(arg);
            }
            other => {
                eprintln!("Error: Unknown argument '{}'.", other);
                print_usage_and_exit(2);
            }
        }
    }

    if let Some(openapi_out_path) = openapi_out_opt {
        write_openapi_json_to_file(&openapi_out_path);
        println!("OpenAPI JSON written to '{}'.", openapi_out_path);
        return;
    }

    let input_json_path: String = input_json_path_opt
        .unwrap_or_else(|| "005_Cantilever_with_Triangular_Distributed_Load.json".to_string());
    // input_json_path_opt.unwrap_or_else(|| "093_Loadcombinations_hooked_cantilever.json".to_string());

    // Premium run for the binary:
    match calculate_from_file_internal_with_tier(&input_json_path, LicenseTier::Premium) {
        Ok(serialized_results) => {
            let output_results_path: &str = "internal_results.json";
            match fs::File::create(output_results_path) {
                Ok(mut file) => {
                    if let Err(error) = file.write_all(serialized_results.as_bytes()) {
                        log::error!(
                            "Failed to write results to '{}': {}",
                            output_results_path,
                            error
                        );
                        std::process::exit(1);
                    } else {
                        log::info!("Internal results written to '{}'.", output_results_path);
                    }
                }
                Err(error) => {
                    log::error!(
                        "Failed to create results file '{}': {}",
                        output_results_path,
                        error
                    );
                    std::process::exit(1);
                }
            }
        }
        Err(error) => {
            eprintln!("Analysis failed: {}", error);
            std::process::exit(1);
        }
    }
}

fn write_openapi_json_to_file(file_path: &str) {
    let openapi = ApiDoc::openapi();
    let json_content = openapi.to_json().expect("Failed to generate OpenAPI JSON");

    let mut file = fs::File::create(file_path).expect("Failed to create the OpenAPI JSON file");
    file.write_all(json_content.as_bytes())
        .expect("Failed to write OpenAPI JSON to the file");

    log::debug!("OpenAPI JSON written to '{}'", file_path);
}
