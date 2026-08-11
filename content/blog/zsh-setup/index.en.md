+++
title = "My ZSH shell setup."
description = "If you're not a fan of the standard command-line shell like bash or sh, you should switch to ZSH — I'll show you how to install and configure it."
date = 2025-09-02
updated = 2025-09-02
taxonomies = { tags = ["linux", "zsh","oh-my-zsh"], categories = [] }

# draft = false
# in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

If you're tired of the standard look of your command-line shell and want to boost your productivity while working in the console, this article is for you! We'll go over how to install and configure the advanced zsh shell, and set up a few handy plugins along the way.

## Stage 1: Installing Zsh (if it's not installed yet)

**On macOS:**
Starting with Catalina, Zsh is the default shell. Check your current version:

```bash
zsh --version
```

If you need to update or install it: `brew install zsh`

**On Ubuntu/Debian:**

```bash
sudo apt update -y && sudo apt install zsh -y
```

After installing, make Zsh your default shell:

```bash
chsh -s $(which zsh)
```

(You'll need to restart your terminal for the changes to take effect.)

---

## Stage 2: Installing Oh My Zsh

Oh My Zsh is a framework for managing your Zsh configuration. Installing it is very simple:

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Or via wget:

```bash
sh -c "$(wget -O- https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

---

### Stage 3: Choosing and setting up a theme (the best and most interesting part)

This choice is subjective, but the community favorite — and my personal pick — is **Powerlevel10k**.

**Why do I like Powerlevel10k (p10k)?**

- Incredibly fast (the fastest of the "powerline" themes).
- Unlimited customization through a built-in configuration wizard.
- Shows a ton of useful info: Git status, Python/Node.js version, command execution time, battery level, and much more.
- Comes with built-in "presets" for a good-looking layout.

**Installing Powerlevel10k:**

1. Clone the theme repository into the Oh My Zsh directory:

   ```bash
   git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
   ```

2. Open the `~/.zshrc` config file in a text editor (for example, `nano ~/.zshrc`).

3. Find the line `ZSH_THEME="robbyrussell"` and change it to:

   ```bash
   ZSH_THEME="powerlevel10k/powerlevel10k"
   ```

4. Save the file and reload Zsh:

   ```bash
   source ~/.zshrc
   ```

5. **After reloading, the automatic Powerlevel10k configuration wizard will launch.** It'll ask you a few questions about your style preferences and show you a preview. Just follow the prompts — it's the easiest way to get the perfect theme! If the wizard doesn't start automatically, you can run it manually: `p10k configure`.

---

## Stage 4: Installing the most essential productivity plugins

Plugins are Oh My Zsh's superpower. Here's the TOP 5 must-have plugins:

1. **zsh-autosuggestions**: Suggests commands based on your history. Just press `→` or `Ctrl+F` to accept the suggestion.

   - Installation:

     ```bash
     git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
     ```

2. **zsh-syntax-highlighting**: Highlights commands — correct ones in green, invalid ones in red. Incredibly convenient.

   - Installation:

     ```bash
     git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
     ```

3. **web-search**: Lets you search right from the console. Examples:

   - `google how to set up zsh`
   - `ddg what is docker`
   - `github ohmyzsh`
   - (Already included in the standard Oh My Zsh set — you just need to add it to the plugin list.)

4. **git**: A huge collection of Git aliases. For example:

   - `gst` instead of `git status`
   - `gaa` instead of `git add --all`
   - `gcmsg "commit"` instead of `git commit -m "commit"`
   - `gl` / `gp` instead of `git pull` / `git push`
   - (Also already included in the standard set — again, just add it to the plugin list.)

5. **sudo**: Press `ESC` twice to automatically prepend `sudo` to the current command. A real time-saver.

**How to enable plugins:**
Open `~/.zshrc` again. Find the line:

```bash
plugins=(git)
```

And replace it with a list of all the plugins you need (**important:** `zsh-syntax-highlighting` must be last!).

```bash
plugins=(
    git
    web-search
    sudo
    zsh-autosuggestions
    zsh-syntax-highlighting
)
```

Save the file and apply the changes:

```bash
source ~/.zshrc
```

---

## Stage 5: Extra upgrades (optional, but pretty cool)

### 1. Installing Nerd Fonts

For icons and special characters to display correctly in Powerlevel10k, you **absolutely** need a Nerd Font.

- Download any Nerd Font you like (for example, **Meslo Nerd Font**, **FiraCode Nerd Font**, **Hack Nerd Font**) from the [website](https://www.nerdfonts.com/font-downloads).
- Install it on your system.
- **In your terminal's settings (iTerm2, Windows Terminal, GNOME Terminal, etc.), switch the font to the Nerd Font you just installed.** This is a critical step!

### 2. Setting up aliases in `~/.zshrc`

Add your own aliases for frequently used commands to the end of your `~/.zshrc` file:

```bash
# My Custom Aliases
alias update='sudo apt update && sudo apt upgrade -y' # For Ubuntu/Debian
alias cls='clear'
alias zshconfig='nano ~/.zshrc'
alias ohmyzsh='nano ~/.oh-my-zsh'
alias ..='cd ..'
alias ...='cd ../..'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
```

I also added a bunch of aliases for working with kubectl, but not everyone uses that tool, so I'll give an example of those in a separate article.

### 3. Setting up colored `ls` output

- **On macOS:** `brew install coreutils` and add the alias `alias ls='gls --color=auto'`.
- **On Linux:** it's usually already set up. Make sure your `~/.zshrc` has a line like: `export LS_COLORS="di=1;36:ln=35:so=32:pi=33:ex=31:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43"` (or something similar).

---

## Stage 6. If you don't feel like doing all this by hand

If you don't want to go through all these steps manually, you can just run a single script and have all the settings applied for you.

To do that, check out [this repository](https://github.com/ni-gushch/zsh-setup), grab the script, and start the installation. Here's how:

- Download the script from the source

  ```bash
  curl -O https://raw.githubusercontent.com/ni-gushch/zsh-setup/master/zsh_setup.sh
  ```

- Make it executable:

  ```bash
  chmod +x zsh_setup.sh
  ```

- Run it:

  ```bash
  sudo ./zsh_setup.sh
  ```

---

### Summary

After all these steps, you end up with:

1. **An incredibly good-looking and informative theme** (Powerlevel10k).
2. **Smart command suggestions** on the fly (autosuggestions).
3. **Syntax highlighting** to help avoid mistakes (syntax-highlighting).
4. **A ton of handy shortcuts** for Git and more.
5. **Quick search** right from the console.

The final step — restart your terminal or run `source ~/.zshrc` and enjoy your new, incredibly productive shell.
