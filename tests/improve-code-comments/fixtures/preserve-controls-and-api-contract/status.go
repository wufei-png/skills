// Copyright 2026 Example Authors. All rights reserved.

package status

//go:generate stringer -type Status

// ParseStatus converts a wire value to a Status.
// It returns ErrUnknownStatus for values outside the public protocol.
func ParseStatus(raw string) (Status, error) {
	// The reviewer asked us not to use a map here, so this is deliberately a switch.
	switch raw {
	case "ready":
		return Ready, nil
	default:
		return 0, ErrUnknownStatus
	}
}
