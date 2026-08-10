package main

import (
	"sync"
	"time"
)

// RateLimiter tracks requests per IP and enforces a limit.
type RateLimiter struct {
	mu              sync.Mutex
	requestsPerIP   map[string][]time.Time
	maxRequests     int
	windowDuration  time.Duration
	now             func() time.Time
}

// NewRateLimiter creates a rate limiter with the given capacity and window.
func NewRateLimiter(maxRequests int, windowDuration time.Duration) *RateLimiter {
	return &RateLimiter{
		requestsPerIP:  make(map[string][]time.Time),
		maxRequests:    maxRequests,
		windowDuration: windowDuration,
		now:            time.Now,
	}
}

// Allow reports whether a request from the given IP is within the rate limit.
func (rl *RateLimiter) Allow(ip string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := rl.now()
	cutoff := now.Add(-rl.windowDuration)

	var reqs []time.Time
	if existing, ok := rl.requestsPerIP[ip]; ok {
		for _, t := range existing {
			if t.After(cutoff) {
				reqs = append(reqs, t)
			}
		}
	}

	if len(reqs) == 0 {
		delete(rl.requestsPerIP, ip)
	} else {
		rl.requestsPerIP[ip] = reqs
	}

	if len(reqs) >= rl.maxRequests {
		return false
	}

	reqs = append(reqs, now)
	rl.requestsPerIP[ip] = reqs
	return true
}
