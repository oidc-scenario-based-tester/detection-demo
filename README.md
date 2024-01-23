# detection-demo
## Demo Environment
### [env1](./env1)
Environment containing vulnerability mimicking [CVE-2021-27582](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-27582).

Query parameters (including `redirect_uri`) of `/authorize` are inherited by `/consent`. Since `/authorize` performs `redirect_uri` validation, but `/consent` does not, `redirect_uri` validation can be bypassed, allowing an attacker to steal the user's authorization code.

### [env2](./env2)
Environment containing session poisoning vulnerability [Chapter two: "redirect_uri" Session Poisoning](https://portswigger.net/research/hidden-oauth-attack-vectors).

A race condition vulnerability may occur when multiple authentication requests are sent simultaneously. An attacker can use Session Poisoning to modify the user's session information and redirect the user to an untrusted client's `redirect_uri` to illegally obtain a token.

### [env3](./env3)
Environment containing LDAP injection vulnerability mimicking [CVE-2021-29156](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-29156).

An LDAP injection vulnerability exists in the WebFinger protocol. An attacker can exploit this vulnerability to steal user information.

### [env4](./env4)
Environment containing RP's XSS and IdP's authorization code consumption flaws. 

By exploiting these vulnerabilities in a chain, an attacker can steal a victim's valid authorization code.

### [env5](./env5)
Environment containing open redirect vulnerability.

Since `/authorize` don't perform `redirect_uri` validation, an attacker can steal the user's authorization code by redirecting the user to an attacker's `redirect_uri`.

### [env6](./env6)
Environment containing CSRF vulnerability.

RP does not perform CSRF protection, allowing an attacker to tie the victim's session to the attacker's one.

### [env7](./env7)
Environment containing ID spoofing vulnerability.

An attacker can modify the `iss` or `sub` of `id_token` to impersonate the victim.

### [env8](./env8)
Environment containing Wrong Recipient vulnerability.

An attacker can modify the `aud` of `id_token` to impersonate the victim.

### [env9](./env9)
Environment containing ID Token Replay vulnerability.

An attacker can replay the `id_token` to impersonate the victim.

## References
- https://portswigger.net/research/hidden-oauth-attack-vectors
- https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-27582
- https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-29156
