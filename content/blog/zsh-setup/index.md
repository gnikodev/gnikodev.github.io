+++
title = "Моя настройка оболочки ZSH."
description = "Если вам не нравится стандартная оболочка командной строки типа bash и sh, то нужно ставить ZSH, расскажу как его установить и настроить."
date = 2025-09-02
updated = 2025-09-02
taxonomies = { tags = ["linux", "zsh","oh-my-zsh"], categories = [] }

# draft = false
# in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

Если тебе надоел стандартный вид оболочки командной строки, и хочется увеличить свою продуктивность при работе в консоли, то эта статья для тебя! Мы рассмотрим как установить и настроить продвинутую оболочку zsh, а так же поставим несколько удобных плагинов.

## Этап 1: Установка Zsh (если он еще не установлен)

**На macOS:**
Начиная с Catalina, Zsh является оболочкой по умолчанию. Проверь текущую версию:

```bash
zsh --version
```

Если нужно обновить или установить: `brew install zsh`

**На Ubuntu/Debian:**

```bash
sudo apt update -y && sudo apt install zsh -y
```

После установки сделай Zsh оболочкой по умолчанию:

```bash
chsh -s $(which zsh)
```

(Нужно перезапустить терминал, чтобы изменения вступили в силу).

---

## Этап 2: Установка Oh My Zsh

Oh My Zsh — это фреймворк для управления конфигурацией Zsh. Установка очень проста:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Или через wget:

```bash
sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

---

### Этап 3: Выбор и настройка темы (Самая лучшая и интересная)

Здесь субъективный выбор, но хит среди сообщества и мой личный фаворит — **Powerlevel10k**.

**Почему мне нравится Powerlevel10k (p10k)?**

- Невероятно быстрая (самая быстрая из "powerline"-тем).
- Неограниченная кастомизация через встроенный мастер настройки.
- Показывает кучу полезной информации: статус Git, версия Python/Node.js, время выполнения команды, уровень заряда батареи и многое другое.
- Имеет встроенные "пресеты" для красивого вида.

**Установка Powerlevel10k:**

1. Клонируем репозиторий темы в каталог Oh My Zsh:

   ```bash
   git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
   ```

2. Открой файл конфигурации `~/.zshrc` в текстовом редакторе (например, `nano ~/.zshrc`).

3. Находим строчку `ZSH_THEME="robbyrussell"` и меняем её на:

   ```bash
   ZSH_THEME="powerlevel10k/powerlevel10k"
   ```

4. Сохрани файл и перезагружаем Zsh:

   ```bash
   source ~/.zshrc
   ```

5. **После перезагрузки запустится автоматический мастер настройки (wizard) Powerlevel10k.** Он задаст тебе несколько вопросов о предпочтениях в стиле и покажет предпросмотр. Следуй его инструкциям — это самый простой способ получить идеальную тему! Если wizard не запустился, вызовите его вручную: `p10k configure`.

---

## Этап 4: Установка самых нужных плагинов для продуктивности

Плагины — это суперсила Oh My Zsh. Вот ТОП-5 Must-Have плагинов:

1. **zsh-autosuggestions**: Подсказывает команды по истории. Просто жмите `→` или `Ctrl+F` чтобы принять подсказку.

   - Установка:

     ```bash
     git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
     ```

2. **zsh-syntax-highlighting**: Подсвечивает команды: корректные — зеленым, неверные — красным. Невероятно удобно.

   - Установка:

     ```bash
     git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
     ```

3. **web-search**: Позволяет искать прямо из консоли. Примеры:

   - `google как настроить zsh`
   - `ddg что такое docker`
   - `github ohmyzsh`
   - (Уже входит в стандартный набор Oh My Zsh, его просто добавить в список плагинов).

4. **git**: Огромная коллекция алиасов для Git. Например:

   - `gst` вместо `git status`
   - `gaa` вместо `git add --all`
   - `gcmsg "commit"` вместо `git commit -m "commit"`
   - `gl` / `gp` вместо `git pull` / `git push`
   - (Уже входит в стандартный набор, точно так же достаточно добавить в список плагинов).

5. **sudo**: Дважды нажмите `ESC`, чтобы автоматически добавить `sudo` в начало текущей команды. Очень экономит время.

**Как подключить плагины:**
Снова открой `~/.zshrc`. Найди строку:

```bash
plugins=(git)
```

И замени её на список всех нужных плагинов (**важно:** `zsh-syntax-highlighting` должен быть последним!).

```bash
plugins=(
    git
    web-search
    sudo
    zsh-autosuggestions
    zsh-syntax-highlighting
)
```

Сохрани файл и примени изменения:

```bash
source ~/.zshrc
```

---

## Этап 5: Дополнительные "прокачки" (Опционально, но очень круто)

### 1. Установка Nerdfonts

Для корректного отображения иконок и спецсимволов в Powerlevel10k **обязательно** нужен Nerd Font.

- Скачай любой понравившийся шрифт (например, **Meslo Nerd Font**, **FiraCode Nerd Font**, **Hack Nerd Font**) с [сайта](https://www.nerdfonts.com/font-downloads).
- Установи его в систему.
- **В настройках твоего терминала (iTerm2, Windows Terminal, GNOME Terminal и т.д.) смени шрифт на установленный Nerd Font.** Это критически важный шаг!

### 2. Настройка алиасов в `~/.zshrc`

Добавь в конец файла `~/.zshrc` свои собственные алиасы для частоиспользуемых команд:

```bash
# My Custom Aliases
alias update='sudo apt update && sudo apt upgrade -y' # Для Ubuntu/Debian
alias cls='clear'
alias zshconfig='nano ~/.zshrc'
alias ohmyzsh='nano ~/.oh-my-zsh'
alias ..='cd ..'
alias ...='cd ../..'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
```

Я еще дополнительно добавлял алиасы для работы с kubectl, но далеко не все пользуются этой утилитой, поэтому пример приведу в другой статье.

### 3. Установка цветной команды `ls`

- **На macOS:** `brew install coreutils` и добавь алиас `alias ls='gls --color=auto'`.
- **На Linux:** обычно уже установлено. Убедитесь, что в `~/.zshrc` есть строка: `export LS_COLORS="di=1;36:ln=35:so=32:pi=33:ex=31:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43"` (или похожая).

---

## Этап 6. Если не хочется делать это все руками

Если не хочется выполнять все действия руками, то есть возможность просто запустить 1 скрипт, и все настройки будут применены.

Для этого можно посетить [этот репозиторий](https://github.com/ni-gushch/zsh-setup), стянуть скрипт, и начать установку. Для этого можно сделать.

- Скачай скрипт из источника

  ```bash
  curl -O https://raw.githubusercontent.com/ni-gushch/zsh-setup/master/zsh_setup.sh
  ```

- Сделай его исполняемым:

  ```bash
  chmod +x zsh_setup.sh
  ```

- Запусти:

  ```bash
  sudo ./zsh_setup.sh
  ```

---

### Итог

После всех этих шагов ты получаешь:

1. **Невероятно красивую и информативную тему** (Powerlevel10k).
2. **Умные подсказки команд** на лету (autosuggestions).
3. **Подсветку синтаксиса** для избежания ошибок (syntax-highlighting).
4. **Множество удобных сокращений** для Git и не только.
5. **Возможность быстрого поиска** из консоли.

Финальный шаг — перезагрузи терминал или выполни `source ~/.zshrc` и наслаждайся своей новой, невероятно продуктивной консолью.
