+++
title = "Rust. Работа с конфигурациями"
description = "Способ подключения и использования конфигураций в Rust проектах."
date = 2025-08-17
updated = 2025-08-17
taxonomies = { tags = ["rust","config","config-rs","dotenvy"], categories = [] }

draft = false
in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

Как в любом приложении, хоть Web, хоть Desktop, необходимо использовать конфигурации. Они могут быть записаны в переменных окружения среды выполнения, либо же в отдельных файлах, таких как `json`, `xml`, `env` или `toml`.

Во многих языках программирования, например в C#, работа с конфигурациями уже является стандартизированной, и можно использовать готовые библиотеки, которые предоставляют полноценный функционал. В Rust же необходимо искать отдельные крейты. В этой статье рассмотрим те крейты, которые я сам использую в своих проектах для работы с конфигурациями.

## 1. `dotenvy` — работа с `.env` файлами

Крейт `dotenvy` предоставляет удобный способ загрузки переменных окружения из `.env` файлов. Это особенно полезно при разработке приложений, когда не хочется прописывать конфигурации в переменных окружения системы.

### Установка

Добавьте в `Cargo.toml`:

```toml
[dependencies]
dotenvy = "0.15"
```

или можно выполнить команду

```bash
cargo add dotenvy
```

### Пример использования

```rust
use dotenvy::dotenv;
use std::env;

fn main() {
    dotenv().ok(); // Загружает переменные из .env файла

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    println!("Database URL: {}", database_url);
}
```

### Лучшие практики

1. **Не следует коммитить `.env` файлы** — добавляйте их в `.gitignore`. Для того, чтобы пользователям обозначить шаблон конфигураций достаточно сделать отдельный файл `.env.example`, который будет содержать примеры, но без конкретных значений
2. **Проверяйте наличие переменных** — всегда обрабатывайте ошибки, если переменная не установлена.
3. **`.env.local` для локальной разработки** - я использую этот файл для упрощенной локальной конфигурации, при этом он просто добавлен в `.gitingone`

Если использовать файл `.env.local`, то можно чуть улучшить инициализацию `dotenvy`, в котором будет определяться выбор исходного файла

```rust
pub fn add_configuration() -> Result<Config, AddConfigurationError> {
    load_env_file()?;
    ...
}

fn load_env_file() -> Result<(), AddConfigurationError> {
    let local_env_path = Path::new(".env.local");
    if local_env_path.exists() {
        let load_result = dotenvy::from_path(local_env_path);
        match load_result {
            Ok(_) => Ok(()),
            Err(err) => Err(AddConfigurationError::from(err)),
        }
    } else {
        let load_result = dotenvy::dotenv();
        match load_result {
            Ok(_) => Ok(()),
            Err(err) => Err(AddConfigurationError::from(err)),
        }
    }
}
```

Увы, не получилось нормально вынести в общую обработку результата `load_result`, потому что `from_path` и `dotenv` имеют разное возвращаемое значение.

---

## 2. `envconfig` — автоматическое парсинг переменных окружения в структуры

`envconfig` позволяет автоматически парсить переменные окружения в Rust-структуры, что делает работу с конфигурациями более удобной и типобезопасной.

### Установка

```toml
[dependencies]
envconfig = { version = "0.13", features = ["derive"] }
```

### Пример использования

```rust
use envconfig::Envconfig;

#[derive(Envconfig)]
struct Config {
    #[envconfig(from = "DATABASE_URL", default = "postgres://localhost:5432")]
    pub database_url: String,

    #[envconfig(from = "PORT", default = "8080")]
    pub port: u16,
}

fn main() {
    let config = Config::init().unwrap();

    println!("Database URL: {}", config.database_url);
    println!("Port: {}", config.port);
}
```

### Лучшие практики

1. **Используйте `default`** — задавайте значения по умолчанию для переменных, которые не критичны.
2. **Группируйте конфигурации** — создавайте отдельные структуры для разных частей приложения (например, `DatabaseConfig`, `ServerConfig`).
3. **Документируйте переменные** — добавляйте комментарии к полям структуры, чтобы было понятно, какие переменные нужны.

---

## 3. `config-rs` — универсальный конфигурационный крейт

`config-rs` — это мощный крейт для работы с конфигурациями, который поддерживает множество форматов (`JSON`, `YAML`, `TOML` и др.) и источников (файлы, переменные окружения).

### Установка

```toml
[dependencies]
config = { version = "0.15", features = ["json"] }
serde = { version = "1.0", features = ["derive"] }
```

### Пример использования (TOML + переменные окружения)

```rust
use config::{Config, Environment, File};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct AppConfig {
    database_url: String,
    port: u16,
    debug: bool,
}

fn main() {
    let config = Config::builder()
        // Читаем из `config.toml`
        .add_source(File::with_name("config"))
        // Переменные окружения с префиксом `APP_` (например, `APP_PORT=8080`)
        .add_source(Environment::with_prefix("APP"))
        .build()
        .unwrap();

    let app_config: AppConfig = config.try_deserialize().unwrap();

    println!("Config: {:?}", app_config);
}
```

### Вложенные структуры с TOML

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
    pub pool_size: u32,
}

#[derive(Debug, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Deserialize)]
pub struct AppCfg {
    pub database: DatabaseConfig,
    pub server: ServerConfig,
    pub debug: bool,
}
```

config.toml:

```toml
[database]
url = "postgres://user:pass@localhost:5432/db"
pool_size = 20

[server]
host = "0.0.0.0"
port = 8080

debug = true
```

Загрузка конфига:

```rust
use config::Config;

fn main() {
    let cfg = Config::builder()
        .add_source(config::File::with_name("config"))
        .build()
        .unwrap();

    let app_cfg: AppCfg = cfg.try_deserialize().unwrap();

    println!("DB URL: {}", app_cfg.database.url);
    println!("Server port: {}", app_cfg.server.port);
}
```

### Вложенные структуры с массивами

Структуры:

```rust
#[derive(Debug, Deserialize)]
pub struct RedisConfig {
    pub hosts: Vec<String>,
    pub timeout_ms: u64,
}

#[derive(Debug, Deserialize)]
pub struct AppCfg {
    pub redis: RedisConfig,
    pub allowed_origins: Vec<String>,
}
```

config.yaml:

```yaml
redis:
  hosts:
    - 'redis1:6379'
    - 'redis2:6379'
  timeout_ms: 500

allowed_origins:
  - 'https://example.com'
  - 'https://api.example.com'
```

### Использование `config-rs` с переменными окружения для вложенных структур

В таком случае имена переменных формируются по следующим правилам:

#### Стандартный подход (с разделителем `_`)

Для структуры переменные окружения будут называться так:

```bash
APP_DATABASE_CFG_CONNECTION_STRING=your_connection_string
APP_DATABASE_CFG_CONNECTION_ROLE=your_role
APP_BOT_CFG_TOKEN=your_bot_token
APP_BOT_CFG_WEBHOOK_URL=your_webhook_url
```

Пример загрузки:

```rust
let cfg = Config::builder()
    .add_source(Environment::with_prefix("APP").separator("_"))
    .build()?;
```

#### Альтернативные варианты именования

1. **Кастомный разделитель** (например, `__`):

   ```rust
   // Переменные будут: APP__DATABASE_CFG__CONNECTION_STRING
   .add_source(Environment::with_prefix("APP").separator("__"))
   ```

2. **Упрощенное именование** (игнорируя названия вложенных структур):

   ```bash
   APP_DB_CONNECTION_STRING
   APP_BOT_TOKEN
   ```

   (но тогда нужно вручную мапить поля)

3. **Префиксы по функциональности**:

   ```bash
   DB_CONNECTION_STRING
   BOT_TOKEN
   ```

   (используя разные префиксы для разных компонентов)

## Как сделать именование более удобным

1. **Использовать более плоскую структуру**:

   ```rust
   pub struct AppCfg {
       pub db_connection_string: String,
       pub db_connection_role: String,
       pub bot_token: String,
       pub bot_webhook_url: String,
   }
   ```

   Тогда переменные будут проще:

   ```bash
   APP_DB_CONNECTION_STRING
   APP_BOT_TOKEN
   ```

1. **Кастомизировать имена через атрибуты**:

   ```rust
   #[derive(Deserialize)]
   pub struct DatabaseCfg {
       #[serde(rename = "DB_CONN_STR")]
       pub connection_string: String,

       #[serde(rename = "DB_ROLE")]
       pub connection_role: String,
   }
   ```

### Лучшие практики

1. **Используйте иерархические конфиги** — разделяйте конфигурацию по разным файлам (`database.toml`, `server.toml`).
1. **Используйте конфигурации для разных сред** - подобный подход есть в `dotnet`. А именно файлы подобные `appsettings.staging.json`, `appsettings.production.json`
1. **Переопределяйте значения через переменные окружения** — это полезно для деплоя (например, в Docker).
1. **Комбинируйте источники** — можно загружать конфигурацию из файла и переопределять часть значений через env-переменные.
1. **Использование опциональных полей**

   ```rust
   #[derive(Deserialize)]
   pub struct OptionalConfig {
       #[serde(default)]
       pub cache_size: Option<usize>,
   }
   ```

1. **Использование префиксов для env-переменных**

   ```rust
   // Для конфига:
   struct A { struct B { field: String } }

   // Будет искать переменную:
   APP_A_B_FIELD=value
   ```

---

## Заключение

В Rust нет "официального" способа работы с конфигурациями, но благодаря крейтам можно выбрать удобный подход:

- **`dotenvy`** — простой способ загружать `.env` файлы.
- **`envconfig`** — автоматический парсинг env-переменных в структуры.
- **`config-rs`** — мощный инструмент для сложных конфигураций с поддержкой множества форматов.

Выбор зависит от ваших потребностей: для маленьких проектов подойдет `dotenvy` + `envconfig`, а для больших — `config-rs`.

---

Я в своих проектах использую `dotenvy` и `config-rs`. По началу работал только с `envconfig`, но его функционала все таки не хватает для полноценной работы.

Надеюсь, эта статья поможет вам удобно работать с конфигурациями в Rust! 🚀
