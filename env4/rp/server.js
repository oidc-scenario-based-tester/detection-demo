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

app.get('/login', (req, res) => {
  const state = crypto.randomBytes(16).toString('hex');
  const url = new URL(`http://localhost:3001/authorize`);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('client_id', clientID);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('state', state);
  url.searchParams.set('scope', 'openid');
  
  res.redirect(url.toString());
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
    
    res.send(`<html>
                <body>
                    <div>State: ${state}</div>
                    <div>Response Data: <pre>${JSON.stringify(response.data, null, 2)}</pre></div>
                </body>
              </html>`);
  } catch (error) {
    res.status(500).send(error.toString());
  }
});

app.listen(port, () => {
  console.log(`RP is running at http://localhost:${port}`);
});
