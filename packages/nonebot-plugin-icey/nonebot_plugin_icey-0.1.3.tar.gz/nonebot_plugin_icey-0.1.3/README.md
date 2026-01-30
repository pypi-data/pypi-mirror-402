<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://ghfast.top/https://raw.githubusercontent.com/Fansirsqi/nonebot-plugin-icey/refs/heads/main/.docs/Nonebot-Plugin-Icey.svg" alt="logo"></a>


## ✨ nonebot-plugin-icey ✨
[![python](https://img.shields.io/badge/python-3.11|3.12|3.13-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Fansirsqi/nonebot-plugin-icey/main.svg)](https://results.pre-commit.ci/latest/github/Fansirsqi/nonebot-plugin-icey/main)

</div>
# Getting Started

## Install Preview

[![asciicast](https://asciinema.org/a/bqOZS0o36s8Gjjwg.svg)](https://asciinema.org/a/bqOZS0o36s8Gjjwg)

---


## 1. Create a Bot Project
>If you already have a bot environment, you can skip this step.

Ensure you have the `nb-cli` tool installed in your environment.

`uv tool install nb-cli`

(In the following CLI operations, use arrow keys to navigate, Space to select, and Enter to confirm.)

`nb init` Choose a template, enter the project name, e.g., `icey`

Adapters: `onebotv11`, `telegram`

Drivers: `fastapi`, `httpx`, `websockets`

Storage Policy: `Current Project`

Do not install dependencies immediately: `n`

```bash
[?] Project name: icey
[?] Which adapters to use? OneBot V11 (OneBot V11 Protocol), Telegram (Telegram Protocol)
[?] Which drivers to use? FastAPI (FastAPI Driver), HTTPX (HTTPX Driver), websockets (websockets Driver)
[?] What local storage policy to use? Current Project (Suitable for multi-instance/portable instance)
[?] Install dependencies immediately? n
Done!
Run the following command to start your bot:
  cd icey
  nb run --reload
```

Now navigate to the project directory.

Synchronize NoneBot dependencies.

`uv sync`

## 2. Add This Module's Dependencies

`uv add nonebot-plugin-icey` / `pip install nonebot-plugin-icey` / `pdm add nonebot-plugin-icey` / `poetry add nonebot-plugin-icey` - any one of these should work.

> [!IMPORTANT]
Please ensure to append the loading of the `nonebot-plugin-icey` plugin under the `[tool.nonebot.plugins]` section in your `pyproject.toml` file.

```toml
[tool.nonebot.plugins] # Under this configuration item, if not manually added before
...
nonebot_plugin_icey = ["nonebot_plugin_icey"] # Append this line
...

```

> [!NOTE]
The following steps need to be executed after each update/upgrade or during the first initialization.

`nb orm revision -m "xxxx_date"`

`nb orm upgrade`

`nb run --reload`

```bash
➜ nb orm revision -m "2026_01_22_15_10"
Using Python: xxxxxxxxxxxx\.venv\Scripts\python.exe
01-22 15:02:03 [SUCCESS] nonebot | NoneBot is initializing...
01-22 15:02:03 [INFO] nonebot | Current Env: prod
01-22 15:02:04 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_localstore"
01-22 15:02:05 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_orm"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.common"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.welcome"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.help"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.request"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.verify"
01-22 15:02:05 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.filters"
01-22 15:02:05 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_icey"
Generating xxxxxxxxxxx\tmpo10400vs\f3408d0c8073_xxxx_date.py ... done
root in icey on master ≢  ?1
➜ nb run --reload
Using Python: D:\Githubs\bot_test\icey\.venv\Scripts\python.exe
Starting reload watcher, current process [2978456].
01-22 15:02:12 [SUCCESS] nonebot | NoneBot is initializing...
01-22 15:02:12 [INFO] nonebot | Current Env: prod
01-22 15:02:13 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_localstore"
01-22 15:02:13 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_orm"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.common"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.welcome"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.help"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.request"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.verify"
01-22 15:02:13 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.filters"
01-22 15:02:13 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_icey"
01-22 15:02:13 [SUCCESS] nonebot | Running NoneBot...
01-22 15:02:13 [SUCCESS] nonebot | Loaded adapters: OneBot V11, Telegram
01-22 15:02:13 [INFO] uvicorn | Started server process [2977836]
01-22 15:02:13 [INFO] uvicorn | Waiting for application startup.
Target database is not up to date with the latest migration, update? [y/N]: y
01-22 15:02:16 [INFO] uvicorn | Application startup complete.
01-22 15:02:16 [INFO] uvicorn | Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
Watchfiles detected changes in "data\nonebot_plugin_orm\migrations\f3408d0c8073_xxxx_date.py". Reloading...
01-22 15:02:16 [INFO] uvicorn | Shutting down
01-22 15:02:16 [INFO] uvicorn | Waiting for application shutdown.
01-22 15:02:16 [INFO] uvicorn | Application shutdown complete.
01-22 15:02:16 [INFO] uvicorn | Finished server process [2977836]
Restarting process [2974968].
01-22 15:02:17 [SUCCESS] nonebot | NoneBot is initializing...
01-22 15:02:17 [INFO] nonebot | Current Env: prod
01-22 15:02:18 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_localstore"
01-22 15:02:18 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_orm"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.common"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.welcome"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.help"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.request"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.verify"
01-22 15:02:18 [SUCCESS] nonebot_plugin_icey | Succeeded to load icey plugin model "nonebot_plugin_icey.modules.filters"
01-22 15:02:18 [SUCCESS] nonebot | Succeeded to load plugin "nonebot_plugin_icey"
01-22 15:02:18 [SUCCESS] nonebot | Running NoneBot...
01-22 15:02:18 [SUCCESS] nonebot | Loaded adapters: OneBot V11, Telegram
01-22 15:02:18 [INFO] uvicorn | Started server process [2978916]
01-22 15:02:18 [INFO] uvicorn | Waiting for application startup.
01-22 15:02:18 [INFO] nonebot_plugin_orm | No new upgrade operations detected.
01-22 15:02:18 [INFO] uvicorn | Application startup complete.
01-22 15:02:18 [INFO] uvicorn | Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)

```

### 3. Finally, enjoy your bot!


## [Usage](/.docs/Usage.md)