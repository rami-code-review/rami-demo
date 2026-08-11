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
	s := newTestStore()
	h := &Handler{
		store:       s,
		baseURL:     "http://short.test",
		rateLimiter: NewRateLimiter(10, 60*time.Second),
	}
	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	mux.HandleFunc("GET /api/stats/{code}", h.stats)
	srv := httptest.NewServer(mux)
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
	expectedExpiry := link.CreatedAt.Add(3600 * time.Second)
	if !link.ExpiresAt.Equal(expectedExpiry) {
		t.Errorf("ExpiresAt = %v, want %v", link.ExpiresAt, expectedExpiry)
	}
}

func TestCreateWithMaxClicks(t *testing.T) {
	s := newTestStore()
	link, err := s.Create("https://example.com", 0, 3)
	if err != nil {
		t.Fatalf("Create returned error: %v", err)
	}
	if link.MaxClicks == nil {
		t.Error("expected MaxClicks to be set")
	}
	if link.MaxClicks != nil && *link.MaxClicks != 3 {
		t.Errorf("MaxClicks = %d, want 3", *link.MaxClicks)
	}
}

func TestResolveUpToMaxClicksRetires(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 0, 2)

	url1, ok1 := s.Resolve(link.Code)
	if !ok1 {
		t.Fatalf("first Resolve failed")
	}
	if url1 != "https://example.com" {
		t.Errorf("first resolve got url %q", url1)
	}

	url2, ok2 := s.Resolve(link.Code)
	if !ok2 {
		t.Fatalf("second Resolve failed")
	}
	if url2 != "https://example.com" {
		t.Errorf("second resolve got url %q", url2)
	}

	_, ok3 := s.Resolve(link.Code)
	if ok3 {
		t.Error("third Resolve should have failed after hitting max_clicks")
	}

	_, ok := s.Stats(link.Code)
	if ok {
		t.Error("expected Stats to report link not found after retirement")
	}
}

func TestResolveWithoutMaxClicks(t *testing.T) {
	s := newTestStore()
	link, _ := s.Create("https://example.com", 0, 0)

	for i := 0; i < 10; i++ {
		_, ok := s.Resolve(link.Code)
		if !ok {
			t.Fatalf("Resolve %d failed", i+1)
		}
	}

	stats, ok := s.Stats(link.Code)
	if !ok {
		t.Fatal("expected Stats to find link")
	}
	if stats.Clicks != 10 {
		t.Errorf("clicks = %d, want 10", stats.Clicks)
	}
}

func TestResolveExpiredLinkReturns404(t *testing.T) {
	s := &Store{links: make(map[string]*Link)}
	baseTime := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	s.now = func() time.Time { return baseTime }

	link, _ := s.Create("https://example.com", 3600, 0)

	s.now = func() time.Time {
		return time.Date(2026, 6, 1, 13, 1, 0, 0, time.UTC)
	}

	h := &Handler{
		store:       s,
		baseURL:     "http://short.test",
		rateLimiter: NewRateLimiter(10, 60*time.Second),
	}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{code}", h.resolve)
	srv := httptest.NewServer(mux)
	defer srv.Close()
	client := noRedirectClient()

	resp, err := client.Get(srv.URL + "/" + link.Code)
	if err != nil {
		t.Fatalf("GET: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("status = %d, want 404", resp.StatusCode)
	}
}

func TestShortenRejectsNegativeExpiry(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","expires_in_seconds":-1}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestShortenRejectsExcessiveExpiry(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","expires_in_seconds":315360001}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func newTestHandlerWithRateLimit(maxRequests int, windowDuration time.Duration) *Handler {
	s := newTestStore()
	h := &Handler{
		store:       s,
		baseURL:     "http://short.test",
		rateLimiter: NewRateLimiter(maxRequests, windowDuration),
	}
	fixed := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	h.rateLimiter.now = func() time.Time { return fixed }
	return h
}

func TestShortenRateLimitUnderLimit(t *testing.T) {
	h := newTestHandlerWithRateLimit(2, 60*time.Second)
	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	srv := httptest.NewServer(mux)
	defer srv.Close()

	for i := 1; i <= 2; i++ {
		resp := shorten(t, srv, `{"url":"https://example.com"}`)
		if resp.StatusCode != http.StatusCreated {
			t.Errorf("request %d: status = %d, want 201", i, resp.StatusCode)
		}
		resp.Body.Close()
	}
}

func TestShortenRateLimitExceeded(t *testing.T) {
	h := newTestHandlerWithRateLimit(1, 60*time.Second)
	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	srv := httptest.NewServer(mux)
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com"}`)
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("first request: status = %d, want 201", resp.StatusCode)
	}
	resp.Body.Close()

	resp = shorten(t, srv, `{"url":"https://example.com"}`)
	if resp.StatusCode != http.StatusTooManyRequests {
		t.Fatalf("second request: status = %d, want 429", resp.StatusCode)
	}
	resp.Body.Close()
}

func TestShortenRateLimitPerIP(t *testing.T) {
	s := newTestStore()
	h := &Handler{
		store:       s,
		baseURL:     "http://short.test",
		rateLimiter: NewRateLimiter(1, 60*time.Second),
	}
	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	srv := httptest.NewServer(mux)
	defer srv.Close()

	req1, _ := http.NewRequest("POST", srv.URL+"/shorten", strings.NewReader(`{"url":"https://example.com"}`))
	req1.Header.Set("Content-Type", "application/json")
	req1.Header.Set("X-Forwarded-For", "192.168.1.1")

	resp1, _ := http.DefaultClient.Do(req1)
	if resp1.StatusCode != http.StatusCreated {
		t.Errorf("IP1 first: status = %d, want 201", resp1.StatusCode)
	}
	resp1.Body.Close()

	req2, _ := http.NewRequest("POST", srv.URL+"/shorten", strings.NewReader(`{"url":"https://example.com"}`))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("X-Forwarded-For", "192.168.1.2")

	resp2, _ := http.DefaultClient.Do(req2)
	if resp2.StatusCode != http.StatusCreated {
		t.Errorf("IP2 first: status = %d, want 201", resp2.StatusCode)
	}
	resp2.Body.Close()
}

func TestShortenWithCustomCode(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com/path","code":"mycode"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if out.Code != "mycode" {
		t.Errorf("code = %q, want mycode", out.Code)
	}
	if want := "http://short.test/mycode"; out.ShortURL != want {
		t.Errorf("short_url = %q, want %q", out.ShortURL, want)
	}
}

func TestShortenCustomCodeConflict(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	first := shorten(t, srv, `{"url":"https://example.com/one","code":"taken"}`)
	if first.StatusCode != http.StatusCreated {
		t.Fatalf("first request: status = %d, want 201", first.StatusCode)
	}
	first.Body.Close()

	second := shorten(t, srv, `{"url":"https://example.com/two","code":"taken"}`)
	defer second.Body.Close()

	if second.StatusCode != http.StatusConflict {
		t.Errorf("second request: status = %d, want 409", second.StatusCode)
	}
}

func TestShortenCustomCodeResolves(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()
	client := noRedirectClient()

	resp := shorten(t, srv, `{"url":"https://example.com/dest","code":"custom"}`)
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("shorten: status = %d, want 201", resp.StatusCode)
	}
	resp.Body.Close()

	resolveResp, err := client.Get(srv.URL + "/custom")
	if err != nil {
		t.Fatalf("GET /custom: %v", err)
	}
	defer resolveResp.Body.Close()

	if resolveResp.StatusCode != http.StatusFound {
		t.Errorf("status = %d, want 302", resolveResp.StatusCode)
	}
	if loc := resolveResp.Header.Get("Location"); loc != "https://example.com/dest" {
		t.Errorf("Location = %q, want https://example.com/dest", loc)
	}
}

func TestShortenOmittedCodeGeneratesRandom(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if out.Code == "" {
		t.Error("expected a non-empty random code")
	}
	if len(out.Code) != defaultCodeLength {
		t.Errorf("code length = %d, want %d", len(out.Code), defaultCodeLength)
	}
}

func TestShortenInvalidCustomCodeWithSlash(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","code":"a/b"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestShortenInvalidCustomCodeWithSpace(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","code":"a b"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestShortenInvalidCustomCodeTooLong(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","code":"abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", resp.StatusCode)
	}
}

func TestShortenValidCustomCode(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	resp := shorten(t, srv, `{"url":"https://example.com","code":"validCode123"}`)
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		t.Errorf("status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if out.Code != "validCode123" {
		t.Errorf("code = %q, want validCode123", out.Code)
	}
}

func TestShortenCustomCodeConflictAfterValidation(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	first := shorten(t, srv, `{"url":"https://example.com/one","code":"taken123"}`)
	if first.StatusCode != http.StatusCreated {
		t.Fatalf("first request: status = %d, want 201", first.StatusCode)
	}
	first.Body.Close()

	second := shorten(t, srv, `{"url":"https://example.com/two","code":"taken123"}`)
	defer second.Body.Close()

	if second.StatusCode != http.StatusConflict {
		t.Errorf("second request: status = %d, want 409", second.StatusCode)
	}
}

func TestShortenWithMaxClicksViaAPI(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()
	client := noRedirectClient()

	resp := shorten(t, srv, `{"url":"https://example.com/dest","max_clicks":2}`)
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("shorten: status = %d, want 201", resp.StatusCode)
	}
	var out shortenResponse
	_ = json.NewDecoder(resp.Body).Decode(&out)
	resp.Body.Close()

	for i := 1; i <= 2; i++ {
		resolveResp, err := client.Get(srv.URL + "/" + out.Code)
		if err != nil {
			t.Fatalf("resolve %d: %v", i, err)
		}
		if resolveResp.StatusCode != http.StatusFound {
			t.Errorf("resolve %d: status = %d, want 302", i, resolveResp.StatusCode)
		}
		resolveResp.Body.Close()
	}

	resolveResp, err := client.Get(srv.URL + "/" + out.Code)
	if err != nil {
		t.Fatalf("third resolve: %v", err)
	}
	if resolveResp.StatusCode != http.StatusNotFound {
		t.Errorf("third resolve: status = %d, want 404", resolveResp.StatusCode)
	}
	resolveResp.Body.Close()
}

func TestAdminEndpointListsAllLinks(t *testing.T) {
	srv := newTestServer()
	defer srv.Close()

	shorten(t, srv, `{"url":"https://example.com/one"}`)
	shorten(t, srv, `{"url":"https://example.com/two"}`)

	resp, err := http.Get(srv.URL + "/api/admin/links")
	if err != nil {
		t.Fatalf("GET /api/admin/links: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("status = %d, want 200", resp.StatusCode)
	}

	var links []Link
	if err := json.NewDecoder(resp.Body).Decode(&links); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if len(links) != 2 {
		t.Errorf("expected 2 links, got %d", len(links))
	}

	urls := make(map[string]bool)
	for _, link := range links {
		urls[link.URL] = true
		if link.Clicks != 0 {
			t.Errorf("link %s should have 0 clicks, got %d", link.Code, link.Clicks)
		}
	}

	if !urls["https://example.com/one"] || !urls["https://example.com/two"] {
		t.Error("expected both URLs in response")
	}
}

func TestAdminEndpointIncludesClickStats(t *testing.T) {
	s := newTestStore()
	h := &Handler{
		store:       s,
		baseURL:     "http://short.test",
		rateLimiter: NewRateLimiter(10, 60*time.Second),
	}
	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	mux.HandleFunc("GET /api/admin/links", h.admin)
	mux.HandleFunc("GET /{code}", h.resolve)
	srv := httptest.NewServer(mux)
	defer srv.Close()
	client := noRedirectClient()

	resp := shorten(t, srv, `{"url":"https://example.com/dest"}`)
	var out shortenResponse
	_ = json.NewDecoder(resp.Body).Decode(&out)
	resp.Body.Close()

	client.Get(srv.URL + "/" + out.Code)
	client.Get(srv.URL + "/" + out.Code)

	adminResp, err := http.Get(srv.URL + "/api/admin/links")
	if err != nil {
		t.Fatalf("GET /api/admin/links: %v", err)
	}
	defer adminResp.Body.Close()

	var links []Link
	if err := json.NewDecoder(adminResp.Body).Decode(&links); err != nil {
		t.Fatalf("decode: %v", err)
	}

	if len(links) != 1 {
		t.Errorf("expected 1 link, got %d", len(links))
	}

	if links[0].Clicks != 2 {
		t.Errorf("expected 2 clicks, got %d", links[0].Clicks)
	}
}
