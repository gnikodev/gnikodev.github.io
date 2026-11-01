+++
title = "ChatGPT without registration or SMS."
description = "A way to work with AI without \"extra\" apps."
date = 2025-02-04
updated = 2025-02-04
taxonomies = { tags = ["networks", "chatgpt","dns"], categories = [] }

draft = false
in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

In an era of rapid tech progress, it's frustrating when you can't get access to some new program or service you've really been wanting to try.

That's the case with ChatGPT. Requests from certain IP addresses are blocked from using the service. Sure, there are plenty of ways around it using third-party tunnels, or you can spin up your own. But the service has learned to detect provider IP ranges and block access again.

There's another approach that can also help solve the problem: using alternative DNS servers. For example, the ones provided by [comss](https://www.comss.ru/page.php?id=7315). This DNS server returns the address of its own proxy server instead of the service's real IP address. On top of that, you also get ad blocking on other sites — roughly the same way you would with AdGuard's DNS servers.

This approach, of course, doesn't come with a 100% guarantee. But as of this writing, it works. By the way, besides ChatGPT access, it also unlocks Sora, Microsoft Copilot, GitHub Copilot, Google Gemini and Google ImageFX, Claude AI...

Setting up your device to talk to the new servers is very easy, and there are a few ways to do it.

## Setting DNS records globally (e.g. on your router)

For this you need access to your router's admin panel. You can usually reach it at 192.168.0.1 or 192.168.1.1. Or check the back of your device — it usually has the address plus the login and password for the admin panel printed on it.

I won't describe how to change the DNS on every single router model — you can find that online. I'll just leave links to guides for the most popular ones.

- [tp-link](https://www.tp-link.com/ru/support/faq/1712/)
- [d-link](https://www.dlink.ru/by/faq/391/1037.html)
- [keenetic](https://help.keenetic.com/hc/ru/articles/213966649-%D0%98%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D1%87%D0%BD%D1%8B%D1%85-DNS-%D1%81%D0%B5%D1%80%D0%B2%D0%B5%D1%80%D0%BE%D0%B2)

### Pros

- Every device gets access right away, no need to configure each one manually.

### Cons

- There's a chance some other sites will become unreachable.
- There's a chance of slower speeds, since these servers may not handle the load well.
- In general, using third-party DNS servers carries some risk, since the provider could be attacked and records swapped to redirect you to phishing sites 🧐.

## Configuring each device individually

I think the title makes this one self-explanatory. I'll leave a few links here too.

- [Windows](https://remontka.pro/change-dns-server-windows/)
- [Mac](https://support.apple.com/ru-ru/guide/mac-help/mh141272/mac)

On mobile devices, you can change this in your network or Wi-Fi settings by turning off automatic DNS. On Android there are dedicated apps for this — comss covers them [here](https://www.comss.ru/page.php?id=7120) and [here](https://www.comss.ru/page.php?id=7316).

## Getting a specific address

To do this, we need to open the [comss](https://www.comss.ru/page.php?id=7315) site, find the DNS server's IP address (currently `83.220.169.155`), and then run the following command in the terminal:

```bash
nslookup chatgpt.com 83.220.169.155
```

We get back:

```bash
Server:         83.220.169.155
Address:        83.220.169.155#53

Non-authoritative answer:
Name:   chatgpt.com
Address: 94.131.119.85
Name:   chatgpt.com
Address: 2a11:3c00:0:1e::1
```

The `Address` line contains the address of the proxy server that requests to ChatGPT get routed through. Now we need to add this value to the `hosts` file. How to edit that file and add domain-name-to-IP mappings is described in the articles below — there's a separate one for each OS:

- [Setting up the hosts file on Linux](https://help.reg.ru/support/dns-servery-i-nastroyka-zony/rabota-s-dns-serverami/fayl-hosts-na-linux#0)
- [Setting up the hosts file on Windows](https://help.reg.ru/support/dns-servery-i-nastroyka-zony/rabota-s-dns-serverami/fayl-hosts-dlya-windows-10)
- [Setting up the hosts file on macOS](https://help.reg.ru/support/dns-servery-i-nastroyka-zony/rabota-s-dns-serverami/fayl-hosts-na-macos)

We need to add the following lines to that file:

```txt
94.131.119.85 chatgpt.com
94.131.119.85 auth.openai.com
94.131.119.85 chat.openai.com
```

For every domain we might hit while working with ChatGPT, we set it to the proxy server address we got in the `Address` field.

Now only traffic headed to ChatGPT's servers will go through the separate proxy.
