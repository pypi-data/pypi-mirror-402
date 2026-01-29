import httpx
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from asyncio_throttle import Throttler


class JavaAPIConfig(BaseModel):
    """API配置"""
    base_url: str
    timeout: float = 30.0
    headers: Dict[str, str] = {}
    cookie_name: Optional[str] = None
    cookie_token: Optional[str] = None


class JavaAPIResponse(BaseModel):
    """API响应"""
    data: Any = None
    code: int = 200
    msg: str = ""


class JavaAPI:
    """Java后台API客户端"""
    
    def __init__(self, config: JavaAPIConfig):
        self.config = config
        self.throttler = Throttler(rate_limit=30, period=60)
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.config.headers
        }
        # Sa-Token支持通过header传递token
        if self.config.cookie_name and self.config.cookie_token:
            headers[self.config.cookie_name] = self.config.cookie_token.strip()
        return headers
    
    async def _request(self, method: str, endpoint: str, 
                       data: Optional[Dict] = None, 
                       params: Optional[Dict] = None) -> JavaAPIResponse:
        """发起HTTP请求"""
        async with self.throttler:
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            async with httpx.AsyncClient() as client:
                try:
                    kwargs = {
                        "method": method.upper(),
                        "url": url,
                        "headers": self._get_headers(),
                        "timeout": self.config.timeout
                    }
                    if data is not None:
                        kwargs["json"] = data
                    if params is not None:
                        kwargs["params"] = params
                    if self.config.cookie_name and self.config.cookie_token:
                        kwargs["cookies"] = {self.config.cookie_name: self.config.cookie_token.strip()}
                    
                    response = await client.request(**kwargs)
                    
                    try:
                        result = response.json()
                    except:
                        result = {"raw": response.text}
                    
                    return JavaAPIResponse(
                        data=result,
                        code=response.status_code,
                        msg="请求成功" if response.status_code < 400 else f"HTTP错误: {response.status_code}"
                    )
                except Exception as e:
                    return JavaAPIResponse(data=None, code=500, msg=f"请求失败: {str(e)}")

    # CRUD操作
    async def create(self, endpoint: str, data: Dict) -> JavaAPIResponse:
        """创建 POST"""
        return await self._request("POST", endpoint, data=data)
    
    async def get(self, endpoint: str, item_id: Optional[str] = None) -> JavaAPIResponse:
        """查询 GET /{id}"""
        if item_id:
            endpoint = f"{endpoint.rstrip('/')}/{item_id}"
        return await self._request("GET", endpoint)
    
    async def update(self, endpoint: str, data: Dict) -> JavaAPIResponse:
        """更新 PUT"""
        return await self._request("PUT", endpoint, data=data)
    
    async def batch_delete(self, endpoint: str, ids: List[int]) -> JavaAPIResponse:
        """批量删除 DELETE /batchDelete?ids=1,2,3"""
        return await self._request("DELETE", f"{endpoint.rstrip('/')}/batchDelete", params={"ids": ",".join(map(str, ids))})
    
    async def list(self, endpoint: str, params: Optional[Dict] = None) -> JavaAPIResponse:
        """列表查询 GET"""
        return await self._request("GET", endpoint, params=params)
    
    async def custom(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> JavaAPIResponse:
        """自定义请求"""
        return await self._request(method, endpoint, data=data, params=params)


class JavaAPIManager:
    """API管理器"""
    
    def __init__(self):
        self.apis: Dict[str, JavaAPI] = {}
    
    def add(self, name: str, config: JavaAPIConfig) -> None:
        self.apis[name] = JavaAPI(config)
    
    def get(self, name: str) -> Optional[JavaAPI]:
        return self.apis.get(name)
    
    def list(self) -> List[str]:
        return list(self.apis.keys())
