use std::fs::File;
use std::io::{self, BufReader, Seek, SeekFrom, Write};
use std::process::ExitCode;
use std::thread;
use std::time::Duration;

use logtail::{filter_available_with_prefix, parse_args, Config, USAGE};

const POLL_INTERVAL: Duration = Duration::from_millis(200);

fn main() -> ExitCode {
    let config = match parse_args(std::env::args().skip(1)) {
        Ok(config) => config,
        Err(err) => {
            eprintln!("{err}");
            eprintln!("{USAGE}");
            return ExitCode::from(2);
        }
    };

    match run(&config) {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            if err.kind() != io::ErrorKind::NotFound {
                let first_path = config.paths.first().map(|s| s.as_str()).unwrap_or("unknown");
                eprintln!("logtail: {}: {err}", first_path);
            } else {
                eprintln!("logtail: {err}");
            }
            ExitCode::FAILURE
        }
    }
}

/// Follow the configured files, printing matching lines as they arrive.
fn run(config: &Config) -> io::Result<()> {
    struct FileReader {
        reader: BufReader<File>,
        path: String,
    }

    let mut readers: Vec<FileReader> = Vec::new();
    for path in &config.paths {
        match File::open(path) {
            Ok(file) => {
                let mut reader = BufReader::new(file);
                if !config.from_start {
                    reader.seek(SeekFrom::End(0))?;
                }
                readers.push(FileReader {
                    reader,
                    path: path.clone(),
                });
            }
            Err(err) => {
                eprintln!("logtail: {}: {err}", path);
            }
        }
    }

    if readers.is_empty() {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            "could not open any of the specified files",
        ));
    }

    let show_prefix = config.paths.len() > 1;
    let stdout = io::stdout();
    loop {
        {
            let mut out = stdout.lock();
            for file_reader in &mut readers {
                let prefix = if show_prefix {
                    Some(file_reader.path.as_str())
                } else {
                    None
                };
                filter_available_with_prefix(
                    &mut file_reader.reader,
                    &mut out,
                    config.matcher.as_ref(),
                    config.invert,
                    config.since,
                    prefix,
                )?;
            }
            out.flush()?;
        }
        thread::sleep(POLL_INTERVAL);
    }
}
