package main

import (
	"errors"
	"sync"
	"time"
)

// Link is a shortened URL and its click count.
type Link struct {
	Code      string    `json:"code"`
	URL       string    `json:"url"`
	Clicks    int64     `json:"clicks"`
	CreatedAt time.Time `json:"created_at"`
}

// ErrCodeExhausted is returned when a unique code could not be generated.
var ErrCodeExhausted = errors.New("could not generate a unique code")

// Store holds links in memory, keyed by their short code.
type Store struct {
	mu    sync.Mutex
	links map[string]*Link
	now   func() time.Time
}

// NewStore returns an empty store.
func NewStore() *Store {
	return &Store{links: make(map[string]*Link), now: time.Now}
}

// Create stores a URL under a freshly generated unique code and returns the link.
func (s *Store) Create(url string) (Link, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	var code string
	for attempt := 0; attempt < 10; attempt++ {
		candidate, err := generateCode(defaultCodeLength)
		if err != nil {
			return Link{}, err
		}
		if _, taken := s.links[candidate]; !taken {
			code = candidate
			break
		}
	}
	if code == "" {
		return Link{}, ErrCodeExhausted
	}

	link := &Link{Code: code, URL: url, Clicks: 0, CreatedAt: s.now()}
	s.links[code] = link
	return *link, nil
}

// Resolve returns the URL for a code and increments its click count.
func (s *Store) Resolve(code string) (string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	link, ok := s.links[code]
	if !ok {
		return "", false
	}
	link.Clicks++
	return link.URL, true
}

// Stats returns a copy of the link for a code without changing its click count.
func (s *Store) Stats(code string) (Link, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	link, ok := s.links[code]
	if !ok {
		return Link{}, false
	}
	return *link, true
}
