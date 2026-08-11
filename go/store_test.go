package main

import (
	"testing"
	"time"
)

func newTestStore() *Store {
	s := NewStore()
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	s.now = func() time.Time { return fixed }
	return s
}

func TestCreateAssignsUniqueCodeAndZeroClicks(t *testing.T) {
	s := newTestStore()

	a, err := s.Create("https://example.com/one", 0, 0)
	if err != nil {
		t.Fatalf("Create returned error: %v", err)
	}
	b, err := s.Create("https://example.com/two", 0, 0)
	if err != nil {
		t.Fatalf("Create returned error: %v", err)
	}

	if a.Code == b.Code {
		t.Fatalf("expected distinct codes, got %q twice", a.Code)
	}
	if a.Clicks != 0 {
		t.Errorf("expected 0 clicks on create, got %d", a.Clicks)
	}
	if len(a.Code) != defaultCodeLength {
		t.Errorf("expected code length %d, got %d", defaultCodeLength, len(a.Code))
	}
}

func TestResolveIncrementsClicks(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 0, 0)

	for i := 1; i <= 3; i++ {
		url, ok := s.Resolve(link.Code)
		if !ok {
			t.Fatalf("Resolve(%q) not found", link.Code)
		}
		if url != "https://example.com" {
			t.Errorf("got url %q, want https://example.com", url)
		}
	}

	stats, _ := s.Stats(link.Code)
	if stats.Clicks != 3 {
		t.Errorf("expected 3 clicks, got %d", stats.Clicks)
	}
}

func TestStatsDoesNotIncrementClicks(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 0, 0)

	s.Stats(link.Code)
	s.Stats(link.Code)

	stats, _ := s.Stats(link.Code)
	if stats.Clicks != 0 {
		t.Errorf("expected Stats to leave clicks at 0, got %d", stats.Clicks)
	}
}

func TestResolveUnknownCode(t *testing.T) {
	s := newTestStore()
	if _, ok := s.Resolve("missing"); ok {
		t.Error("expected Resolve of unknown code to report not found")
	}
}

func TestCreateWithExpiry(t *testing.T) {
	s := newTestStore()
	link, err := s.Create("https://example.com", 3600, 0)
	if err != nil {
		t.Fatalf("Create returned error: %v", err)
	}
	if link.ExpiresAt == nil {
		t.Error("expected ExpiresAt to be set")
	}
}

func TestResolveBeforeExpiry(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 3600, 0)

	url, ok := s.Resolve(link.Code)
	if !ok {
		t.Fatal("expected Resolve to succeed before expiry")
	}
	if url != "https://example.com" {
		t.Errorf("got url %q, want https://example.com", url)
	}
}

func TestResolveAfterExpiry(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 3600, 0)

	s.now = func() time.Time {
		return time.Date(2026, 6, 1, 13, 1, 0, 0, time.UTC)
	}

	_, ok := s.Resolve(link.Code)
	if ok {
		t.Error("expected Resolve to fail after expiry")
	}
}
