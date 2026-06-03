use std::fs::File;
use std::io::{self, BufReader, Seek, SeekFrom, Write};
use std::process::ExitCode;
use std::thread;
use std::time::Duration;

use logtail::{filter_available, parse_args, Config, USAGE};

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
            eprintln!("logtail: {}: {err}", config.path);
            ExitCode::FAILURE
        }
    }
}

/// Follow the configured file, printing matching lines as they arrive.
fn run(config: &Config) -> io::Result<()> {
    let file = File::open(&config.path)?;
    let mut reader = BufReader::new(file);

    if !config.from_start {
        reader.seek(SeekFrom::End(0))?;
    }

    let filter = config.filter.as_deref();
    let stdout = io::stdout();
    loop {
        {
            let mut out = stdout.lock();
            filter_available(&mut reader, &mut out, filter)?;
            out.flush()?;
        }
        thread::sleep(POLL_INTERVAL);
    }
}
