//go:build !windows

package main

import (
	"fmt"
	"os/exec"
	"runtime"
)

// 개발·테스트용 (Windows 외)
func openWindow(url string) {
	if runtime.GOOS == "darwin" {
		exec.Command("open", url).Start()
		return
	}
	if p, err := exec.LookPath("xdg-open"); err == nil {
		exec.Command(p, url).Start()
		return
	}
	fmt.Println("열기:", url)
}
