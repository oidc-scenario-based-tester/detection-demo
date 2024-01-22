const express = require('express');
const session = require('express-session');
const axios = require('axios');
const crypto = require('crypto');
const qs = require('querystring');

const app = express();
const port = 3000;

const secret = crypto.randomBytes(32).toString('hex');

app.use(session({
  secret: secret,
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } 
}));

const clientID = 'client';
const clientSecret = 'secret';
const idpUrl = 'http://idp:3001';
const redirectUri = `http://localhost:${port}/callback`;

app.get('/login', (req, res) => {
  const state = crypto.randomBytes(16).toString('hex');
  const url = new URL(`http://localhost:3001/authorize`);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('client_id', clientID);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('state', state);
  url.searchParams.set('scope', 'openid');

  req.session.state = state;
  
  res.redirect(url.toString());
});

app.get('/callback', async (req, res) => {
  const { code, state } = req.query;

  if (state !== req.session.state) {
    return res.status(403).send('Invalid state');
  }

  try {
    const response = await axios.post(`${idpUrl}/token`, qs.stringify({
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
    
    res.send(response.data);
  } catch (error) {
    res.status(500).send(error.toString());
  }
});

app.listen(port, () => {
  console.log(`RP is running at http://localhost:${port}`);
});
