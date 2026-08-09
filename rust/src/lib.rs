//! A live log tailer with built-in filtering — the reusable core behind the `logtail` binary.

use std::io::{self, BufRead, Write};

/// How `logtail` was configured to run.
#[derive(Debug, PartialEq, Eq)]
pub struct Config {
    /// The file to follow.
    pub path: String,
    /// Keep only lines containing this substring; `None` keeps every line.
    pub filter: Option<String>,
    /// Read existing content before following; otherwise start at end of file.
    pub from_start: bool,
    /// Invert the filter: keep lines that do NOT match.
    pub invert: bool,
}

/// An error in the command-line arguments.
#[derive(Debug, PartialEq, Eq)]
pub struct ParseError(pub String);

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for ParseError {}

/// The usage string shown on a parse error or `--help`.
pub const USAGE: &str = "usage: logtail [--filter <substring>] [--invert] [--from-start] <file>";

/// Parse command-line arguments (excluding the program name) into a [`Config`].
pub fn parse_args<I: IntoIterator<Item = String>>(args: I) -> Result<Config, ParseError> {
    let mut filter = None;
    let mut from_start = false;
    let mut invert = false;
    let mut path = None;

    let mut iter = args.into_iter();
    while let Some(arg) = iter.next() {
        match arg.as_str() {
            "--filter" => {
                let value = iter
                    .next()
                    .ok_or_else(|| ParseError("--filter requires a value".to_string()))?;
                filter = Some(value);
            }
            "--from-start" => from_start = true,
            "--invert" => invert = true,
            other if other.starts_with("--") => {
                return Err(ParseError(format!("unknown flag: {other}")));
            }
            _ => {
                if path.is_some() {
                    return Err(ParseError("expected exactly one file argument".to_string()));
                }
                path = Some(arg);
            }
        }
    }

    match path {
        Some(path) => Ok(Config {
            path,
            filter,
            from_start,
            invert,
        }),
        None => Err(ParseError("a file argument is required".to_string())),
    }
}

/// Report whether a line should be printed under the given filter and invert setting.
pub fn matches(line: &str, filter: Option<&str>, invert: bool) -> bool {
    match filter {
        Some(needle) => line.contains(needle) != invert,
        None => !invert,
    }
}

/// Read all currently available lines from `reader` and write the matching ones to `out`.
///
/// Returns the number of lines written. Stops at EOF; callers tailing a growing
/// file invoke this repeatedly as new lines arrive.
pub fn filter_available<R: BufRead, W: Write>(
    reader: &mut R,
    out: &mut W,
    filter: Option<&str>,
    invert: bool,
) -> io::Result<usize> {
    let mut written = 0;
    let mut line = String::new();
    loop {
        line.clear();
        let read = reader.read_line(&mut line)?;
        if read == 0 {
            break;
        }
        let trimmed = line.trim_end_matches(['\r', '\n']);
        if matches(trimmed, filter, invert) {
            writeln!(out, "{trimmed}")?;
            written += 1;
        }
    }
    Ok(written)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse(args: &[&str]) -> Result<Config, ParseError> {
        parse_args(args.iter().map(|s| s.to_string()))
    }

    #[test]
    fn parses_file_only() {
        let config = parse(&["app.log"]).unwrap();
        assert_eq!(
            config,
            Config {
                path: "app.log".to_string(),
                filter: None,
                from_start: false,
                invert: false,
            }
        );
    }

    #[test]
    fn parses_filter_and_from_start() {
        let config = parse(&["--filter", "ERROR", "--from-start", "app.log"]).unwrap();
        assert_eq!(
            config,
            Config {
                path: "app.log".to_string(),
                filter: Some("ERROR".to_string()),
                from_start: true,
                invert: false,
            }
        );
    }

    #[test]
    fn filter_requires_a_value() {
        assert!(parse(&["--filter"]).is_err());
    }

    #[test]
    fn unknown_flag_is_rejected() {
        assert!(parse(&["--nope", "app.log"]).is_err());
    }

    #[test]
    fn missing_file_is_rejected() {
        assert!(parse(&["--filter", "x"]).is_err());
    }

    #[test]
    fn two_files_are_rejected() {
        assert!(parse(&["a.log", "b.log"]).is_err());
    }

    #[test]
    fn matches_respects_substring_and_none() {
        assert!(matches("an ERROR line", Some("ERROR"), false));
        assert!(!matches("an info line", Some("ERROR"), false));
        assert!(matches("anything", None, false));
    }

    #[test]
    fn filter_available_keeps_only_matching_lines() {
        let input = "INFO start\nERROR boom\nINFO ok\nERROR again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, Some("ERROR"), false).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR boom\nERROR again\n");
    }

    #[test]
    fn filter_available_with_no_filter_keeps_all() {
        let input = "one\ntwo\nthree\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, None, false).unwrap();
        assert_eq!(written, 3);
        assert_eq!(String::from_utf8(out).unwrap(), "one\ntwo\nthree\n");
    }

    #[test]
    fn filter_available_strips_carriage_returns() {
        let input = "ERROR crlf\r\nINFO skip\r\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        filter_available(&mut reader, &mut out, Some("ERROR"), false).unwrap();
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR crlf\n");
    }

    #[test]
    fn filter_available_emits_a_final_line_without_newline() {
        let input = "ERROR done";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, Some("ERROR"), false).unwrap();
        assert_eq!(written, 1);
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR done\n");
    }

    #[test]
    fn parses_invert_flag() {
        let config = parse(&["--invert", "--filter", "ERROR", "app.log"]).unwrap();
        assert_eq!(
            config,
            Config {
                path: "app.log".to_string(),
                filter: Some("ERROR".to_string()),
                from_start: false,
                invert: true,
            }
        );
    }

    #[test]
    fn matches_inverts_filter_when_invert_is_true() {
        assert!(!matches("an ERROR line", Some("ERROR"), true));
        assert!(matches("an info line", Some("ERROR"), true));
        assert!(!matches("anything", None, true));
    }

    #[test]
    fn filter_available_with_invert_keeps_non_matching_lines() {
        let input = "INFO start\nERROR boom\nINFO ok\nERROR again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, Some("ERROR"), true).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "INFO start\nINFO ok\n");
    }
}
