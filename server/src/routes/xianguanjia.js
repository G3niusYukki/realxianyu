const express = require('express');
const crypto = require('crypto');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { auth } = require('../middleware/auth');

const router = express.Router();

const CONFIG_FILE = path.join(__dirname, '../../data/system_config.json');

const ALLOWED_API_PREFIXES = ['/api/open/'];

function md5(str) {
  return crypto.createHash('md5').update(str, 'utf8').digest('hex');
}

function signRequest(appKey, appSecret, body, timestamp) {
  const bodyMd5 = md5(body || '');
  return md5(`${appKey},${bodyMd5},${timestamp},${appSecret}`);
}

function loadXgjConfig() {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
      const xgj = config.xianguanjia || {};
      return {
        appKey: xgj.app_key || process.env.XGJ_APP_KEY || '',
        appSecret: xgj.app_secret || process.env.XGJ_APP_SECRET || '',
        baseUrl: xgj.base_url || process.env.XGJ_BASE_URL || 'https://open.goofish.pro',
      };
    }
  } catch (e) {
    console.error('Failed to load XGJ config:', e.message);
  }
  return {
    appKey: process.env.XGJ_APP_KEY || '',
    appSecret: process.env.XGJ_APP_SECRET || '',
    baseUrl: process.env.XGJ_BASE_URL || 'https://open.goofish.pro',
  };
}

function timingSafeCompare(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  const bufA = Buffer.from(a, 'utf8');
  const bufB = Buffer.from(b, 'utf8');
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

router.post('/proxy', auth, async (req, res) => {
  try {
    const { path: apiPath, payload } = req.body;

    if (!apiPath || !ALLOWED_API_PREFIXES.some(p => apiPath.startsWith(p))) {
      return res.status(403).json({ ok: false, error: 'API path not allowed' });
    }

    const cfg = loadXgjConfig();
    if (!cfg.appKey || !cfg.appSecret) {
      return res.status(400).json({ ok: false, error: 'XianGuanJia API not configured. Please configure in Settings.' });
    }

    const body = JSON.stringify(payload || {});
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const sign = signRequest(cfg.appKey, cfg.appSecret, body, timestamp);

    const url = `${cfg.baseUrl}${apiPath}`;
    const response = await axios.post(url, body, {
      params: { appid: cfg.appKey, timestamp, sign },
      headers: { 'Content-Type': 'application/json' },
      timeout: 15000,
    });

    res.json({ ok: true, data: response.data });
  } catch (error) {
    console.error('XGJ proxy error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({
      ok: false,
      error: error.response?.data?.msg || 'Request failed',
    });
  }
});

router.post('/order/receive', async (req, res) => {
  try {
    const cfg = loadXgjConfig();
    if (!cfg.appKey || !cfg.appSecret) {
      return res.status(400).json({ code: 1, msg: 'Not configured' });
    }

    const { timestamp, sign } = req.query;
    const rawBody = req.rawBody ? req.rawBody.toString('utf8') : JSON.stringify(req.body);
    const expected = signRequest(cfg.appKey, cfg.appSecret, rawBody, timestamp);

    if (!timingSafeCompare(expected, sign || '')) {
      return res.status(401).json({ code: 401, msg: 'Invalid signature' });
    }

    console.log('Order push received:', rawBody.slice(0, 500));
    res.json({ code: 0, msg: 'OK' });
  } catch (error) {
    console.error('Order push error:', error.message);
    res.status(500).json({ code: 500, msg: 'Internal error' });
  }
});

router.post('/product/receive', async (req, res) => {
  try {
    const cfg = loadXgjConfig();
    if (!cfg.appKey || !cfg.appSecret) {
      return res.status(400).json({ code: 1, msg: 'Not configured' });
    }

    const { timestamp, sign } = req.query;
    const rawBody = req.rawBody ? req.rawBody.toString('utf8') : JSON.stringify(req.body);
    const expected = signRequest(cfg.appKey, cfg.appSecret, rawBody, timestamp);

    if (!timingSafeCompare(expected, sign || '')) {
      return res.status(401).json({ code: 401, msg: 'Invalid signature' });
    }

    console.log('Product push received:', rawBody.slice(0, 500));
    res.json({ code: 0, msg: 'OK' });
  } catch (error) {
    console.error('Product push error:', error.message);
    res.status(500).json({ code: 500, msg: 'Internal error' });
  }
});

module.exports = router;
