from .client import MyDisctClient
from .types import (
    RecaptchaV2Options, RecaptchaV3Options, RecaptchaV2EnterpriseOptions,
    RecaptchaV3EnterpriseOptions, HCaptchaOptions, HCaptchaEnterpriseOptions,
    CloudflareTurnstileOptions, CloudflareTurnstileManagedOptions,
    CloudflareChallengeOptions, FunCaptchaOptions, GeeTestV4Options,
    MTCaptchaOptions, LeminCaptchaOptions, FriendlyCaptchaOptions,
    DataDomeOptions, AltchaOptions, TencentCaptchaOptions,
    NetEaseCaptchaOptions, FaucetPayCaptchaOptions, CaptchaFoxOptions,
    AWSCaptchaOptions, TextCaptchaImageOptions, RecaptchaImageOptions,
    HCaptchaImageOptions, FunCaptchaImageOptions, GeeTestV3ImageOptions,
    GeeTestV4ImageOptions, RotateImageOptions, SlideCaptchaImageOptions,
    ClickCaptchaImageOptions, GridCaptchaImageOptions, MultiSelectImageOptions,
    DragCaptchaImageOptions, MTCaptchaImageOptions, LeminCaptchaImageOptions,
    DataDomeCaptchaImageOptions, CaptchaFoxImageOptions, BinanceImageOptions,
    BLSImageOptions, TikTokImageOptions, ShopeeImageOptions,
    TemuCaptchaImageOptions, TencentImageOptions, AWSWAFImageOptions,
    ProsopoImageOptions, FaucetPayImageOptions, AccountInfo
)
from typing import Optional

class MyDisctSolver:
    def __init__(self, apiKey: str, baseURL: Optional[str] = None):
        if baseURL is None:
            self.client = MyDisctClient(apiKey)
        else:
            self.client = MyDisctClient(apiKey, baseURL)
    
    def recaptchaV2Token(self, options: RecaptchaV2Options) -> str:
        taskId = self.client.createTask(
            'RECAPTCHA_V2_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'invisible': options.get('invisible'),
                'userAgent': options.get('userAgent'),
                'cookies': options.get('cookies'),
                'domain': options.get('domain'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def recaptchaV3Token(self, options: RecaptchaV3Options) -> str:
        taskId = self.client.createTask(
            'RECAPTCHA_V3_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'recaptchaAction': options.get('recaptchaAction', 'verify'),
                'userAgent': options.get('userAgent'),
                'cookies': options.get('cookies'),
                'domain': options.get('domain'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def recaptchaV2EnterpriseToken(self, options: RecaptchaV2EnterpriseOptions) -> str:
        taskId = self.client.createTask(
            'RECAPTCHA_V2_ENTERPRISE_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'sValue': options.get('sValue'),
                'userAgent': options.get('userAgent'),
                'cookies': options.get('cookies'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def recaptchaV3EnterpriseToken(self, options: RecaptchaV3EnterpriseOptions) -> str:
        taskId = self.client.createTask(
            'RECAPTCHA_V3_ENTERPRISE_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'recaptchaAction': options.get('recaptchaAction', 'verify'),
                'sValue': options.get('sValue'),
                'userAgent': options.get('userAgent'),
                'cookies': options.get('cookies'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def hCaptchaToken(self, options: HCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'HCAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'invisible': options.get('invisible'),
                'rqdata': options.get('rqdata'),
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def hCaptchaEnterpriseToken(self, options: HCaptchaEnterpriseOptions) -> str:
        taskId = self.client.createTask(
            'HCAPTCHA_ENTERPRISE_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey'],
                'domain': options.get('domain')
            },
            {
                'rqdata': options.get('rqdata'),
                'userAgent': options.get('userAgent'),
                'cookies': options.get('cookies'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def cloudflareTurnstileToken(self, options: CloudflareTurnstileOptions) -> str:
        taskId = self.client.createTask(
            'CLOUDFLARE_TURNSTILE_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def cloudflareTurnstileManagedToken(self, options: CloudflareTurnstileManagedOptions) -> str:
        taskId = self.client.createTask(
            'CLOUDFLARE_TURNSTILE_MANAGED_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'data': options['data'],
                'chlPageData': options['chlPageData'],
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def cloudflareChallengeToken(self, options: CloudflareChallengeOptions) -> str:
        taskId = self.client.createTask(
            'CLOUDFLARE_CHALLENGE_TOKEN',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'userAgent': options.get('userAgent'),
                'proxy': options['proxy']
            }
        )
        return self.client.waitForResult(taskId, 5000, 180000)
    
    def funCaptchaToken(self, options: FunCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'FUNCAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey'],
                'subdomain': options.get('subdomain')
            },
            {
                'data': options.get('data'),
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def geeTestV4Token(self, options: GeeTestV4Options) -> str:
        taskId = self.client.createTask(
            'GEETEST_V4_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey'],
                'apiServerSubdomain': options.get('apiServerSubdomain')
            },
            {
                'proxy': options['proxy']
            }
        )
        return self.client.waitForResult(taskId)
    
    def mtCaptchaToken(self, options: MTCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'MTCAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {}
        )
        return self.client.waitForResult(taskId)
    
    def leminCaptchaToken(self, options: LeminCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'LEMIN_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def friendlyCaptchaToken(self, options: FriendlyCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'FRIENDLY_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def dataDomeToken(self, options: DataDomeOptions) -> str:
        taskId = self.client.createTask(
            'DATADOME_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'userAgent': options.get('userAgent'),
                'proxy': options['proxy']
            }
        )
        return self.client.waitForResult(taskId)
    
    def altchaCaptchaToken(self, options: AltchaOptions) -> str:
        taskId = self.client.createTask(
            'ALTCHA_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': ''
            },
            {
                'metadata': {
                    'challenge': options['challenge'],
                    'iterations': str(options['iterations']),
                    'salt': options['salt'],
                    'signature': options['signature']
                },
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def tencentCaptchaToken(self, options: TencentCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'TENCENT_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def netEaseCaptchaToken(self, options: NetEaseCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'NETEASE_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey'],
                'jsLibUrl': options.get('jsLibUrl'),
                'apiServerSubdomain': options.get('apiServerSubdomain')
            },
            {
                'userAgent': options.get('userAgent'),
                'captchaId': options.get('captchaId'),
                'captchaHash': options.get('captchaHash'),
                'captchaTimestamp': options.get('captchaTimestamp'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def faucetPayCaptchaToken(self, options: FaucetPayCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'FAUCETPAY_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def captchaFoxToken(self, options: CaptchaFoxOptions) -> str:
        taskId = self.client.createTask(
            'CAPTCHAFOX_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'userAgent': options.get('userAgent'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def awsCaptchaToken(self, options: AWSCaptchaOptions) -> str:
        taskId = self.client.createTask(
            'AWS_CAPTCHA_TOKEN',
            {
                'siteUrl': options['siteUrl'],
                'siteKey': options['siteKey']
            },
            {
                'context': options.get('context'),
                'proxy': options.get('proxy')
            }
        )
        return self.client.waitForResult(taskId)
    
    def getBalance(self) -> float:
        return self.client.getBalance()
    
    def getAccountInfo(self) -> AccountInfo:
        return self.client.getAccountInfo()
    
    def textCaptchaImage(self, options: TextCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'TEXT_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'questionType': options.get('questionType', 'text'),
                'caseSensitive': options.get('caseSensitive'),
                'numeric': options.get('numeric'),
                'minLength': options.get('minLength'),
                'maxLength': options.get('maxLength'),
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def recaptchaImage(self, options: RecaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'RECAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'questionType': options['questionType']
            }
        )
        return self.client.waitForResult(taskId)
    
    def hCaptchaImage(self, options: HCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'HCAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def funCaptchaImage(self, options: FunCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'FUNCAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def geeTestV3Image(self, options: GeeTestV3ImageOptions) -> str:
        taskId = self.client.createTask(
            'GEETEST_V3_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def geeTestV4Image(self, options: GeeTestV4ImageOptions) -> str:
        taskId = self.client.createTask(
            'GEETEST_V4_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def rotateImage(self, options: RotateImageOptions) -> str:
        taskId = self.client.createTask(
            'ROTATE_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options.get('question'),
                'angle': options.get('angle'),
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def slideCaptchaImage(self, options: SlideCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'SLIDE_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options.get('question')
            }
        )
        return self.client.waitForResult(taskId)
    
    def clickCaptchaImage(self, options: ClickCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'CLICK_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'questionType': options.get('questionType', 'click'),
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def gridCaptchaImage(self, options: GridCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'GRID_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'rows': options.get('rows'),
                'columns': options.get('columns')
            }
        )
        return self.client.waitForResult(taskId)
    
    def multiSelectImage(self, options: MultiSelectImageOptions) -> str:
        taskId = self.client.createTask(
            'MULTI_SELECT_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def dragCaptchaImage(self, options: DragCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'DRAG_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'questionType': options.get('questionType', 'drag'),
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def mtCaptchaImage(self, options: MTCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'MTCAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'module': options.get('module', 'mtcaptcha'),
                'maxLength': options.get('maxLength', 5)
            }
        )
        return self.client.waitForResult(taskId)
    
    def leminCaptchaImage(self, options: LeminCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'LEMIN_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def dataDomeCaptchaImage(self, options: DataDomeCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'DATADOME_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options.get('question')
            }
        )
        return self.client.waitForResult(taskId)
    
    def captchaFoxImage(self, options: CaptchaFoxImageOptions) -> str:
        taskId = self.client.createTask(
            'CAPTCHAFOX_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'questionType': options.get('questionType'),
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def binanceImage(self, options: BinanceImageOptions) -> str:
        taskId = self.client.createTask(
            'BINANCE_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question'],
                'questionType': options['questionType'],
                'referenceImages': options.get('referenceImages', [])
            }
        )
        return self.client.waitForResult(taskId)
    
    def blsImage(self, options: BLSImageOptions) -> str:
        taskId = self.client.createTask(
            'BLS_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def tikTokImage(self, options: TikTokImageOptions) -> str:
        taskId = self.client.createTask(
            'TIKTOK_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def shopeeImage(self, options: ShopeeImageOptions) -> str:
        taskId = self.client.createTask(
            'SHOPEE_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def temuCaptchaImage(self, options: TemuCaptchaImageOptions) -> str:
        taskId = self.client.createTask(
            'TEMU_CAPTCHA_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images']
            }
        )
        return self.client.waitForResult(taskId)
    
    def tencentImage(self, options: TencentImageOptions) -> str:
        taskId = self.client.createTask(
            'TENCENT_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def awsWAFImage(self, options: AWSWAFImageOptions) -> str:
        taskId = self.client.createTask(
            'AWS_WAF_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def prosopoImage(self, options: ProsopoImageOptions) -> str:
        taskId = self.client.createTask(
            'PROSOPO_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
    
    def faucetPayImage(self, options: FaucetPayImageOptions) -> str:
        taskId = self.client.createTask(
            'FAUCETPAY_IMAGE',
            {
                'siteUrl': options['siteUrl']
            },
            {
                'images': options['images'],
                'question': options['question']
            }
        )
        return self.client.waitForResult(taskId)
