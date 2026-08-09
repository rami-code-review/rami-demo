package main

import (
	"testing"
	"time"
)

func TestRateLimiterUnderLimit(t *testing.T) {
	rl := NewRateLimiter(3, 60*time.Second)
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	rl.now = func() time.Time { return fixed }

	for i := 1; i <= 3; i++ {
		if !rl.Allow("192.168.1.1") {
			t.Errorf("request %d: expected Allow to return true", i)
		}
	}
}

func TestRateLimiterOverLimit(t *testing.T) {
	rl := NewRateLimiter(2, 60*time.Second)
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	rl.now = func() time.Time { return fixed }

	rl.Allow("192.168.1.1")
	rl.Allow("192.168.1.1")

	if rl.Allow("192.168.1.1") {
		t.Error("expected Allow to return false when over limit")
	}
}

func TestRateLimiterIndependentIPs(t *testing.T) {
	rl := NewRateLimiter(1, 60*time.Second)
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	rl.now = func() time.Time { return fixed }

	if !rl.Allow("192.168.1.1") {
		t.Error("first IP: expected Allow to return true")
	}

	if !rl.Allow("192.168.1.2") {
		t.Error("second IP: expected Allow to return true")
	}

	if rl.Allow("192.168.1.1") {
		t.Error("first IP over limit: expected Allow to return false")
	}

	if rl.Allow("192.168.1.2") {
		t.Error("second IP over limit: expected Allow to return false")
	}
}

func TestRateLimiterIdleIPEviction(t *testing.T) {
	rl := NewRateLimiter(2, 60*time.Second)
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	rl.now = func() time.Time { return fixed }

	if !rl.Allow("192.168.1.1") {
		t.Error("initial request: expected Allow to return true")
	}

	if len(rl.requestsPerIP) != 1 {
		t.Errorf("expected 1 IP in map, got %d", len(rl.requestsPerIP))
	}

	fixed = time.Date(2026, 6, 1, 12, 2, 0, 0, time.UTC)
	rl.now = func() time.Time { return fixed }

	if !rl.Allow("192.168.1.1") {
		t.Error("request after window: expected Allow to return true")
	}

	if len(rl.requestsPerIP) != 1 {
		t.Errorf("expected 1 IP in map after eviction, got %d", len(rl.requestsPerIP))
	}

	if _, ok := rl.requestsPerIP["192.168.1.1"]; !ok {
		t.Error("expected IP to still be in map after new request")
	}
}
