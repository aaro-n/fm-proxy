# 使用 Golang 官方镜像
FROM golang:1.20

# 设置工作目录
WORKDIR /app

# 复制源代码
COPY . .

# 初始化 Go 模块
RUN go mod init fm-proxy || true

# 下载依赖
RUN go mod tidy

# 编译应用
RUN go build -o fm-proxy .

# 设置环境变量
ENV FM_USER="fm"
ENV FM_PASSWORD="1234"
ENV FM_ACCESS_KEY="5555"
ENV FM_M3U8_URL_1="http://ngcdn001.cnr.cn/live/zgzs/index.m3u8"
ENV FM_MP3_NAME_1="cnr1.mp3"
ENV FM_MP3_PATH_1="cnr1"
ENV FM_M3U8_URL_2="http://ngcdn002.cnr.cn/live/jjzs/index.m3u8"
ENV FM_MP3_NAME_2="cnr2.mp3"
ENV FM_MP3_PATH_2="cnr2"
ENV FM_M3U8_URL_18="http://ngcdn003.cnr.cn/live/yyzs/index.m3u8"
ENV FM_MP3_NAME_18="cnr3.mp3"
ENV FM_MP3_PATH_18="cnr3"
ENV FM_M3U8_URL_4="http://ngcdn010.cnr.cn/live/wyzs/index.m3u8"
ENV FM_MP3_NAME_4="cnr4.mp3"
ENV FM_MP3_PATH_4="cnr4"

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["./fm-proxy"]
