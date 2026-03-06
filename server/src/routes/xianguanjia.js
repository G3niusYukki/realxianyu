const express = require('express');
const crypto = require('crypto');
const axios = require('axios');
const { auth } = require('../middleware/auth');

const router = express.Router();

function md5(str) {
  return crypto.createHash('md5').update(str, 'utf8').digest('hex');
}

function signRequest(appKey, appSecret, body, timestamp) {
  const bodyMd5 = md5(body || '');
  return md5(`${appKey},${bodyMd5},${timestamp},${appSecret}`);
}

router.post('/proxy', auth, async (req, res) => {
  try {
    const { path: apiPath, payload } = req.body;
    const appKey = process.env.XGJ_APP_KEY || '';
    const appSecret = process.env.XGJ_APP_SECRET || '';
    const baseUrl = process.env.XGJ_BASE_URL || 'https://open.goofish.pro';

    if (!appKey || !appSecret) {
      return res.status(400).json({ ok: false, error: 'XianGuanJia API not configured' });
    }

    const body = JSON.stringify(payload || {});
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const sign = signRequest(appKey, appSecret, body, timestamp);

    const url = `${baseUrl}${apiPath}`;
    const response = await axios.post(url, body, {
      params: { appid: appKey, timestamp, sign },
      headers: { 'Content-Type': 'application/json' },
      timeout: 15000,
    });

    res.json({ ok: true, data: response.data });
  } catch (error) {
    console.error('XGJ proxy error:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({
      ok: false,
      error: error.response?.data?.msg || error.message,
    });
  }
});

router.post('/order/receive', async (req, res) => {
  try {
    const appKey = process.env.XGJ_APP_KEY || '';
    const appSecret = process.env.XGJ_APP_SECRET || '';
    const { timestamp, sign } = req.query;

    if (!appKey || !appSecret) {
      return res.status(400).json({ code: 1, msg: 'Not configured' });
    }

    const rawBody = JSON.stringify(req.body);
    const expected = signRequest(appKey, appSecret, rawBody, timestamp);
    if (expected !== sign) {
      return res.status(401).json({ code: 401, msg: 'Invalid signature' });
    }

    console.log('Order push received:', JSON.stringify(req.body).slice(0, 500));
    res.json({ code: 0, msg: 'OK' });
  } catch (error) {
    console.error('Order push error:', error.message);
    res.status(500).json({ code: 500, msg: 'Internal error' });
  }
});

router.post('/product/receive', async (req, res) => {
  try {
    const appKey = process.env.XGJ_APP_KEY || '';
    const appSecret = process.env.XGJ_APP_SECRET || '';
    const { timestamp, sign } = req.query;

    if (!appKey || !appSecret) {
      return res.status(400).json({ code: 1, msg: 'Not configured' });
    }

    const rawBody = JSON.stringify(req.body);
    const expected = signRequest(appKey, appSecret, rawBody, timestamp);
    if (expected !== sign) {
      return res.status(401).json({ code: 401, msg: 'Invalid signature' });
    }

    console.log('Product push received:', JSON.stringify(req.body).slice(0, 500));
    res.json({ code: 0, msg: 'OK' });
  } catch (error) {
    console.error('Product push error:', error.message);
    res.status(500).json({ code: 500, msg: 'Internal error' });
  }
});

module.exports = router;
