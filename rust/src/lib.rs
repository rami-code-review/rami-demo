//! A live log tailer with built-in filtering — the reusable core behind the `logtail` binary.

use std::io::{self, BufRead, Write};
use regex::Regex;
use chrono::DateTime;

#[derive(Debug)]
pub enum Matcher {
    Substring(String),
    Regex(Regex),
}

impl Matcher {
    fn is_match(&self, text: &str) -> bool {
        match self {
            Matcher::Substring(s) => text.contains(s),
            Matcher::Regex(re) => re.is_match(text),
        }
    }
}

/// How `logtail` was configured to run.
#[derive(Debug)]
pub struct Config {
    /// The file to follow.
    pub path: String,
    /// Compiled matcher (either substring or regex); `None` keeps every line.
    pub matcher: Option<Matcher>,
    /// Read existing content before following; otherwise start at end of file.
    pub from_start: bool,
    /// Invert the filter: keep lines that do NOT match.
    pub invert: bool,
    /// Show only lines with timestamps at or after this time; `None` keeps every line.
    pub since: Option<String>,
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
pub const USAGE: &str = "usage: logtail [--filter <substring>] [--regex] [--invert] [--from-start] [--since <timestamp>] <file>";

/// Parse command-line arguments (excluding the program name) into a [`Config`].
pub fn parse_args<I: IntoIterator<Item = String>>(args: I) -> Result<Config, ParseError> {
    let mut filter = None;
    let mut from_start = false;
    let mut invert = false;
    let mut regex_mode = false;
    let mut since = None;
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
            "--regex" => regex_mode = true,
            "--since" => {
                let value = iter
                    .next()
                    .ok_or_else(|| ParseError("--since requires a value".to_string()))?;
                validate_timestamp(&value)?;
                since = Some(value);
            }
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

    let matcher = if let Some(ref f) = filter {
        if regex_mode {
            let re = Regex::new(f).map_err(|e| ParseError(format!("invalid regex: {e}")))?;
            Some(Matcher::Regex(re))
        } else {
            Some(Matcher::Substring(f.clone()))
        }
    } else {
        None
    };

    match path {
        Some(path) => Ok(Config {
            path,
            matcher,
            from_start,
            invert,
            since,
        }),
        None => Err(ParseError("a file argument is required".to_string())),
    }
}

fn validate_timestamp(s: &str) -> Result<(), ParseError> {
    DateTime::parse_from_rfc3339(s)
        .map_err(|_| ParseError(format!("invalid timestamp: {s}")))?;
    Ok(())
}

fn extract_leading_timestamp(line: &str) -> Option<String> {
    let mut timestamp = String::new();
    for ch in line.chars() {
        if ch == ' ' && !timestamp.is_empty() {
            if DateTime::parse_from_rfc3339(&timestamp).is_ok() {
                return Some(timestamp);
            }
            return None;
        }
        timestamp.push(ch);
    }
    None
}

fn is_after_since(line: &str, since: &str) -> bool {
    if let Some(ts_str) = extract_leading_timestamp(line) {
        if let (Ok(line_ts), Ok(since_ts)) = (
            DateTime::parse_from_rfc3339(&ts_str),
            DateTime::parse_from_rfc3339(since),
        ) {
            return line_ts >= since_ts;
        }
    }
    false
}

/// Report whether a line should be printed using a compiled matcher.
pub fn matches(line: &str, matcher: Option<&Matcher>, invert: bool) -> bool {
    match matcher {
        Some(m) => m.is_match(line) != invert,
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
    matcher: Option<&Matcher>,
    invert: bool,
    since: Option<&str>,
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
        if matches(trimmed, matcher, invert) && since.map_or(true, |s| is_after_since(trimmed, s)) {
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
        assert_eq!(config.path, "app.log");
        assert!(config.matcher.is_none());
        assert_eq!(config.from_start, false);
        assert_eq!(config.invert, false);
    }

    #[test]
    fn parses_filter_and_from_start() {
        let config = parse(&["--filter", "ERROR", "--from-start", "app.log"]).unwrap();
        assert_eq!(config.path, "app.log");
        assert!(config.matcher.is_some());
        assert_eq!(config.from_start, true);
        assert_eq!(config.invert, false);
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
        let substr_matcher = Matcher::Substring("ERROR".to_string());
        assert!(matches("an ERROR line", Some(&substr_matcher), false));
        assert!(!matches("an info line", Some(&substr_matcher), false));
        assert!(matches("anything", None, false));
    }

    #[test]
    fn filter_available_keeps_only_matching_lines() {
        let input = "INFO start\nERROR boom\nINFO ok\nERROR again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Substring("ERROR".to_string());
        let written = filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR boom\nERROR again\n");
    }

    #[test]
    fn filter_available_with_no_filter_keeps_all() {
        let input = "one\ntwo\nthree\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, None, false, None).unwrap();
        assert_eq!(written, 3);
        assert_eq!(String::from_utf8(out).unwrap(), "one\ntwo\nthree\n");
    }

    #[test]
    fn filter_available_strips_carriage_returns() {
        let input = "ERROR crlf\r\nINFO skip\r\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Substring("ERROR".to_string());
        filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR crlf\n");
    }

    #[test]
    fn filter_available_emits_a_final_line_without_newline() {
        let input = "ERROR done";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Substring("ERROR".to_string());
        let written = filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
        assert_eq!(written, 1);
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR done\n");
    }

    #[test]
    fn parses_invert_flag() {
        let config = parse(&["--invert", "--filter", "ERROR", "app.log"]).unwrap();
        assert_eq!(config.path, "app.log");
        assert!(config.matcher.is_some());
        assert_eq!(config.from_start, false);
        assert_eq!(config.invert, true);
    }

    #[test]
    fn matches_inverts_filter_when_invert_is_true() {
        let substr_matcher = Matcher::Substring("ERROR".to_string());
        assert!(!matches("an ERROR line", Some(&substr_matcher), true));
        assert!(matches("an info line", Some(&substr_matcher), true));
        assert!(!matches("anything", None, true));
    }

    #[test]
    fn filter_available_with_invert_keeps_non_matching_lines() {
        let input = "INFO start\nERROR boom\nINFO ok\nERROR again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Substring("ERROR".to_string());
        let written = filter_available(&mut reader, &mut out, Some(&matcher), true, None).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "INFO start\nINFO ok\n");
    }

    #[test]
    fn parses_regex_flag() {
        let config = parse(&["--filter", "ERR.*", "--regex", "app.log"]).unwrap();
        assert_eq!(config.path, "app.log");
        assert!(config.matcher.is_some());
        assert_eq!(config.from_start, false);
        assert_eq!(config.invert, false);
    }

    #[test]
    fn regex_flag_validates_pattern() {
        let result = parse(&["--filter", "[invalid", "--regex", "app.log"]);
        assert!(result.is_err());
    }

    #[test]
    fn matches_regex_pattern() {
        let re_matcher = Matcher::Regex(Regex::new("^ERROR").unwrap());
        assert!(matches("ERROR: boom", Some(&re_matcher), false));
        assert!(!matches("INFO: ok", Some(&re_matcher), false));
        let ci_matcher = Matcher::Regex(Regex::new("(?i)ERROR").unwrap());
        assert!(matches("error: case", Some(&ci_matcher), false));
    }

    #[test]
    fn filter_available_with_regex_matches_pattern() {
        let input = "ERROR: boom\nINFO: ok\nERROR: again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Regex(Regex::new("^ERROR").unwrap());
        let written = filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "ERROR: boom\nERROR: again\n");
    }

    #[test]
    fn filter_available_regex_with_invert() {
        let input = "ERROR: boom\nINFO: ok\nERROR: again\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let matcher = Matcher::Regex(Regex::new("^ERROR").unwrap());
        let written = filter_available(&mut reader, &mut out, Some(&matcher), true, None).unwrap();
        assert_eq!(written, 1);
        assert_eq!(String::from_utf8(out).unwrap(), "INFO: ok\n");
    }

    #[test]
    fn parses_since_flag() {
        let config = parse(&["--since", "2026-07-10T14:30:00+00:00", "app.log"]).unwrap();
        assert_eq!(config.path, "app.log");
        assert_eq!(config.since, Some("2026-07-10T14:30:00+00:00".to_string()));
    }

    #[test]
    fn invalid_since_timestamp_is_rejected() {
        let result = parse(&["--since", "not-a-timestamp", "app.log"]);
        assert!(result.is_err());
    }

    #[test]
    fn since_flag_requires_a_value() {
        let result = parse(&["--since"]);
        assert!(result.is_err());
    }

    #[test]
    fn filter_available_with_since_keeps_lines_after_timestamp() {
        let input = "2026-07-10T14:30:00+00:00 INFO boot\n2026-07-10T14:35:00+00:00 ERROR boom\n2026-07-10T14:25:00+00:00 INFO skipped\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, None, false, Some("2026-07-10T14:30:00+00:00")).unwrap();
        assert_eq!(written, 2);
        assert_eq!(String::from_utf8(out).unwrap(), "2026-07-10T14:30:00+00:00 INFO boot\n2026-07-10T14:35:00+00:00 ERROR boom\n");
    }

    #[test]
    fn filter_available_with_since_handles_short_lines() {
        let input = "short\n2026-07-10T14:35:00+00:00 valid\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, None, false, Some("2026-07-10T14:30:00+00:00")).unwrap();
        assert_eq!(written, 1);
        assert_eq!(String::from_utf8(out).unwrap(), "2026-07-10T14:35:00+00:00 valid\n");
    }

    #[test]
    fn filter_available_with_since_handles_multibyte_chars() {
        let input = "2026-07-10T14:35:00+00:00 café\n🎉 no timestamp\n";
        let mut reader = std::io::Cursor::new(input);
        let mut out = Vec::new();
        let written = filter_available(&mut reader, &mut out, None, false, Some("2026-07-10T14:30:00+00:00")).unwrap();
        assert_eq!(written, 1);
        assert_eq!(String::from_utf8(out).unwrap(), "2026-07-10T14:35:00+00:00 café\n");
    }
}
