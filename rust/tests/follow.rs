use std::fs::{File, OpenOptions};
use std::io::{BufReader, Seek, SeekFrom, Write};

use logtail::filter_available;
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
    let written = filter_available(&mut reader, &mut out, Some("ERROR")).unwrap();
    assert_eq!(written, 1);
    assert_eq!(String::from_utf8(out.clone()).unwrap(), "ERROR first\n");

    // Append more lines; a second read should pick up only the new matches.
    writeln!(writer, "INFO more").unwrap();
    writeln!(writer, "ERROR second").unwrap();
    writer.flush().unwrap();

    out.clear();
    let written = filter_available(&mut reader, &mut out, Some("ERROR")).unwrap();
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
    filter_available(&mut reader, &mut out, None).unwrap();
    assert_eq!(String::from_utf8(out).unwrap(), "new line\n");
}
