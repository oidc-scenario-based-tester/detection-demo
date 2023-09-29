# detection-demo
## Demo Environment
### [env1](./env)
Environment containing vulnerability mimicking [CVE-2021-27582](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-27582)

Query parameters (including `redirect_uri`) of `/authorize` are inherited by `/consent`. Since `/authorize` performs `redirect_uri` validation, but `/consent` does not, `redirect_uri` validation can be bypassed, allowing an attacker to steal the user's authorization code.

## References
- https://portswigger.net/research/hidden-oauth-attack-vectors
- https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-27582