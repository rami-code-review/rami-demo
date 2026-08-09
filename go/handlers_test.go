package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func newTestServer() *httptest.Server {
	return httptest.NewServer(NewHandler(newTestStore(), "http://short.test"))
}

// noRedirectClient returns an HTTP client that does not follow redirects.
func noRedirectClient() *http.Client {
	return &http.Client{
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}
}

func shorten(t *testing.T, srv *httptest.Server, body string) *http.Response {
	t.Helper()
	resp, err := http.Post(srv.URL+"/shorten", "application/json", strings.NewReader(body))
	if err != nil {
		t.Fatalf("POST /shorten: %v", err)
	}
	return resp
}

func TestShortenReturnsCode(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com/path"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if out.Code == "" {
		t.Error("expected a non-empty code")
	}
	if want := "http://short.test/" + out.Code; out.ShortURL != want {
		t.Errorf("short_url = %q, want %q", out.ShortURL, want)
	}
}

func TestShortenRejectsBadURL(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	for _, body := range []string{
		`{"url":"not-a-url"}`,
		`{"url":"ftp://example.com"}`,
		`{"url":""}`,
		`not json`,
		`{"url":"https://example.com"} trailing`,
	} {
		resp := shorten(t, srv, body)
		if resp.StatusCode != http.StatusBadRequest {
			t.Errorf("body %q: status = %d, want 400", body, resp.StatusCode)
		}
		resp.Body.Close()
	}
}

func TestResolveRedirectsAndCounts(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()
	client := noRedirectClient()

	created := shorten(t, srv, `{"url":"https://example.com/dest"}`)
	var out shortenResponse
	_ = json.NewDecoder(created.Body).Decode(&out)
	created.Body.Close()

	resp, err := client.Get(srv.URL + "/" + out.Code)
	if err != nil {
		t.Fatalf("GET /%s: %v", out.Code, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusFound {
		t.Fatalf("status = %d, want 302", resp.StatusCode)
	}
	if loc := resp.Header.Get("Location"); loc != "https://example.com/dest" {
		t.Errorf("Location = %q, want https://example.com/dest", loc)
	}

	statsResp, err := client.Get(srv.URL + "/api/stats/" + out.Code)
	if err != nil {
		t.Fatalf("GET stats: %v", err)
	}
	defer statsResp.Body.Close()
	var link Link
	_ = json.NewDecoder(statsResp.Body).Decode(&link)
	if link.Clicks != 1 {
		t.Errorf("clicks = %d, want 1", link.Clicks)
	}
}

func TestResolveUnknownReturns404(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()
	client := noRedirectClient()

	resp, err := client.Get(srv.URL + "/doesnotexist")
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("status = %d, want 404", resp.StatusCode)
	}
}

func TestStatsUnknownReturns404(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp, err := http.Get(srv.URL + "/api/stats/missing")
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("status = %d, want 404", resp.StatusCode)
	}
}

func TestShortenWithExpiry(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()
	client := noRedirectClient()

	resp := shorten(t, srv, `{"url":"https://example.com","expires_in_seconds":3600}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode: %v", err)
	}

	statsResp, err := client.Get(srv.URL + "/api/stats/" + out.Code)
	if err != nil {
		t.Fatalf("stats: %v", err)
	}
	defer statsResp.Body.Close()
	var link Link
	if err := json.NewDecoder(statsResp.Body).Decode(&link); err != nil {
		t.Fatalf("decode stats: %v", err)
	}
	if link.ExpiresAt == nil {
		t.Error("expected ExpiresAt to be set in response")
	}
}

func TestResolveExpiredLinkReturns404(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 3600)

	h := &Handler{store: s, baseURL: "http://short.test"}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{code}", h.resolve)
	srv := httptest.NewServer(mux)
	defer srv.Close()
	client := noRedirectClient()

	s.now = func() time.Time {
		return time.Date(2026, 6, 1, 13, 1, 0, 0, time.UTC)
	}

	resp, err := client.Get(srv.URL + "/" + link.Code)
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("status = %d, want 404", resp.StatusCode)
	}
}
