+++
title = "Basic VPS Configuration"
description = "A checklist of basic settings you should apply right after spinning up a new server."
date = 2025-08-24
updated = 2025-08-24
taxonomies = { tags = ["linux", "vps", "servers"], categories = [] }

draft = false
in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

Imagine you've just spun up a new `VPS` server. Ready to use it as a reliable gateway for your home servers? The first few minutes of a server's life are the most critical from a security standpoint. Freshly created cloud servers are a favorite target for automated scanners and bots.

In this guide we'll walk step by step through the necessary and sufficient minimum of initial **Ubuntu Server** setup that will turn a "bare" system into a convenient, well-protected outpost for your services. Our goal isn't just to protect it from attacks, but also to make working with it comfortable.

## Step 0: Prerequisites

- A VPS server running Ubuntu Server 22.04 LTS or 24.04 LTS.
- Root access to the server (the login and password your hosting provider gave you, or an SSH key).
- An SSH client on your computer (the standard terminal usually works fine).

---

## Step 1: First Connection and System Update

First, let's connect to the server. If the provider gave you a root password, the command looks like this (replace your_server_ip with the actual IP address):

```bash
ssh root@your_server_ip
```

You'll get a prompt to confirm the fingerprint. Answer "yes" to trust it, then enter the password.

Right after logging in:

1. Update the package index and install updates:

   ```bash
   apt update && apt upgrade -y
   ```

   This makes sure all system components and libraries have the latest security patches.

2. Install some basic useful utilities:

   ```bash
   apt install -y curl wget nano ufw fail2ban
   ```

   · **curl**, **wget** — for downloading files from the internet.
   · **nano** — a simple text editor for beginners (you can use vim instead if you're familiar with it).
   · **ufw** — a firewall for easily managing network traffic.
   · **fail2ban** — a system for blocking brute-force attacks (password guessing).

3. Reboot the server (if the update touched the kernel):

   ```bash
   reboot
   ```

   Wait a minute, then reconnect.

---

## Step 2: Create a New User and Disable Root SSH Login

Working as `root` is bad practice. Let's create a new user with elevated privileges.

1. Create a user (replace username with your actual username):

   ```bash
   adduser username
   ```

   Set a strong password and fill in the information (you can skip this part).

2. Add the user to the sudo group: this gives them permission to run commands with root privileges.

   ```bash
   usermod -aG sudo username
   ```

3. Set up SSH keys for secure login (recommended):
   · On your computer (not on the server!), generate an SSH key pair if you don't already have one:

   ```bash
   ssh-keygen -t ed25519
   ```

   · Copy the public key to the server for your new user:

   ```bash
   ssh-copy-id username@your_server_ip
   ```

   (On Windows, without ssh-copy-id, you can copy the contents of ~/.ssh/id_ed25519.pub and manually add it to the ~/.ssh/authorized_keys file on the server.)

4. Configure the SSH daemon for better security: open the config file:

   ```bash
   nano /etc/ssh/sshd_config
   ```

   Find and change the following directives (if the lines are commented out with #, uncomment them):

   ```bash
   PermitRootLogin no          # Disable root login
   PasswordAuthentication no   # Disable password login, key-based only
   PubkeyAuthentication yes    # Allow key-based authentication
   ```

   Warning! Make sure your SSH key is copied over and working before restarting SSH! Otherwise you'll lock yourself out, and you'll have to get back in through your hosting provider's admin panel.

5. Reload the SSH service to apply the changes:

   ```bash
   systemctl reload sshd
   ```

   Now open a new terminal window and try connecting as the new user: ssh username@your_server_ip. If it works, you can close the root session.

---

## Step 3: Changing the Default SSH Port (Optional)

Changing the default SSH port isn't about real security. In this case, security comes from obscurity (security through obscurity). Changing the port doesn't remove the need for `SSH keys` and `Fail2Ban`. It's an extra, very easy-to-implement layer that significantly cuts down the noise from automated scanners.

Is it safe to leave port 22 as-is? Yes, if and only if you've already implemented:

1. A full ban on password login (PasswordAuthentication no).
2. SSH-keys-only authentication (PubkeyAuthentication yes).
3. A ban on root login (PermitRootLogin no).
4. Protection via Fail2Ban.

Under these conditions, leaving port 22 open is a perfectly safe choice. Automated bots scanning port 22 will just get their authentication attempts rejected and walk away empty-handed.

Even though it doesn't add any cryptographic strength, I still strongly recommend changing the default port. It brings some practical benefits:

1. A sharp drop in log "noise." Your `/var/log/auth.log` logs and the `Fail2Ban` ban table won't get cluttered with thousands of attempts from primitive bots that only scan port `22`. That makes log analysis easier and cuts a small but pointless load on the system.
2. It makes targeted attacks harder. An attacker deliberately going after your system will still find the `SSH port` by scanning the full port range (Nmap). But that's no longer a low-level script bot — it's a more advanced attack. You cut off `99.9%` of automated junk.

Downside:

· Convenience. You always have to specify the non-standard port when connecting: `ssh -p 12345 user@server.ip`. That said, it's easily solved by configuring the `SSH` config on your client machine.

Which port should you pick? Best practices.

The main rule: don't pick a port that's already used by another well-known service (for example, 80 — HTTP, 443 — HTTPS, 21 — FTP), to avoid future conflicts.

A good choice:

· Ports in the `1024-49151` range (registered/user ports).
· Avoid "trendy" non-standard SSH ports like `2222`, `22222`, `22225`. Those get scanned en masse too, because their popularity has made them just as obvious.
· Pick a random, unremarkable number.

Examples of good ports: `53982`, `28465`, `49123`, `13574`

Examples of bad ports: `22` (default), `2222` (obvious), `22222` (obvious), `9022` (obvious variation), `21`, `80`, `443` (conflicting).

How to change the port

1. Connect to the server and open the SSH config file:

   ```bash
   sudo nano /etc/ssh/sshd_config
   ```

2. Find the line #Port 22. Uncomment it (remove the # comment mark) and change the port number to the one you picked earlier.

   ```txt
   Port 53982   # Replace 53982 with your own port
   ```

3. Save the file and reload the SSH service.

   ```bash
   sudo systemctl reload ssh
   ```

   WARNING! Don't close your current SSH session! Make sure the new connection works first.

4. Open a new terminal window and try connecting to the server using the new port.

   ```bash
   ssh -p 53982 username@your_server_ip
   ```

   If the connection succeeds, you can close the old session.

---

## Step 4: Setting Up a Basic Firewall (`UFW`)

We'll only allow the most essential ports: `SSH` for management, and later on, a port for the network linking our local machines with the remote server.

1. Allow `SSH` connections: it's important to do this before enabling the firewall.

   ```bash
   ufw allow OpenSSH
   ```

   If you're planning to use a non-standard port for `SSH`, specify it explicitly: `ufw allow 2222/tcp` (example for port 2222).

   - If you've already changed the default SSH port, update the `UFW` firewall rules. First remove the old `OpenSSH` rule (which opened port `22`), then add the new one.

   ```bash
   sudo ufw delete allow OpenSSH  # Or just 'ufw delete allow 22/tcp'
   sudo ufw allow 53982/tcp       # Allow the new port
   sudo ufw status                # Make sure port 22 is closed and the new one is open
   ```

2. Enable the firewall:

   ```bash
   ufw enable
   ```

   Answer y. The firewall is now active and already blocking all disallowed incoming connections.

3. Check the status:

   ```bash
   ufw status verbose
   ```

   You should see that only `OpenSSH` or the new `SSH` port is allowed.

---

## Step 5: Setting Up `Fail2Ban` for Attack Protection

`Fail2Ban` will monitor `SSH` logs and automatically block `IP` addresses that try to brute-force the password.

1. Create a simple config for `SSH`: copy the default `jail` settings file:

   ```bash
   cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
   ```

   Edit it:

   ```bash
   nano /etc/fail2ban/jail.local
   ```

   In the [sshd] section, make sure the settings look like this:

   ```ini
   [sshd]
   enabled = true
   port    = ssh
   logpath = %(sshd_log)s
   backend = %(sshd_backend)s
   maxretry = 3
   bantime = 1h
   findtime = 1h
   ```

   - `maxretry` = 3: the number of failed attempts before a ban.
   - `bantime` = 1h: the ban duration (1 hour). You can set -1 for a permanent ban.
   - `findtime` = 1h: the time window in which failed attempts are counted.

2. Start and enable `Fail2Ban`:

   ```bash
   systemctl enable fail2ban --now
   ```

3. Check the status:

   ```bash
   fail2ban-client status sshd
   ```

   You'll see a list of banned `IP` addresses, if there have already been attacks.

4. (Important!) Update the `Fail2Ban` config if you've changed the default `SSH` port. `Fail2Ban` watches port `22` by default. You need to tell it to watch the new port instead.

   - Edit the `Fail2Ban` config for `SSH`:

   ```bash
   sudo nano /etc/fail2ban/jail.local
   ```

   - In the [sshd] section, find the `port` parameter and change it:

   ```ini
   [sshd]
   enabled = true
   port    = 53982    # Put your new port here!
   # ... rest of the settings (maxretry, bantime) ...
   ```

   - Restart `Fail2Ban`:

   ```bash
   sudo systemctl restart fail2ban
   ```

---

## Step 6: Timezone, Locale, and Monitoring Setup

1. Set the correct timezone:

   ```bash
   sudo timedatectl set-timezone Europe/Moscow  # Replace with your own timezone
   ```

2. Set the locale you need (system language):

   ```bash
   sudo dpkg-reconfigure locales
   ```

   Choose en_US.UTF-8 UTF-8 (recommended for servers) or ru_RU.UTF-8 UTF-8.

3. Install resource monitoring utilities:

   ```bash
   sudo apt install -y htop
   ```

   htop is a great replacement for the standard top, letting you interactively watch CPU load, RAM usage, and processes.

---

## Step 7: (Optional, but Recommended) Setting Up Backups

Your VPS is important infrastructure. Its failure shouldn't turn into a catastrophe. That's why I strongly recommend setting up backups for critical directories (/etc, /home, /root). You can use the built-in backup utilities your provider offers, or set up your own storage and ship the data to, say, S3.

---

## Step 8: Running a Security Audit

There are tools out there that can run a basic security audit of your server. For example, there's a bash script called [VPS Audit](https://github.com/vernu/vps-audit). Running it gives you a report analyzing the system. The report is saved to a separate file so you can go back and review it later.

The analysis covers not only the points we've touched on here, but also less obvious things, like whether critical packages get updated automatically, or whether a password policy rule is set up for users. Here's the list of checks it runs:

- `System Restart` — checks whether the server needs a reboot after an update
- `SSH Root Login` — checks whether root login via SSH is enabled
- `SSH Password Auth` — checks whether password-based SSH authentication is enabled
- `SSH Port` — checks the SSH port; if it's set to 22, changing it is recommended
- `Firewall Status (UFW)` — checks the status of the UFW firewall
- `Unattended Upgrades` — checks whether security packages are updated automatically
- `Intrusion Prevention` — checks for the presence of Fail2ban or CrowdSec, plus their activity status
- `Failed Logins` — checks the number of failed login attempts
- `System Updates` — checks whether all system packages are up to date
- `Running Services` — checks the number of running services; more than 16 isn't great
- `Port Security` — checks open ports; having too many isn't great either
- `Disk Usage` — checks available disk space
- `Memory Usage` — checks how much RAM is used
- `CPU Usage` — checks CPU load; high load is also worth a second look
- `Sudo Logging` — checks whether logging of sudo commands is enabled or disabled
- `Password Policy` — checks the password policy configuration
- `SUID Files` — searches for the presence of SUID files

---

## Step 9: Enabling Logging for All `sudo` Commands

To enable logging, you need to edit the `sudo` config file. To do that, just run the command

```bash
sudo visudo
```

This opens an editor with the utility's config. By default it opens in `nano`. After that, you need to add the following lines, right after the block with all the `Defaults` settings

```txt
Defaults logfile=/var/log/sudo.log
Defaults log_input,log_output
```

---

## Step 10: Setting Up Automatic Security Updates

To set up automatic security updates on most Linux distros, it's enough to install and configure `unattended-upgrades` (for Debian/Ubuntu distros) or `dnf-automatic` (for Fedora/RHEL), and enable them by configuring the services or timers themselves. You can later customize these utilities to update only security packages.

Installing and configuring for Debian/Ubuntu

1. Install the `unattended-upgrades` package

   ```bash
   sudo apt update
   sudo apt install unattended-upgrades
   ```

2. Now configure the utility

   ```bash
   sudo dpkg-reconfigure --priority=low unattended-upgrades
   ```

   A confirmation dialog will pop up where you'll need to answer `yes` to enable automatic updates.

3. Check the configuration. You can do this by running an update in `--dry-run` mode

   ```bash
   sudo unattended-upgrades --dry-run --debug
   ```

Installing and configuring for Fedora and RHEL

1. Install the `dnf-automatic` package

   ```bash
   sudo dnf install dnf-automatic
   ```

2. Configure the `dnf-automatic.conf` config file

   ```bash
   sudo nano /etc/dnf/automatic.conf
   ```

   there you need to add the following lines

   ```txt
   apply_updates = yes
   upgrade_type = security
   ```

3. Enable and start the timer

   ```bash
   sudo systemctl enable --now dnf-automatic.timer
   ```

4. And check its status

   ```bash
   systemctl status dnf-automatic.timer
   ```

Beyond that, you can also configure:

- Email alerts. On both systems you can enable alerts about what happened. To do that, edit the `/etc/apt/apt.conf.d/50unattended-upgrades` file and set an address to send messages to the sysadmin.
- Automatic reboot. You can also set this up, but be careful here — it's not a good idea to enable this in a production environment.
- You should also keep an eye on the log file after updates. For example, for `unattended-upgrades` it's located at `/var/log/unattended-upgrades`.

---

## Step 11: Setting Up a Strong Password Policy

Pluggable Authentication Modules (PAM) are installed by default on DEB-based systems (Ubuntu/Debian). However, you'll need to install an extra module, `libpam-cracklib`.

```bash
sudo apt install libpam-cracklib
```

On Debian-based systems, password policies are defined in the `/etc/pam.d/common-password` file. Before making any changes to it, it's best to back the file up.

```bash
sudo cp /etc/pam.d/common-password /etc/pam.d/common-password.bak
```

Now edit the `/etc/pam.d/common-password` file:

```bash
sudo nano /etc/pam.d/common-password
```

Find the following line and edit it; if it doesn't exist, you'll need to create it.

```txt
password required pam_cracklib.so try_first_pass retry=3 minlen=12 lcredit=1 ucredit=1 dcredit=2 ocredit=1 difok=2 reject_username
```

What each option means

- **try_first_pass retry=N** – the maximum number of retries when changing a password. N is a number. The default value is 1.
- **minlen=N** – the minimum allowed length for a new password (plus one, if credits aren't disabled, which is the default). In addition to the character count of the new password, each character type (other, uppercase, lowercase, and digit) earns a credit (+1 to length). The default value is 9.
- **lcredit=N** – sets the maximum credit for having lowercase letters in the password. The default value is 1.
- **ucredit=N** – sets the maximum credit for uppercase letters in the password. The default value is 1.
- **dcredit=N** – sets the maximum credit for digits in the password. The default value is 1.
- **ocredit=N** – sets the maximum credit for other characters in the password. The default value is 1.
- **ifok=N** – sets the number of characters that must differ from the previous password.
- **reject_username** – forbids users from using their username as their password.

Users will now need to use a password with a complexity score of 12. One "credit" is given for 1 lowercase letter, 1 credit for 1 uppercase letter, 1 credit for at least 2 digits, and 1 credit for 1 other character.

You can also disable credits by assigning them negative values, forcing the user to use a combination of different character types of a minimum length.

Let's look at an example:

```txt
password required pam_cracklib.so minlen=8 lcredit=-1 ucredit=-1 dcredit=-2 ocredit=-1 difok=2 reject_username
```

As defined above, users must use an 8-character password that includes 1 lowercase letter, 1 uppercase letter, 2 digits, and 1 other character. Note that these restrictions only apply to regular users, not to root. The root user can use any type of password.

### Checking Password Complexity

After setting the policy itself, you need to check whether it actually works. Let's assign a simple password that doesn't meet the policy and see what happens. To change or set the password for the current user, run:

```bash
$ passwd
Example output:

Changing password for myuser.
Current password:
New password:
BAD PASSWORD: it does not contain enough DIFFERENT characters
New password:
BAD PASSWORD: it is based on a dictionary word
New password:
Retype new password:
BAD PASSWORD: is too simple
New password:
BAD PASSWORD: is too simple
New password:
BAD PASSWORD: is too simple
passwd: Have exhausted maximum number of retries for service
passwd: password unchanged
```

So the user can't set the password because it doesn't meet the requirements.
