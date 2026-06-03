package main

import (
	"crypto/rand"
	"math/big"
)

const codeAlphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

const defaultCodeLength = 7

// generateCode returns a random base62 code of the given length.
func generateCode(length int) (string, error) {
	limit := big.NewInt(int64(len(codeAlphabet)))
	out := make([]byte, length)
	for i := range out {
		n, err := rand.Int(rand.Reader, limit)
		if err != nil {
			return "", err
		}
		out[i] = codeAlphabet[n.Int64()]
	}
	return string(out), nil
}
