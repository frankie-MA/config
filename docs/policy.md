# Dotfiles Policy

- Shared behavior belongs in tracked files.
- OS-specific behavior belongs in `linux.conf`, `macos.conf`, or a small `uname` block.
- Machine-local behavior belongs in ignored local overrides:
  - `~/.config/fish/conf.d/99-local.fish`
  - `~/.config/kitty/local.conf`
  - `~/.config/nvim/lua/local.lua`
- `~/.config/nvim/lazy-lock.json` is not tracked. Each OS can resolve plugin versions locally.
- The selected Catppuccin flavour is local: `~/.config/kitty/catppuccin-current.conf`
  and `~/.config/nvim/lua/theme-flavour.lua` are ignored. When absent, both
  Kitty and Neovim use Mocha; the shared theme switcher creates these files.
- Secrets, tokens, private hostnames, and machine-only paths are not tracked.
- Finish config changes with `check-config`, then `sync-config`.

## AI-клиенты

- Публичный репозиторий хранит `.config/dotfiles-ai/`, установщики и workflow.
- Рабочие конфиги Codex/Claude/OpenCode, токены, кэш, графы и бинарники локальные.
- Новые серверы добавляются с резервной копией, существующие значения сохраняются.
- Установку и проверку выполняй по `docs/ai-environment.md`.
- Перед коммитом проверяй diff на секреты; `.gitignore` не защищает старые tracked-файлы.
- `check-config` не заменяет MCP handshake и проверку обнаружения навыков клиентом.
