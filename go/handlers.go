package main

import (
	"encoding/json"
	"net/http"
	"net/url"
	"strings"
)

type shortenRequest struct {
	URL              string `json:"url"`
	ExpiresInSeconds int64  `json:"expires_in_seconds,omitempty"`
}

type shortenResponse struct {
	Code     string `json:"code"`
	ShortURL string `json:"short_url"`
}

// Handler wires the store to HTTP routes.
type Handler struct {
	store   *Store
	baseURL string
}

// NewHandler returns an http.Handler serving the shortener API.
func NewHandler(store *Store, baseURL string) http.Handler {
	h := &Handler{store: store, baseURL: strings.TrimRight(baseURL, "/")}

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

func (h *Handler) shorten(w http.ResponseWriter, r *http.Request) {
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

	link, err := h.store.Create(req.URL, req.ExpiresInSeconds)
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
