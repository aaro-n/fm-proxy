use actix_web::{web, App, HttpResponse, HttpServer, Responder, middleware::Logger};
use std::env;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use log::{info, error};

#[macro_use]
extern crate log;

#[derive(Clone)]
struct AppState {
    active_processes: Arc<Mutex<Vec<String>>>,
}

async fn stream(path_value: web::Path<(String, String)>, state: web::Data<AppState>) -> impl Responder {
    let (path_value, filename) = path_value.into_inner();
    
    let mut stream_id = None;

    for (key, value) in env::vars() {
        if key.starts_with("FM_MP3_NAME_") && value == filename {
            let i = key.split('_').last().unwrap();
            if path_value == env::var(format!("FM_MP3_PATH_{}", i)).unwrap_or_default() {
                stream_id = Some(i.to_string());
                break;
            }
        }
    }

    if stream_id.is_none() {
        error!("请求的文件名或路径不匹配。");
        return HttpResponse::NotFound().body("请求的文件名或路径不匹配。");
    }

    // 处理流逻辑
    HttpResponse::Ok().body("Streaming...")
}

fn report_memory_usage() {
    loop {
        let memory_info = psutil::memory::virtual_memory().unwrap();
        info!("Memory Usage: {:.2} MB", memory_info.used / (1024 * 1024));
        thread::sleep(Duration::from_secs(300));
    }
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    simplelog::SimpleLogger::init(log::LevelFilter::Info, simplelog::Config::default()).unwrap();

    let state = AppState {
        active_processes: Arc::new(Mutex::new(vec![])),
    };

    thread::spawn(move || {
        report_memory_usage();
    });

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(state.clone()))
            .wrap(Logger::default())
            .route("/{path_value}/{filename}", web::get().to(stream))
    })
    .bind("0.0.0.0:8000")?
    .run()
    .await
}
