package main

import (
	"encoding/json"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type shortenRequest struct {
	URL              string `json:"url"`
	Code             string `json:"code,omitempty"`
	ExpiresInSeconds int64  `json:"expires_in_seconds,omitempty"`
}

type shortenResponse struct {
	Code     string `json:"code"`
	ShortURL string `json:"short_url"`
}

// Handler wires the store to HTTP routes.
type Handler struct {
	store       *Store
	baseURL     string
	rateLimiter *RateLimiter
}

// NewHandler returns an http.Handler serving the shortener API.
func NewHandler(store *Store, baseURL string) http.Handler {
	h := &Handler{
		store:       store,
		baseURL:     strings.TrimRight(baseURL, "/"),
		rateLimiter: NewRateLimiter(10, 60*time.Second),
	}

	mux := http.NewServeMux()
	mux.HandleFunc("POST /shorten", h.shorten)
	mux.HandleFunc("GET /api/stats/{code}", h.stats)
	mux.HandleFunc("GET /{code}", h.resolve)
	return mux
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

// validShortenURL reports whether a string is an absolute http(s) URL.
func validShortenURL(raw string) bool {
	u, err := url.Parse(raw)
	if err != nil {
		return false
	}
	return (u.Scheme == "http" || u.Scheme == "https") && u.Host != ""
}

// validCustomCode reports whether a custom code is valid.
// Valid codes contain only alphanumeric characters and are at most 32 characters long.
func validCustomCode(code string) bool {
	if code == "" || len(code) > 32 {
		return false
	}
	for _, ch := range code {
		if !((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
			return false
		}
	}
	return true
}

// clientIP extracts the client IP from the request.
func clientIP(r *http.Request) string {
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		if ip, _, err := net.SplitHostPort(forwarded); err == nil {
			return ip
		}
		return forwarded
	}
	ip, _, _ := net.SplitHostPort(r.RemoteAddr)
	return ip
}

func (h *Handler) shorten(w http.ResponseWriter, r *http.Request) {
	ip := clientIP(r)
	if !h.rateLimiter.Allow(ip) {
		writeError(w, http.StatusTooManyRequests, "rate limit exceeded")
		return
	}

	var req shortenRequest
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid JSON body")
		return
	}
	if decoder.More() {
		writeError(w, http.StatusBadRequest, "body must contain a single JSON object")
		return
	}
	if !validShortenURL(req.URL) {
		writeError(w, http.StatusBadRequest, "url must be an absolute http or https URL")
		return
	}
	if req.ExpiresInSeconds < 0 {
		writeError(w, http.StatusBadRequest, "expires_in_seconds must be non-negative")
		return
	}
	const maxExpiresInSeconds = 315360000
	if req.ExpiresInSeconds > maxExpiresInSeconds {
		writeError(w, http.StatusBadRequest, "expires_in_seconds must be at most 10 years")
		return
	}

	var link Link
	var err error
	if req.Code != "" {
		if !validCustomCode(req.Code) {
			writeError(w, http.StatusBadRequest, "code must be alphanumeric and at most 32 characters")
			return
		}
		link, err = h.store.CreateWithCode(req.URL, req.Code, req.ExpiresInSeconds)
		if err == ErrCodeTaken {
			writeError(w, http.StatusConflict, "short code already taken")
			return
		}
	} else {
		link, err = h.store.Create(req.URL, req.ExpiresInSeconds)
	}
	if err != nil {
		writeError(w, http.StatusInternalServerError, "could not create short link")
		return
	}
	writeJSON(w, http.StatusCreated, shortenResponse{
		Code:     link.Code,
		ShortURL: h.baseURL + "/" + link.Code,
	})
}

func (h *Handler) resolve(w http.ResponseWriter, r *http.Request) {
	code := r.PathValue("code")
	target, ok := h.store.Resolve(code)
	if !ok {
		writeError(w, http.StatusNotFound, "unknown short code")
		return
	}
	http.Redirect(w, r, target, http.StatusFound)
}

func (h *Handler) stats(w http.ResponseWriter, r *http.Request) {
	code := r.PathValue("code")
	link, ok := h.store.Stats(code)
	if !ok {
		writeError(w, http.StatusNotFound, "unknown short code")
		return
	}
	writeJSON(w, http.StatusOK, link)
}
