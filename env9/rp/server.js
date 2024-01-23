const express = require('express');
const session = require('express-session');
const axios = require('axios');
const crypto = require('crypto');
const qs = require('querystring');

const app = express();
const port = 3000;

const secret = crypto.randomBytes(32).toString('hex');

app.use(express.json());
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
  const nonce = crypto.randomBytes(16).toString('hex');
  const url = new URL(`http://localhost:3001/authorize`);
  url.searchParams.set('response_type', 'id_token');
  url.searchParams.set('client_id', clientID);
  url.searchParams.set('redirect_uri', redirectUri);
  url.searchParams.set('state', state);
  url.searchParams.set('nonce', nonce);
  url.searchParams.set('scope', 'openid');

  req.session.state = state;
  req.session.nonce = nonce;
  
  // TODO: /callbackで参照できないので修正
  req.session.save(function (err) {
    if (err) return next(err)
    res.redirect(url.toString());
  })
});

app.get('/callback', (req, res) => {
  if (req.query.state !== req.session.state) {
      return res.status(403).send('Invalid state');
  }

  res.send(`
      <html>
          <body>
              <div id="response"></div> <!-- Placeholder for the response message -->
              <script>
                  function parseHash() {
                      const hash = window.location.hash.substring(1);
                      const params = new URLSearchParams(hash);
                      const idToken = params.get('id_token');
                      if (idToken) {
                          // Send the ID Token to the /login endpoint
                          fetch('/login', {
                              method: 'POST',
                              headers: {
                                  'Content-Type': 'application/json'
                              },
                              body: JSON.stringify({ id_token: idToken })
                          })
                          .then(response => response.json())
                          .then(data => {
                              // Handle the response data, e.g., display a message or redirect
                              if (data.message && data.message === 'Login successful') {
                                  document.getElementById('response').innerHTML = '<p>Success: ' + data.message + '</p>';
                              } else {
                                  document.getElementById('response').innerHTML = '<p>Error: Login failed</p>';
                              }
                          })
                          .catch(error => {
                              console.error('Error:', error);
                              document.getElementById('response').innerHTML = '<p>Error: ' + error.toString() + '</p>';
                          });
                      }
                  }
                  window.onload = parseHash;
              </script>
          </body>
      </html>
  `);
});

app.post('/login', async (req, res) => {
  const { id_token } = req.body;

  try {
    // Decode and validate the ID Token
    const decoded = JSON.parse(Buffer.from(id_token.split('.')[1], 'base64').toString());
    console.log(decoded);

    // Validate issuer
    if (decoded.iss !== 'http://localhost:3001') {
      res.status(403).send({'message': 'Invalid issuer'});
      return;
    }

    // Validate audience
    if (decoded.aud !== clientID) {
      res.status(403).send({'message': 'Invalid audience'});
      return;
    }

    // Validate nonce
    // console.log(decoded.nonce, req.session.nonce);
    // if (decoded.nonce !== req.session.nonce) {
    //   res.status(403).send({'message': 'Invalid nonce'});
    //   return;
    // }
    
    // ID Token is valid, handle it according to your application's needs
    res.send({ message: 'Login successful', user: decoded.sub });
  } catch (error) {
    res.status(500).send(error.toString());
  }
});

app.listen(port, () => {
  console.log(`RP is running at http://localhost:${port}`);
});
