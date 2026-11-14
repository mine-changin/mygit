//go:build windows

package main

import (
	"os"
	"os/exec"
	"path/filepath"
)

// Edge 앱 창(주소창 없는 독립 창)으로 열고, 없으면 기본 브라우저로 엽니다.
func openWindow(url string) {
	candidates := []string{}
	for _, env := range []string{"ProgramFiles(x86)", "ProgramFiles", "LocalAppData"} {
		if base := os.Getenv(env); base != "" {
			candidates = append(candidates, filepath.Join(base, "Microsoft", "Edge", "Application", "msedge.exe"))
		}
	}
	if p, err := exec.LookPath("msedge.exe"); err == nil {
		candidates = append([]string{p}, candidates...)
	}
	for _, c := range candidates {
		if _, err := os.Stat(c); err == nil {
			if exec.Command(c, "--app="+url, "--window-size=1280,860").Start() == nil {
				return
			}
		}
	}
	exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
}
