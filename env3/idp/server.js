const express = require('express');
const crypto = require('crypto');
const session = require('express-session');
const { v4: uuidv4 } = require('uuid');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const ldap = require('ldapjs');

const app = express();
const port = 3001;

const secret = crypto.randomBytes(32).toString('hex');

const LDAP_BIND_DN = "cn=admin,dc=example,dc=com";
const LDAP_BIND_PASSWORD = "password";

const ldapClient = ldap.createClient({
  url: 'ldap://ldap:389'
});

ldapClient.bind(LDAP_BIND_DN, LDAP_BIND_PASSWORD, err => {
  if (err) {
    console.error("Error binding to LDAP:", err);
  } else {
    console.log("Successfully bound to LDAP");
  }
});

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: secret,
  resave: false,
  saveUninitialized: true,
  cookie: { secure: false } 
}));

const clients = {
  'client': {
    secret: 'secret',
    redirectUris: ['http://localhost:3000/callback'],
  },
};

const users = {};
const codes = {};

// 初期ユーザーを追加
async function addInitialUser() {
  const userId = 'testuser1';
  const password = 'password1';
  const hashedPassword = await bcrypt.hash(password, 10);
  users[userId] = { userId, password: hashedPassword };
}

// 初期ユーザーを追加するための関数呼び出し
addInitialUser();

const FILTER_PATTERN_ORG = "(&(objectclass=inetOrgPerson)(uid={0}))";
app.get('/.well-known/webfinger', (req, res) => {
  const { resource, rel } = req.query;

  if (rel !== 'http://openid.net/specs/connect/1.0/issuer') {
    return res.status(400).send('Invalid rel parameter');
  }

  // エスケープ処理をせずに直接LDAPフィルタに挿入
  // /.well-known/webfinger?resource=http://x/t*&rel=http://openid.net/specs/connect/1.0/issuer => Found
  // /.well-known/webfinger?resource=http://x/a*&rel=http://openid.net/specs/connect/1.0/issuer => Not Found
  const userSuppliedResource = resource.replace('http://x/', '');
  const sfilter = FILTER_PATTERN_ORG.replace('{0}', userSuppliedResource);
  console.log('Generated filter:', sfilter);

  ldapClient.search('ou=people,dc=example,dc=com', { filter: sfilter, scope: 'sub' }, (err, result) => {
    let found = false;
    result.on('searchEntry', (entry) => {
      console.log('entry: ' + JSON.stringify(entry.object));
      found = true;
    });

    result.on('end', (result) => {
      if (found) {
        res.json({
          subject: `acct:${userSuppliedResource}`,
          links: [
            {
              rel: "http://openid.net/specs/connect/1.0/issuer",
              href: "http://localhost:3001/authorize"
            }
          ]
        });
      } else {
        res.status(404).send('Not Found');
      }
    });

    result.on('error', (err) => {
      console.error('Error searching LDAP:', err);
      res.status(500).send('Internal server error');
    });
  });
});

app.get('/register', (req, res) => {
    res.send(`
      <form method="POST" action="/register">
        <label>User ID: <input type="text" name="userId" required /></label><br>
        <label>Password: <input type="password" name="password" required /></label><br>
        <input type="submit" value="Register" />
      </form>
    `);
});

app.post('/register', async (req, res) => {
    const { userId, password } = req.body;
    
    if (users[userId]) {
      return res.status(400).send('User ID is already taken');
    }
  
    const hashedPassword = await bcrypt.hash(password, 10);
    users[userId] = { userId, password: hashedPassword };
    
    res.send('Registration successful!');
});

app.get('/authorize', (req, res) => {
  const { response_type, client_id, redirect_uri, state, scope } = req.query;
  
  const client = clients[client_id];
  if (!client || response_type !== 'code' || !redirect_uri || !state || !scope) {
    return res.status(400).send('Invalid request');
  }

  if (!client.redirectUris.includes(redirect_uri)) {
    return res.status(400).send('Invalid redirect_uri');
  }

  req.session.authDetails = { client_id, redirect_uri, state, scope };
  res.redirect('/login');
});

app.get('/login', (req, res) => {
    if (!req.session.authDetails) {
        return res.status(400).send('No auth details in session. Start over.');
    }

    res.send(`
        <form method="POST" action="/login">
            <label>User ID: <input type="text" name="userId" required /></label><br>
            <label>Password: <input type="password" name="password" required /></label><br>
            <input type="submit" value="Login" />
        </form>
    `);
});

app.post('/login', async (req, res) => {
    const { userId, password } = req.body;
    
    if (!req.session.authDetails) {
      return res.status(400).send('No auth details in session. Start over.');
    }
    
    const user = users[userId];
    if (!user || !(await bcrypt.compare(password, user.password))) {
      return res.status(400).send('Invalid User ID or Password');
    }
    
    req.session.userId = userId; // Store user ID in session
    res.redirect('/consent'); // Redirect to the consent screen after successful login
});

app.get('/consent', (req, res) => {
    if (!req.session.userId) {
      return res.status(400).send('Not logged in. <a href="/login">Login here</a>');
    }
  
    res.send(`
      <form method="POST" action="/consent">
        <p>Do you consent to share your information with the client?</p>
        <input type="submit" value="Yes" name="consent" />
        <input type="submit" value="No" name="consent" />
      </form>
    `);
});

app.post('/consent', (req, res) => {
    if (req.body.consent !== 'Yes') {
      return res.status(400).send('User denied the consent');
    }
    
    const code = uuidv4();
    codes[code] = { ...req.session.authDetails, userId: req.session.userId };
    
    const { redirect_uri, state } = req.session.authDetails;
    const redirectUrl = new URL(redirect_uri);
    redirectUrl.searchParams.set('code', code);
    redirectUrl.searchParams.set('state', state);
    
    res.redirect(redirectUrl.toString());
});

app.post('/token', (req, res) => {
  const { grant_type, code, redirect_uri, client_id, client_secret } = req.body;
  
  const client = clients[client_id];
  if (!client || client.secret !== client_secret || grant_type !== 'authorization_code' || !code || !redirect_uri) {
    return res.status(400).send('Invalid request');
  }

  if (!client.redirectUris.includes(redirect_uri)) {
    return res.status(400).send('Invalid redirect_uri');
  }

  const authDetails = codes[code];
  if (!authDetails || authDetails.client_id !== client_id || authDetails.redirect_uri !== redirect_uri) {
    return res.status(400).send('Invalid code');
  }

  delete codes[code];

  const now = Math.floor(Date.now() / 1000);
    
  const payload = {
    iss: 'http://localhost:3001', // The issuer of the token (your IdP)
    sub: authDetails.userId, // The subject of the token (the user id)
    aud: authDetails.client_id, // The audience of the token (the client id)
    exp: now + 3600, // The expiration time of the token (1 hour from now)
    iat: now, // The issued at time of the token (now)
    auth_time: now, // The time the user was authenticated
    nonce: authDetails.nonce, // The nonce value received from the authentication request
  };

  const idToken = jwt.sign(payload, secret, { algorithm: 'HS256' });

  res.json({
    access_token: crypto.randomBytes(32).toString('hex'),
    token_type: 'Bearer',
    expires_in: 3600,
    id_token: idToken,
  });
});

app.listen(port, () => {
  console.log(`IdP is running at http://localhost:${port}`);
});
