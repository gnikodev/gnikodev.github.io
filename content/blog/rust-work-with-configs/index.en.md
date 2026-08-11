+++
title = "Rust. Working with configurations"
description = "A way to hook up and use configurations in Rust projects."
date = 2025-08-17
updated = 2025-08-17
taxonomies = { tags = ["rust","config","config-rs","dotenvy"], categories = [] }

draft = false
in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

Like in any application, whether it's Web or Desktop, you need to use configurations. They can be stored in the runtime environment's variables, or in separate files, like `json`, `xml`, `env`, or `toml`.

In many programming languages, C# for example, working with configurations is already standardized, and you can use ready-made libraries that provide full-fledged functionality. In Rust, though, you have to hunt for separate crates. In this article we'll look at the crates I use myself in my own projects for working with configurations.

## 1. `dotenvy` — working with `.env` files

The `dotenvy` crate provides a convenient way to load environment variables from `.env` files. This is especially handy during application development, when you don't want to write configuration values into the system's environment variables.

### Installation

Add to `Cargo.toml`:

```toml
[dependencies]
dotenvy = "0.15"
```

or you can just run

```bash
cargo add dotenvy
```

### Usage example

```rust
use dotenvy::dotenv;
use std::env;

fn main() {
    dotenv().ok(); // Loads variables from the .env file

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    println!("Database URL: {}", database_url);
}
```

### Best practices

1. **Don't commit `.env` files** — add them to `.gitignore`. To give users a template for the configuration, it's enough to make a separate `.env.example` file that contains examples without any actual values.
2. **Check that variables are present** — always handle the error case when a variable isn't set.
3. **`.env.local` for local development** — I use this file for a simplified local config, and it's simply added to `.gitignore`.

If you use an `.env.local` file, you can slightly improve the `dotenvy` initialization so it decides which source file to use:

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

Unfortunately, I couldn't cleanly factor out the common handling of `load_result`, because `from_path` and `dotenv` have different return types.

---

## 2. `envconfig` — automatically parsing environment variables into structs

`envconfig` lets you automatically parse environment variables into Rust structs, which makes working with configuration more convenient and type-safe.

### Installation

```toml
[dependencies]
envconfig = { version = "0.13", features = ["derive"] }
```

### Usage example

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

### Best practices

1. **Use `default`** — set default values for variables that aren't critical.
2. **Group your configurations** — create separate structs for different parts of the application (for example, `DatabaseConfig`, `ServerConfig`).
3. **Document the variables** — add comments to struct fields so it's clear which variables are required.

---

## 3. `config-rs` — a universal configuration crate

`config-rs` is a powerful crate for working with configurations, supporting a wide range of formats (`JSON`, `YAML`, `TOML`, and others) and sources (files, environment variables).

### Installation

```toml
[dependencies]
config = { version = "0.15", features = ["json"] }
serde = { version = "1.0", features = ["derive"] }
```

### Usage example (TOML + environment variables)

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
        // Read from `config.toml`
        .add_source(File::with_name("config"))
        // Environment variables prefixed with `APP_` (e.g. `APP_PORT=8080`)
        .add_source(Environment::with_prefix("APP"))
        .build()
        .unwrap();

    let app_config: AppConfig = config.try_deserialize().unwrap();

    println!("Config: {:?}", app_config);
}
```

### Nested structs with TOML

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

Loading the config:

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

### Nested structs with arrays

Structs:

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

### Using `config-rs` with environment variables for nested structs

In this case, variable names are formed according to the following rules:

#### Standard approach (with `_` as separator)

For the struct above, the environment variables would be named like this:

```bash
APP_DATABASE_CFG_CONNECTION_STRING=your_connection_string
APP_DATABASE_CFG_CONNECTION_ROLE=your_role
APP_BOT_CFG_TOKEN=your_bot_token
APP_BOT_CFG_WEBHOOK_URL=your_webhook_url
```

Loading example:

```rust
let cfg = Config::builder()
    .add_source(Environment::with_prefix("APP").separator("_"))
    .build()?;
```

#### Alternative naming options

1. **Custom separator** (for example, `__`):

   ```rust
   // Variables will look like: APP__DATABASE_CFG__CONNECTION_STRING
   .add_source(Environment::with_prefix("APP").separator("__"))
   ```

2. **Simplified naming** (ignoring the names of nested structs):

   ```bash
   APP_DB_CONNECTION_STRING
   APP_BOT_TOKEN
   ```

   (but then you have to map the fields manually)

3. **Prefixes by feature area**:

   ```bash
   DB_CONNECTION_STRING
   BOT_TOKEN
   ```

   (using different prefixes for different components)

## How to make the naming more convenient

1. **Use a flatter structure**:

   ```rust
   pub struct AppCfg {
       pub db_connection_string: String,
       pub db_connection_role: String,
       pub bot_token: String,
       pub bot_webhook_url: String,
   }
   ```

   Then the variables become simpler:

   ```bash
   APP_DB_CONNECTION_STRING
   APP_BOT_TOKEN
   ```

1. **Customize names via attributes**:

   ```rust
   #[derive(Deserialize)]
   pub struct DatabaseCfg {
       #[serde(rename = "DB_CONN_STR")]
       pub connection_string: String,

       #[serde(rename = "DB_ROLE")]
       pub connection_role: String,
   }
   ```

### Best practices

1. **Use hierarchical configs** — split the configuration across different files (`database.toml`, `server.toml`).
1. **Use separate configurations for different environments** — this is an approach that exists in `dotnet` too, namely files like `appsettings.staging.json`, `appsettings.production.json`.
1. **Override values via environment variables** — this is useful for deployment (for example, in Docker).
1. **Combine sources** — you can load configuration from a file and override part of the values through env variables.
1. **Use optional fields**

   ```rust
   #[derive(Deserialize)]
   pub struct OptionalConfig {
       #[serde(default)]
       pub cache_size: Option<usize>,
   }
   ```

1. **Use prefixes for env variables**

   ```rust
   // For a config like:
   struct A { struct B { field: String } }

   // it will look up the variable:
   APP_A_B_FIELD=value
   ```

---

## Conclusion

Rust has no "official" way of working with configurations, but thanks to crates you can pick whatever approach suits you:

- **`dotenvy`** — a simple way to load `.env` files.
- **`envconfig`** — automatic parsing of env variables into structs.
- **`config-rs`** — a powerful tool for complex configurations with support for many formats.

The choice depends on your needs: for small projects, `dotenvy` + `envconfig` will do fine, while for larger ones — `config-rs`.

---

In my own projects I use `dotenvy` and `config-rs`. At first I only worked with `envconfig`, but its functionality just wasn't enough for full-fledged work.

Hope this article helps you work with configurations in Rust more conveniently! 🚀
