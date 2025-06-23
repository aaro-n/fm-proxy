package main

import (
    "fmt"
    "log"
    "net/http"
    "os"
    "os/exec"
    "sync"
)

var (
    users = map[string]string{
        "fm": "1234",
    }
    accessKeys = map[string]string{
        "5555": "allowed",
    }
    m3u8Urls = map[string]string{
        "cnr1": os.Getenv("FM_M3U8_URL_1"),
        "cnr2": os.Getenv("FM_M3U8_URL_2"),
        "cnr3": os.Getenv("FM_M3U8_URL_18"),
        "cnr4": os.Getenv("FM_M3U8_URL_4"),
    }
    mp3Names = map[string]string{
        "cnr1": os.Getenv("FM_MP3_NAME_1"),
        "cnr2": os.Getenv("FM_MP3_NAME_2"),
        "cnr3": os.Getenv("FM_MP3_NAME_18"),
        "cnr4": os.Getenv("FM_MP3_NAME_4"),
    }
    mp3Paths = map[string]string{
        "cnr1": os.Getenv("FM_MP3_PATH_1"),
        "cnr2": os.Getenv("FM_MP3_PATH_2"),
        "cnr3": os.Getenv("FM_MP3_PATH_18"),
        "cnr4": os.Getenv("FM_MP3_PATH_4"),
    }
)

var (
    ffmpegProcesses = make(map[string]*exec.Cmd)
    mu              sync.Mutex
)

func main() {
    http.HandleFunc("/", streamHandler)
    log.Println("Server started on :8000")
    log.Fatal(http.ListenAndServe(":8000", nil))
}

func streamHandler(w http.ResponseWriter, r *http.Request) {
    key := r.URL.Query().Get("key")
    user, pass, ok := r.BasicAuth()

    if !ok && key != "" && accessKeys[key] == "" {
        http.Error(w, "Unauthorized", http.StatusUnauthorized)
        return
    }

    if ok {
        if pass != users[user] {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
    }

    path := r.URL.Path[1:] // Strip leading '/'
    if _, exists := m3u8Urls[path]; !exists {
        http.NotFound(w, r)
        return
    }

    if err := startFFmpeg(path); err != nil {
        http.Error(w, "Error starting FFmpeg", http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "audio/mpeg")
    http.ServeFile(w, r, fmt.Sprintf("%s/%s", mp3Paths[path], mp3Names[path]))
}

func startFFmpeg(path string) error {
    mu.Lock()
    defer mu.Unlock()

    if cmd, exists := ffmpegProcesses[path]; exists {
        return nil // FFmpeg already running
    }

    cmd := exec.Command("ffmpeg", "-i", m3u8Urls[path], "-c", "copy", fmt.Sprintf("%s/%s", mp3Paths[path], mp3Names[path]))
    err := cmd.Start()
    if err != nil {
        return err
    }

    ffmpegProcesses[path] = cmd

    go func() {
        if err := cmd.Wait(); err != nil {
            log.Println("FFmpeg process exited:", err)
        }
        mu.Lock()
        delete(ffmpegProcesses, path)
        mu.Unlock()
    }()

    return nil
}
