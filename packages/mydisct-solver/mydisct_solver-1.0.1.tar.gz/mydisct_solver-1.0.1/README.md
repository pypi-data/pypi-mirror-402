# MyDisct Solver - Python

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/mydisct-solver.svg)](https://pypi.org/project/mydisct-solver/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/pypi/pyversions/mydisct-solver.svg)](https://pypi.org/project/mydisct-solver/)

**Enterprise AI-Powered Captcha Solving Service**

[Website](https://solver.mydisct.com) • [Documentation](https://solver.mydisct.com/api-docs) • [Discord](https://discord.gg/VmQCHnUK5R) • [GitHub](https://github.com/mydisctsolver/MyDisct-Solver)

</div>

---

## Overview

**MyDisct Solver** is an enterprise-grade, AI-powered CAPTCHA solving service designed for high-reliability automation and integration. Leveraging advanced neural networks, we deliver a **99.9% success rate** with an average solving time of **1.8 seconds** across more than **46 CAPTCHA types**.

Our service supports seamless integration via REST API, browser extensions, and automation frameworks such as Puppeteer, Selenium, and Playwright. All data is processed with enterprise-level encryption, and no sensitive information is stored.

---

## Features

- 99.9% success rate across supported challenges
- Average solving speed of 1.8 seconds
- Pay-as-you-go pricing (no subscription required)
- RESTful JSON API with real-time task polling
- Chrome extension with auto-detection and automatic solving
- Full compatibility with Selenium, Playwright, and automation tools
- Enterprise-grade security and data privacy
- Balance management and account information
- Webhook support for real-time notifications
- Proxy, UserAgent, Cookies support
- Full TypedDict support for type safety

---

## Installation

```bash
pip install mydisct-solver
```

---

## Quick Start

```python
from mydisct_solver import MyDisctSolver

solver = MyDisctSolver('YOUR_API_KEY')

token = solver.recaptchaV2Token({
    'siteUrl': 'https://example.com',
    'siteKey': '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-'
})

print('Token:', token)
```

---

## Supported CAPTCHA Types

### Token-Based CAPTCHAs (21 Types)

| Method | CAPTCHA Type | Description |
|--------|--------------|-------------|
| `recaptchaV2Token()` | reCAPTCHA v2 | Google reCAPTCHA v2 checkbox |
| `recaptchaV3Token()` | reCAPTCHA v3 | Google reCAPTCHA v3 score-based |
| `recaptchaEnterpriseToken()` | reCAPTCHA Enterprise | Google reCAPTCHA Enterprise |
| `hCaptchaToken()` | hCaptcha | Standard hCaptcha challenge |
| `hCaptchaEnterpriseToken()` | hCaptcha Enterprise | hCaptcha Enterprise version |
| `cloudflareTurnstileToken()` | Cloudflare Turnstile | Cloudflare Turnstile challenge |
| `cloudflareTurnstileManagedToken()` | Cloudflare Turnstile Managed | Managed Turnstile challenge |
| `cloudflareChallengeToken()` | Cloudflare Challenge | Cloudflare browser challenge |
| `funCaptchaToken()` | FunCaptcha | Arkose Labs FunCaptcha |
| `geeTestV4Token()` | GeeTest v4 | GeeTest v4 challenge |
| `mtCaptchaToken()` | MTCaptcha | MTCaptcha challenge |
| `captchaFoxToken()` | CaptchaFox | CaptchaFox challenge |
| `awsCaptchaToken()` | AWS WAF Captcha | AWS WAF Captcha token |
| `dataDomeToken()` | DataDome | DataDome challenge |
| `friendlyCaptchaToken()` | Friendly Captcha | Friendly Captcha widget |
| `leminCaptchaToken()` | Lemin CAPTCHA | Lemin CAPTCHA challenge |
| `tencentCaptchaToken()` | Tencent Captcha | Tencent Captcha challenge |
| `faucetPayCaptchaToken()` | FaucetPay Captcha | FaucetPay Captcha |
| `netEaseCaptchaToken()` | NetEase Captcha | NetEase Captcha (China) |
| `altchaCaptchaToken()` | Altcha | Altcha proof-of-work |
| `cyberSiAraToken()` | CyberSiAra | CyberSiAra challenge |

### Image-Based CAPTCHAs (25 Types)

| Method | CAPTCHA Type | Description |
|--------|--------------|-------------|
| `hCaptchaImage()` | hCaptcha Image | hCaptcha image classification |
| `recaptchaImage()` | reCAPTCHA Image | reCAPTCHA image challenges |
| `funCaptchaImage()` | FunCaptcha Image | FunCaptcha image puzzles |
| `geeTestV3Image()` | GeeTest v3 Image | GeeTest v3 image slide |
| `geeTestV4Image()` | GeeTest v4 Image | GeeTest v4 image challenges |
| `tikTokCaptchaImage()` | TikTok Captcha | TikTok image puzzle |
| `rotateCaptchaImage()` | Rotate Captcha | Rotate image to correct angle |
| `tencentCaptchaImage()` | Tencent Image | Tencent image challenge |
| `binanceCaptchaImage()` | Binance Captcha | Binance puzzle captcha |
| `shopeeCaptchaImage()` | Shopee Captcha | Shopee image puzzle |
| `awsWafCaptchaImage()` | AWS WAF Image | AWS WAF image challenge |
| `mtCaptchaImage()` | MTCaptcha Image | MTCaptcha image challenge |
| `captchaFoxImage()` | CaptchaFox Image | CaptchaFox image puzzle |
| `prosopoImage()` | Prosopo Image | Prosopo image challenge |
| `blsCaptchaImage()` | BLS Captcha | BLS image captcha |
| `temuCaptchaImage()` | Temu Captcha | Temu puzzle captcha |
| `dataDomeImage()` | DataDome Image | DataDome image challenge |
| `leminCaptchaImage()` | Lemin Image | Lemin image challenge |
| `faucetPayCaptchaImage()` | FaucetPay Image | FaucetPay image puzzle |
| `gridCaptchaImage()` | Grid Captcha | Grid-based image selection |
| `multiSelectCaptchaImage()` | Multi-Select | Multiple image selection |
| `clickCaptchaImage()` | Click Captcha | Click specific points on image |
| `dragCaptchaImage()` | Drag Captcha | Drag slider puzzle |
| `slideCaptchaImage()` | Slide Captcha | Slide puzzle to match |
| `textCaptchaImage()` | Text Captcha | Text-based image recognition |

---

## Usage Examples

### reCAPTCHA v2

```python
token = solver.recaptchaV2Token({
    'siteUrl': 'https://example.com',
    'siteKey': '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
    'invisible': False
})
```

### reCAPTCHA v3

```python
token = solver.recaptchaV3Token({
    'siteUrl': 'https://example.com',
    'siteKey': '6LdO5_IbAAAAAAeVBL9TClS19NUTt5wswEb3Q7m5',
    'recaptchaAction': 'submit',
    'minScore': 0.7
})
```

### hCaptcha

```python
token = solver.hCaptchaToken({
    'siteUrl': 'https://accounts.hcaptcha.com/demo',
    'siteKey': '10000000-ffff-ffff-ffff-000000000001',
    'invisible': False
})
```

### Cloudflare Turnstile

```python
token = solver.cloudflareTurnstileToken({
    'siteUrl': 'https://example.com',
    'siteKey': '0x4AAAAAAAC3DHQFLr1GavRN',
    'recaptchaAction': 'login'
})
```

### Image Captcha Example

```python
solution = solver.textCaptchaImage({
    'siteUrl': 'https://example.com',
    'images': ['data:image/png;base64,iVBORw0KGgoAAAANS...'],
    'questionType': 'text',
    'caseSensitive': False
})

print('Captcha text:', solution)
```

### With Proxy Support

```python
token = solver.recaptchaV2Token({
    'siteUrl': 'https://example.com',
    'siteKey': '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-',
    'proxy': {
        'protocol': 'http',
        'host': '123.45.67.89',
        'port': 8080,
        'username': 'user',
        'password': 'pass'
    }
})
```

### With UserAgent & Cookies

```python
token = solver.hCaptchaToken({
    'siteUrl': 'https://example.com',
    'siteKey': 'site-key-here',
    'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'cookies': [
        {'name': 'session', 'value': 'abc123', 'domain': '.example.com'}
    ]
})
```

### Check Balance

```python
balance = solver.getBalance()
print(f'Current balance: ${balance} USD')
```

### Get Account Info

```python
account = solver.getAccountInfo()
print('Email:', account['email'])
print('Username:', account['username'])
print('Balance:', account['balance'], account['currency'])
```

---

## Advanced Features

### Custom Base URL

```python
solver = MyDisctSolver('YOUR_API_KEY', 'https://custom-api.mydisct.com')
```

### Type Safety with TypedDict

```python
from mydisct_solver import MyDisctSolver, RecaptchaV2Options

solver = MyDisctSolver('YOUR_API_KEY')

options: RecaptchaV2Options = {
    'siteUrl': 'https://example.com',
    'siteKey': 'your-site-key',
    'invisible': False
}

token: str = solver.recaptchaV2Token(options)
```

---

## Documentation

- **Full API Documentation**: [https://solver.mydisct.com/api-docs](https://solver.mydisct.com/api-docs)
- **Browser Extension Guide**: [https://solver.mydisct.com/api-docs/browser-extension](https://solver.mydisct.com/api-docs/browser-extension)
- **Pricing**: [https://solver.mydisct.com](https://solver.mydisct.com)

---

## Support & Community

<div align="center">

### Join our community for support, updates, and discussions!

[![Discord](https://img.shields.io/badge/Discord-Join%20Server-7289da?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/VmQCHnUK5R)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mydisctsolver/MyDisct-Solver)

**Technical Support**: support@solver.mydisct.com  
**Website**: [solver.mydisct.com](https://solver.mydisct.com)

</div>

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

<div align="center">

**MyDisct Solver** – Reliable, fast, and secure CAPTCHA solving for enterprise and automation needs.

*We are committed to building tools that empower users and contribute to a freer, more open internet.*

</div>
