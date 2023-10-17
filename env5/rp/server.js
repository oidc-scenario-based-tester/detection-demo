const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const qs = require('querystring');

const app = express();
const port = 3000;

const clientID = 'client';
const clientSecret = 'secret';
const idpUrl = 'http://idp:3001';
const redirectUri = `http://localhost:${port}/callback`;

app.get('/login', async(req, res) => {
  const { uid } = req.query;
  const state = crypto.randomBytes(16).toString('hex');

  try{
    const webfingerResponse = await axios.get(`${idpUrl}/.well-known/webfinger`, {
      params: {
        resource: `http://x/${uid}`,
        rel: 'http://openid.net/specs/connect/1.0/issuer'
      }
    });

    const authorizeEndpoint = webfingerResponse.data.links[0].href;

    const url = new URL(authorizeEndpoint);
    url.searchParams.set('response_type', 'code');
    url.searchParams.set('client_id', clientID);
    url.searchParams.set('redirect_uri', redirectUri);
    url.searchParams.set('state', state);
    url.searchParams.set('scope', 'openid');

    res.redirect(url.toString());
  } catch (error) {
    res.status(500).send("Error with WebFinger lookup: " + error.toString());
  }
});

app.get('/callback', async (req, res) => {
  const { code, state } = req.query;

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
