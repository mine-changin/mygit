// MD 변환기 런처: 내장된 웹 앱을 로컬(127.0.0.1)에서만 서비스하고 브라우저 창을 엽니다.
// 파일은 컴퓨터 밖으로 전송되지 않습니다.
package main

import (
	"embed"
	"fmt"
	"io/fs"
	"net"
	"net/http"
	"os"
	"sync/atomic"
	"time"
)

//go:embed all:app
var appFS embed.FS

const addr = "127.0.0.1:17843"

var (
	lastPing atomic.Int64 // 마지막 하트비트 (unix 초)
	byeAt    atomic.Int64 // 창을 닫을 때 보내는 신호 (unix 초)
	started  = time.Now().Unix()
)

func main() {
	url := "http://" + addr + "/"
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		// 이미 실행 중이면 새 창만 엽니다.
		openWindow(url)
		return
	}
	sub, _ := fs.Sub(appFS, "app")
	mux := http.NewServeMux()
	mux.Handle("/", noCache(http.FileServer(http.FS(sub))))
	mux.HandleFunc("/__ping", func(w http.ResponseWriter, r *http.Request) {
		lastPing.Store(time.Now().Unix())
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("/__bye", func(w http.ResponseWriter, r *http.Request) {
		byeAt.Store(time.Now().Unix())
		w.WriteHeader(http.StatusNoContent)
	})
	go func() {
		if err := http.Serve(ln, mux); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}()
	openWindow(url)
	// 창이 닫히면 종료: 닫기 신호 후 5초 안에 다시 연결이 없으면 종료(새로고침은 유지),
	// 하트비트가 3분 넘게 없어도 종료(최소화된 탭은 타이머가 느려질 수 있어 여유를 둡니다).
	for {
		time.Sleep(2 * time.Second)
		now := time.Now().Unix()
		lp, bye := lastPing.Load(), byeAt.Load()
		if bye != 0 && now-bye > 5 && lp <= bye {
			return
		}
		if lp == 0 && now-started > 60 {
			return
		}
		if lp != 0 && now-lp > 180 {
			return
		}
	}
}

func noCache(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		h.ServeHTTP(w, r)
	})
}
