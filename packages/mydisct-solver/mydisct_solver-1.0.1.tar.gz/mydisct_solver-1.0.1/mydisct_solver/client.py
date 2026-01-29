import requests
import time
from typing import Any, Dict, Optional
from .types import TaskResponse, AccountInfo

class MyDisctClient:
    def __init__(self, apiKey: str, baseURL: str = 'https://solver-api.mydisct.com'):
        if not apiKey:
            raise ValueError('API key is required')
        self.apiKey = apiKey
        self.baseURL = baseURL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'apikey': self.apiKey
        })
    
    def createTask(self, captchaType: str, metadata: Dict[str, Any], payload: Dict[str, Any] = None) -> str:
        if payload is None:
            payload = {}
        
        response = self.session.post(
            f'{self.baseURL}/createTask',
            json={
                'auth': {'token': self.apiKey},
                'context': {'source': 'python-sdk', 'version': '1.0.0'},
                'captcha': {
                    'type': captchaType,
                    'metadata': metadata,
                    'payload': payload
                }
            }
        )
        
        data = response.json()
        
        if not data.get('success'):
            error_message = data.get('error', {}).get('message', 'Failed to create task')
            raise Exception(error_message)
        
        return data['task']['id']
    
    def fetchResult(self, taskId: str) -> TaskResponse:
        response = self.session.post(
            f'{self.baseURL}/fetchResult',
            json={'taskId': taskId}
        )
        return response.json()
    
    def waitForResult(self, taskId: str, pollingInterval: int = 5000, timeout: int = 120000) -> str:
        startTime = time.time() * 1000
        pollingIntervalSeconds = pollingInterval / 1000
        
        while (time.time() * 1000 - startTime) < timeout:
            result = self.fetchResult(taskId)
            
            if result['task']['status'] == 'completed':
                token = result.get('task', {}).get('result', {}).get('token')
                if not token:
                    raise Exception('Task completed but no token received')
                return token
            
            if result['task']['status'] == 'failed':
                error_message = result.get('error', {}).get('message', 'Task failed')
                raise Exception(error_message)
            
            time.sleep(pollingIntervalSeconds)
        
        raise Exception('Task timeout exceeded')
    
    def getBalance(self) -> float:
        response = self.session.get(f'{self.baseURL}/balance')
        data = response.json()
        
        if not data.get('success'):
            error_message = data.get('error', {}).get('message', 'Failed to get balance')
            raise Exception(error_message)
        
        return data['balance']['amount']
    
    def getAccountInfo(self) -> AccountInfo:
        response = self.session.get(f'{self.baseURL}/accountInfo')
        data = response.json()
        
        if not data.get('success'):
            error_message = data.get('error', {}).get('message', 'Failed to get account info')
            raise Exception(error_message)
        
        return data['account']
