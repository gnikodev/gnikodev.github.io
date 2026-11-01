+++
title = "Getting certificates in k3s (k8s) via cert-manager"
description = "A way to automate certificate issuance for a local network using cert-manager and the DNS01 challenge."
date = 2025-02-12
updated = 2025-02-12
taxonomies = { tags = ["kubernetes", "k3s", "k8s", "certmanager", "letsencrypt"], categories = [] }

draft = false
in_search_index = true

[extra]
# badge = "NEW"  # Options: NEW, BETA, UPDATED, WIP
+++

Having SSL certificates these days is an essential part of securing any deployed resource. When I started organizing my server and spun up a k3s cluster, I immediately started thinking about how to provide my web services with valid certificates.

Let me give a brief historical overview of what SSL certificates are, why they're needed, and what trusted certificate authorities are. It'll come in handy later.

## SSL certificates and HTTPS connections

**An SSL certificate** is a digital document that confirms the authenticity of a web resource and encrypts data transmitted between client and server. It confirms that the client is talking to the site it claims to be, and not to a fake one. Compromising a certificate is fairly hard: in the simplest case, you'd need to break into the server side of the resource and steal the private part of the key.

**SSL (Secure Sockets Layer)** is a technology that provides a secure connection. These days the abbreviation TLS (Transport Layer Security) is used more often. This protocol protects the information a user sends to or receives from a server — for example, logins, passwords, bank card data. Without encryption, plain HTTP traffic is very easy to intercept and read the contents of.

**HTTPS (HyperText Transfer Protocol Secure)** is the secured version of the HTTP protocol, using certificates and SSL/TLS technologies to encrypt data.

## Trusted certificate authorities (CA)

Certificate authorities (CAs) are organizations that issue SSL certificates. Their job is to verify that whoever requested the certificate actually owns the domain it's being requested for, and to confirm their identity. In other words, these organizations act as a kind of guarantor of the link between a domain and its owner, and issue a signed document — the certificate — to confirm it. Here's a list of well-known certificate authorities:

- Let's Encrypt (the one used in this article)
- DigiCert
- Comodo
- GlobalSign

How the data exchange works:

1. **The client (browser)** requests a connection to the server (for example, when navigating to a site).
2. **The server** sends the client its SSL certificate.
3. **The client** verifies the certificate (it can check it itself or contact the CA that issued it):
   - Is the certificate authority trusted?
   - Has the certificate expired?
   - Does the certificate's domain name match the requested site?
4. If the check passes, **the client and server** establish a secure connection using encryption (for example, via RSA or ECDHE algorithms).
5. After that, data is transmitted encrypted. For example, if you enter a password on a site, it will be encrypted and only decrypted on the server.

## How to get an SSL certificate

There are several ways to get a certificate. Let's briefly go over them.

### Creating self-signed certificates

This is fairly easy to do with the `openssl` utility (Linux). Using just a few commands, we get two files: the certificate itself and the key. These can already be attached to a web server. I don't see much point in describing the whole issuance process here, since there are plenty of articles about it, for example [this one](https://habr.com/ru/articles/352722/).

The downsides of this approach:

- You'll have to add the certificate to every browser on every device, because you'll be the CA, and the rest of the world has no idea that some random person calling themselves a trusted certificate authority exists. So when visiting such a site, the browser will complain that it can't verify the certificate authority.
- You have to track the certificate's validity and lifetime yourself. You can set a calendar reminder, but I've often seen situations in large companies where they forgot to reissue certificates in time and work ground to a halt for half a day.

### Using the `certbot` utility

This utility lets you automatically obtain a **Let's Encrypt** certificate for a given domain. You can get certificates either for specific domains or via the wildcard scheme (where a single certificate covers all possible subdomains). For example, if you request an SSL certificate for `example.com`, it'll only be valid for that domain, but if you request a wildcard `*.example.com`, it can be used for `one.example.com`, `two.example.com`, and even `one.two.example.com`.

The process of getting a certificate is fairly simple. You need to install the utility, then run the `certbot certonly {...params...}` command. For more details on the process, you can read [this article](https://habr.com/ru/articles/270273/).

Worth mentioning are the two ways of obtaining a certificate (ACME challenges):

- **HTTP01 challenge** — a process where, on the host running the utility, an endpoint `{requested_domain}/.well-known/acme-challenge/{ID}` is created, which points to the contents of a file created by `certbot` that holds the secret key. `certbot` sends a callback request to Let's Encrypt. In turn, Let's Encrypt has to call our domain at the given address to fetch and verify the secret key. If the check succeeds, the issued certificate and key are sent back. This requires the service the certificate is being issued for to be reachable from the public internet. Alternatively, you can create a "stub service" that isn't a real service but simply serves the secret key data at the given path. By the way, the article mentioned above describes how to set up such a "stub service."
- **DNS01 challenge** — in this case, the service the certificate is being requested for doesn't need to be reachable from the public internet. But you do need access to the PublicAPI of the registrar where the domain was purchased. For this request, you have to provide a login, password, or API key for the PublicAPI so that `certbot` can create a TXT record for the requested domain. After that, Let's Encrypt looks up that domain to read the key from the created TXT record. Once verified, we again get a certificate and a secret key.

Using `certbot` can solve a huge number of problems, but there are still downsides:

- You still have to track the certificate's lifetime yourself. Starting in January 2025, Let's Encrypt shut down its expiration-notification email service, since it had become too expensive for them to run.
- You still need to manually request new certificates every time. Sure, you could automate this with other tools, but our goal is to integrate this into the k3s cluster so that everything works "out of the box." Yes, I'm lazy.

### Using the `cert-manager` service

And now we've arrived at the solution I actually use in my cluster. The `cert-manager` service takes care of the whole job of issuing, tracking, renewing, and attaching certificates. All you need to do is configure the issuance process and simply mark new services' Ingress resources to use a TLS connection. `cert-manager` will notice the creation of a new Ingress with TLS, immediately obtain a valid certificate, and attach it to the service.

Let's walk through the installation and setup process. First you need a k3s or k8s cluster (or any other Kubernetes). You also need the `helm` utility installed to manage Helm charts.

For convenience, I created a folder `/home/ms/helms` on the cluster machine, where I keep all the `values.yaml` files and other Helm chart settings. Let's go into that folder and start running commands:

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm pull jetstack/cert-manager
```

The commands above add the `jetstack` repository, which contains the chart we need. Then we download the `cert-manager` chart with the `pull` command.

Let's check that the archive was downloaded and unpack it. Pay attention to the chart version — at the time of writing this article, it's version `1.16.3`.

```bash
ls -la
tar zxf cert-manager-v1.16.3.tgz
rm cert-manager-v1.16.3.tgz
cp cert-manager/values.yaml cert-manager-values.yaml
```

I used the DNS01 challenge to get certificates, since the Kubernetes cluster sits on my local network and the services aren't exposed to the public internet. I didn't want to bother with a separate "stub service" to make HTTP01 work. Going through DNS seemed simpler to me. But I ran into a problem where, when requesting a certificate, `cert-manager` would hang forever with the error:

```
DNS record for xxx not yet propagated
```

I spent about three days trying to solve this problem, until I found a GitHub Issue with the fix. [Link to the Issue](https://github.com/cert-manager/cert-manager/issues/5042) and another [link with the solution](https://github.com/cert-manager/cert-manager/issues/5515#issuecomment-1479054700).

You need to edit the `values.yaml` file, find the following lines, and change them like this:

```yaml
crds:
  enabled: true

extraArgs:
  - --enable-certificate-owner-ref=true
  - --dns01-recursive-nameservers-only
  - --dns01-recursive-nameservers=8.8.8.8:53,1.1.1.1:53

prometheus:
  enabled: true
  servicemonitor:
    enabled: true
```

Now let's install the `cert-manager` service itself into the cluster:

```bash
helm upgrade --install cert-manager -f cert-manager-values.yaml cert-manager/
```

To use the DNS challenge, we need to obtain an API key from the provider where the domain was purchased. The setup is similar across many foreign providers, but I use reg.ru. There's no built-in webhook implementation for `cert-manager` for it. So we'll use another [service](https://github.com/flant/cert-manager-webhook-regru). This repository contains a webhook implementation for using the DNS challenge via reg.ru. The repo's README has usage instructions — you can follow all of it except for the part about creating the certificate file. I prefer to use a wildcard certificate rather than issuing a separate one for every domain.

Now we need to configure the `ClusterIssuer` object, which controls the certificate issuance settings. For this, let's create a separate folder `/home/ms/ci` and, inside it, a file `cert-manager-issuer.yml`:

```yaml
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod-issuer
spec:
  acme:
    email: <YOUR_EMAIL>
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: <SUPER_SECRET_KEY>
    solvers:
      - dns01:
          webhook:
            config:
              # here you can put settings for a different webhook provider.
              regruPasswordSecretRef:
                name: regru-password
                key: REGRU_PASSWORD
            # groupName must match `groupName.name` in the `values.yaml` file.
            groupName: acme.regru.ru
            solverName: regru-dns
---
```

An example DNS01 `solver` for Cloudflare:

```yaml
- dns01:
  cloudflare:
    email: xxx
    apiTokenSecretRef:
      name: cloudflare-token-secret
      key: cloudflare-token
```

If you don't want to bother with getting a certificate via the DNS challenge, you can use the HTTP challenge instead. For that, add the following to the `solvers` section:

```yaml
- http01:
    # The ingressClass used to create the necessary ingress routes
    ingress:
      serviceType: ClusterIP
      ingressClassName: traefik
```

But keep in mind that for this method to work, the domain needs to be reachable from the outside network. Or you'll need a separate service that can prove ownership of the resource.

Apply the settings with:

```bash
kubectl apply -f cert-manager-issuer.yml
```

Now let's configure the Ingress file, using the Portainer service as an example. It's convenient to keep the Ingress YAML files in a separate folder, for example `/home/ms/ingress`. Traefik is used as the reverse proxy here, since it's installed by default when deploying k3s.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: portainer-ingress
  namespace: default
  labels:
    app: portainer
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    # specify the name of the ClusterIssuer created earlier
    cert-manager.io/cluster-issuer: letsencrypt-prod-issuer
spec:
  rules:
    - host: portainer.EXAMPLE.COM
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: portainer
                port:
                  number: 9000
  ingressClassName: traefik
  tls:
    - hosts:
        - portainer.EXAMPLE.COM
      secretName: portainer-ssl
```

Apply the Ingress settings:

```bash
kubectl apply -f portainer-ingress.yml
```

And the cherry on top: a file that redirects all HTTP requests hitting the ingress to HTTPS. For this, let's create a `middleware` file in the `home/ms/middlewares` folder named `traefik-https-redirect-middleware.yaml`. Fill it in with the following:

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: redirect-https
spec:
  redirectScheme:
    scheme: https
    permanent: true
```

And apply the configuration:

```bash
kubectl apply -f traefik-https-redirect-middleware.yaml
```

That's it. Once the Ingress settings are applied, `cert-manager` will automatically detect them and start the process of issuing a certificate for the domain listed in the Ingress file's `tls.hosts` section.
