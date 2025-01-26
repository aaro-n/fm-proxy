from flask import Flask, Response, stream_with_context, request, abort
import subprocess
import os
import psutil
import threading
import time
import logging

app = Flask(__name__)

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定义内存报告函数
def report_memory_usage():
    while True:
        process = psutil.Process()
        memory_info = process.memory_info()
        logging.info(f"Memory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")
        time.sleep(300)

# 启动后台线程
threading.Thread(target=report_memory_usage, daemon=True).start()

# 用于存储当前活动的 ffmpeg 进程
active_processes = {}

def check_auth(username, password):
    return username == os.getenv('FM_USER') and password == os.getenv('FM_PASSWORD')

def authenticate():
    return Response(
        '请提供用户名和密码！',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route('/<path:path_value>/<filename>')
def stream(path_value, filename):
    stream_id = None

    for key in os.environ:
        if key.startswith('FM_MP3_NAME_'):
            i = key.split('_')[-1]
            if filename == os.getenv(key) and path_value == os.getenv(f'FM_MP3_PATH_{i}'):
                stream_id = i
                break

    # 如果流 ID 无效，直接返回，不进行认证
    if stream_id is None:
        logging.error("请求的文件名或路径不匹配。")
        return "请求的文件名或路径不匹配。", 404

    # 检查是否设置了 FM_ACCESS_KEY
    access_key = request.args.get('key')
    if os.getenv('FM_ACCESS_KEY') and access_key == os.getenv('FM_ACCESS_KEY'):
        logging.info("通过 FM_ACCESS_KEY 认证访问。")
        # 认证成功后，不再使用 access_key 参数
    else:
        # 进行用户认证，仅在环境变量不为空时
        if os.getenv('FM_USER') and os.getenv('FM_PASSWORD'):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()

    m3u8_url = os.getenv(f'FM_M3U8_URL_{stream_id}')
    
    if not m3u8_url:
        logging.error(f"FM_M3U8_URL_{stream_id} 环境变量未设置。")
        return f"FM_M3U8_URL_{stream_id} 环境变量未设置。", 400

    # 如果流已经在运行，直接返回
    if stream_id in active_processes:
        logging.info(f"流 {stream_id} 已在运行，返回现有流。")
        process = active_processes[stream_id]
    else:
        command = ['ffmpeg', '-i', m3u8_url, '-f', 'mp3', '-']
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_processes[stream_id] = process
        logging.info(f"开始流式传输: {m3u8_url}，流 ID: {stream_id}")

    def generate():
        try:
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data
        except BrokenPipeError:
            logging.warning(f"流 {stream_id} 的 Broken pipe error: 客户端可能已关闭连接。")
        except GeneratorExit:
            logging.info(f"流 {stream_id} 的生成器被关闭，准备终止 ffmpeg 进程。")
        finally:
            # 关闭 ffmpeg 进程
            process.terminate()
            process.wait()
            del active_processes[stream_id]  # 从活动进程中移除
            logging.info(f"ffmpeg 进程已终止，流 {stream_id} 被关闭。")

    return Response(stream_with_context(generate()), content_type='audio/mpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

