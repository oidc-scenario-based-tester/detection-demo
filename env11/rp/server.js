const express = require('express');
const session = require('express-session');
const axios = require('axios');
const crypto = require('crypto');
const qs = require('querystring');

const app = express();
const port = 9999;

const secret = crypto.randomBytes(32).toString('hex');

app.use(session({
  secret: secret,
  resave: false,
  name: "rp.session",
  saveUninitialized: true,
  cookie: { secure: false } 
}));

const clientID = 'web';
const clientSecret = 'secret';
const idpUrl = 'http://host.docker.internal:9997';
const redirectUri = `http://localhost:${port}/auth/callback`;
const idpConfigUrl = `${idpUrl}/.well-known/openid-configuration`;
let authorizationEndpoint;
let tokenEndpoint;

app.get('/login', async (req, res) => {
  // issuerパラメータ自体は検証しない
  const issuer = req.query.issuer;
  if (!issuer) {
    return res.status(400).send('Issuer parameter is required');
  }

  try {
    // IdPの設定を取得
    const idpConfigResponse = await axios.get(idpConfigUrl);
    authorizationEndpoint = idpConfigResponse.data.authorization_endpoint;
    const tokenUrl = new URL(idpConfigResponse.data.token_endpoint);
    if (tokenUrl.port === '9997') {
      tokenUrl.hostname = 'host.docker.internal';
    }    
    tokenEndpoint = tokenUrl.toString();

    const state = crypto.randomBytes(16).toString('hex');
    const url = new URL(authorizationEndpoint);
    url.searchParams.set('response_type', 'code');
    url.searchParams.set('client_id', clientID);
    url.searchParams.set('redirect_uri', redirectUri);
    url.searchParams.set('state', state);
    url.searchParams.set('scope', 'openid');

    req.session.state = state;
    req.session.tokenEndpoint = tokenEndpoint;

    console.log("/login session id:", req.session.id, req.headers.cookie);
    console.log("/login session:", req.session);

    res.redirect(url.toString());
  } catch (error) {
    console.error('Error loading IdP configuration:', error);
    res.status(500).send('Error loading IdP configuration');
  }
});

app.get('/auth/callback', async (req, res) => {
  const { code, state } = req.query;

  console.log("/callback session id:", req.session.id, req.headers.cookie);
  console.log("/callback session:", req.session);

  if (state !== req.session.state) {
    return res.status(403).send('Invalid state');
  }

  const tokenEndpoint = req.session.tokenEndpoint;

  try {
    const response = await axios.post(tokenEndpoint, qs.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: redirectUri,
      client_id: clientID,
      client_secret: clientSecret,
    }), {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    console.log(response.data);
    res.send(response.data);

  } catch (error) {
    res.status(500).send(error.toString());
  }
});

app.listen(port, () => {
  console.log(`RP is running at http://localhost:${port}`);
});
