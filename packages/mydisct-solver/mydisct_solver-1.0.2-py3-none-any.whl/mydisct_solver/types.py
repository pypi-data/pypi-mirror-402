from typing import TypedDict, Optional, List, Literal, Any, Dict

class ProxyConfig(TypedDict, total=False):
    protocol: Literal['http', 'https', 'socks4', 'socks5']
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]

class Cookie(TypedDict, total=False):
    name: str
    value: str
    domain: str
    path: Optional[str]

class TaskResult(TypedDict, total=False):
    token: str
    timestamp: Optional[str]

class Task(TypedDict, total=False):
    id: str
    status: Literal['processing', 'completed', 'failed']
    result: Optional[TaskResult]

class Error(TypedDict):
    code: str
    message: str

class TaskResponse(TypedDict, total=False):
    success: bool
    service: str
    message: str
    task: Task
    error: Optional[Error]

class AccountInfo(TypedDict):
    email: str
    username: str
    balance: float
    currency: str

class RecaptchaV2Options(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    invisible: Optional[bool]
    userAgent: Optional[str]
    cookies: Optional[List[Cookie]]
    domain: Optional[str]
    proxy: Optional[ProxyConfig]

class RecaptchaV3Options(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    recaptchaAction: Optional[str]
    userAgent: Optional[str]
    cookies: Optional[List[Cookie]]
    domain: Optional[str]
    proxy: Optional[ProxyConfig]

class RecaptchaV2EnterpriseOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    sValue: Optional[str]
    userAgent: Optional[str]
    cookies: Optional[List[Cookie]]
    proxy: Optional[ProxyConfig]

class RecaptchaV3EnterpriseOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    recaptchaAction: Optional[str]
    sValue: Optional[str]
    userAgent: Optional[str]
    cookies: Optional[List[Cookie]]
    proxy: Optional[ProxyConfig]

class HCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    invisible: Optional[bool]
    rqdata: Optional[str]
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class HCaptchaEnterpriseOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    domain: Optional[str]
    rqdata: Optional[str]
    userAgent: Optional[str]
    cookies: Optional[List[Cookie]]
    proxy: Optional[ProxyConfig]

class CloudflareTurnstileOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    proxy: Optional[ProxyConfig]

class CloudflareTurnstileManagedOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    data: str
    chlPageData: str
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class CloudflareChallengeOptions(TypedDict, total=False):
    siteUrl: str
    userAgent: Optional[str]
    proxy: ProxyConfig

class FunCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    subdomain: Optional[str]
    data: Optional[str]
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class GeeTestV4Options(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    apiServerSubdomain: Optional[str]
    proxy: ProxyConfig

class MTCaptchaOptions(TypedDict):
    siteUrl: str
    siteKey: str

class LeminCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    proxy: Optional[ProxyConfig]

class FriendlyCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    proxy: Optional[ProxyConfig]

class DataDomeOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    userAgent: Optional[str]
    proxy: ProxyConfig

class AltchaOptions(TypedDict, total=False):
    siteUrl: str
    challenge: str
    iterations: int
    salt: str
    signature: str
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class TencentCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    proxy: Optional[ProxyConfig]

class NetEaseCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    jsLibUrl: Optional[str]
    apiServerSubdomain: Optional[str]
    userAgent: Optional[str]
    captchaId: Optional[str]
    captchaHash: Optional[str]
    captchaTimestamp: Optional[int]
    proxy: Optional[ProxyConfig]

class FaucetPayCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class CaptchaFoxOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    userAgent: Optional[str]
    proxy: Optional[ProxyConfig]

class AWSCaptchaOptions(TypedDict, total=False):
    siteUrl: str
    siteKey: str
    context: Optional[str]
    proxy: Optional[ProxyConfig]

class TextCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    questionType: Optional[str]
    caseSensitive: Optional[bool]
    numeric: Optional[bool]
    minLength: Optional[int]
    maxLength: Optional[int]
    referenceImages: Optional[List[str]]

class RecaptchaImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str
    questionType: str

class HCaptchaImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class FunCaptchaImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class GeeTestV3ImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class GeeTestV4ImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class RotateImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: Optional[str]
    angle: Optional[int]
    referenceImages: Optional[List[str]]

class SlideCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: Optional[str]

class ClickCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    questionType: Optional[str]
    referenceImages: Optional[List[str]]

class GridCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    rows: Optional[int]
    columns: Optional[int]

class MultiSelectImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    referenceImages: Optional[List[str]]

class DragCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    questionType: Optional[str]
    referenceImages: Optional[List[str]]

class MTCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    module: Optional[str]
    maxLength: Optional[int]

class LeminCaptchaImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class DataDomeCaptchaImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: Optional[str]

class CaptchaFoxImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    questionType: Optional[str]
    referenceImages: Optional[List[str]]

class BinanceImageOptions(TypedDict, total=False):
    siteUrl: str
    images: List[str]
    question: str
    questionType: str
    referenceImages: Optional[List[str]]

class BLSImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class TikTokImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class ShopeeImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class TemuCaptchaImageOptions(TypedDict):
    siteUrl: str
    images: List[str]

class TencentImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class AWSWAFImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class ProsopoImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str

class FaucetPayImageOptions(TypedDict):
    siteUrl: str
    images: List[str]
    question: str
