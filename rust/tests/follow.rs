use std::fs::{File, OpenOptions};
use std::io::{BufReader, Seek, SeekFrom, Write};

use logtail::{filter_available, filter_available_with_prefix, Matcher};
use tempfile::tempdir;

/// Reading available lines, then more after the file grows, mirrors `tail -f` over a real file.
#[test]
fn reads_appended_lines_incrementally() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("app.log");

    let mut writer = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap();
    writeln!(writer, "INFO boot").unwrap();
    writeln!(writer, "ERROR first").unwrap();
    writer.flush().unwrap();

    let mut reader = BufReader::new(File::open(&path).unwrap());

    let mut out = Vec::new();
    let matcher = Matcher::Substring("ERROR".to_string());
    let written = filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
    assert_eq!(written, 1);
    assert_eq!(String::from_utf8(out.clone()).unwrap(), "ERROR first\n");

    // Append more lines; a second read should pick up only the new matches.
    writeln!(writer, "INFO more").unwrap();
    writeln!(writer, "ERROR second").unwrap();
    writer.flush().unwrap();

    out.clear();
    let written = filter_available(&mut reader, &mut out, Some(&matcher), false, None).unwrap();
    assert_eq!(written, 1);
    assert_eq!(String::from_utf8(out).unwrap(), "ERROR second\n");
}

/// With no filter, following from end of file yields exactly the lines appended afterward.
#[test]
fn from_end_skips_existing_content() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("app.log");

    let mut writer = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap();
    writeln!(writer, "old line one").unwrap();
    writeln!(writer, "old line two").unwrap();
    writer.flush().unwrap();

    let mut reader = BufReader::new(File::open(&path).unwrap());
    reader.seek(SeekFrom::End(0)).unwrap();

    writeln!(writer, "new line").unwrap();
    writer.flush().unwrap();

    let mut out = Vec::new();
    filter_available(&mut reader, &mut out, None, false, None).unwrap();
    assert_eq!(String::from_utf8(out).unwrap(), "new line\n");
}

/// Inverted filtering shows non-matching lines.
#[test]
fn invert_shows_non_matching_lines() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("app.log");

    let mut writer = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap();
    writeln!(writer, "INFO boot").unwrap();
    writeln!(writer, "ERROR first").unwrap();
    writeln!(writer, "INFO ok").unwrap();
    writer.flush().unwrap();

    let mut reader = BufReader::new(File::open(&path).unwrap());

    let mut out = Vec::new();
    let matcher = Matcher::Substring("ERROR".to_string());
    let written = filter_available(&mut reader, &mut out, Some(&matcher), true, None).unwrap();
    assert_eq!(written, 2);
    assert_eq!(String::from_utf8(out).unwrap(), "INFO boot\nINFO ok\n");
}

/// Inverted with no filter shows no lines (since no filter means all match, inverting shows none).
#[test]
fn invert_with_no_filter_shows_none() {
    let dir = tempdir().unwrap();
    let path = dir.path().join("app.log");

    let mut writer = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .unwrap();
    writeln!(writer, "any line").unwrap();
    writeln!(writer, "another").unwrap();
    writer.flush().unwrap();

    let mut reader = BufReader::new(File::open(&path).unwrap());

    let mut out = Vec::new();
    let written = filter_available(&mut reader, &mut out, None, true, None).unwrap();
    assert_eq!(written, 0);
    assert_eq!(String::from_utf8(out).unwrap(), "");
}

/// Multiple files are followed with prefixed output.
#[test]
fn multiple_files_with_prefix() {
    let dir = tempdir().unwrap();
    let path1 = dir.path().join("app1.log");
    let path2 = dir.path().join("app2.log");

    let mut writer1 = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path1)
        .unwrap();
    let mut writer2 = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path2)
        .unwrap();

    writeln!(writer1, "line from first").unwrap();
    writeln!(writer2, "line from second").unwrap();
    writer1.flush().unwrap();
    writer2.flush().unwrap();

    let mut reader1 = BufReader::new(File::open(&path1).unwrap());
    let mut reader2 = BufReader::new(File::open(&path2).unwrap());

    let mut out = Vec::new();
    let written1 = filter_available_with_prefix(&mut reader1, &mut out, None, false, None, Some("app1.log")).unwrap();
    let written2 = filter_available_with_prefix(&mut reader2, &mut out, None, false, None, Some("app2.log")).unwrap();

    assert_eq!(written1, 1);
    assert_eq!(written2, 1);
    let output = String::from_utf8(out).unwrap();
    assert!(output.contains("app1.log: line from first"));
    assert!(output.contains("app2.log: line from second"));
}

/// Multiple files where one exists and one is missing: present file continues.
#[test]
fn one_missing_file_continues_with_existing() {
    let dir = tempdir().unwrap();
    let existing_path = dir.path().join("existing.log");
    let missing_path = dir.path().join("missing.log");

    let mut writer = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&existing_path)
        .unwrap();
    writeln!(writer, "line from existing").unwrap();
    writer.flush().unwrap();

    let mut existing_reader = BufReader::new(File::open(&existing_path).unwrap());

    let mut out = Vec::new();
    let written = filter_available_with_prefix(&mut existing_reader, &mut out, None, false, None, Some("existing.log")).unwrap();

    assert_eq!(written, 1);
    let output = String::from_utf8(out).unwrap();
    assert_eq!(output, "existing.log: line from existing\n");

    File::open(&missing_path).expect_err("should not be able to open missing file");
}
