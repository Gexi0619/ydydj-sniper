"""
测试运动员等级查询API (univsport新版本)
测试URL: https://www.univsport.com/index.php?m=api&c=AthleteLevel&a=get_athlete_level_list&v=5.9.8&os_source=h5
"""
import pytest
import requests
import json


class TestUnivSportAPI:
    """univsport运动员等级查询API测试类"""
    
    # API配置
    BASE_URL = "https://www.univsport.com"
    API_PATH = "/index.php"
    
    @pytest.fixture
    def api_headers(self):
        """设置请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko)",
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "sec-fetch-site": "same-origin",
            "requestid": "067545469592",
            "accept-language": "zh-CN,zh-Hans;q=0.9",
            "sec-fetch-mode": "cors",
            "origin": "https://www.univsport.com",
            "referer": "https://www.univsport.com/wap/sportLevelInfoSearch?applySource=1",
            "sec-fetch-dest": "empty",
            "cookie": "univsport=03d03adc96aa086a2baa38e4f8df52df"
        }
    
    @pytest.fixture
    def query_params(self):
        """URL查询参数"""
        return {
            "m": "api",
            "c": "AthleteLevel",
            "a": "get_athlete_level_list",
            "v": "5.9.8",
            "os_source": "h5"
        }
    
    @pytest.fixture
    def request_body(self):
        """请求体数据"""
        return {
            "applySource": "1",
            "certificateNo": "20184770",
            "athleteRealName": "孙颖莎",
            "pageNo": 1
        }
    
    def test_get_athlete_level_list(self, api_headers, query_params, request_body):
        """测试获取运动员等级列表"""
        url = f"{self.BASE_URL}{self.API_PATH}"
        
        # 发送POST请求，使用JSON格式
        response = requests.post(
            url,
            params=query_params,
            headers=api_headers,
            json=request_body,
            timeout=30
        )
        
        # 验证响应状态码
        assert response.status_code == 200, f"API请求失败，状态码: {response.status_code}"
        
        # 打印响应信息
        print(f"\n{'='*60}")
        print(f"运动员等级查询测试 (univsport新版本API)")
        print(f"{'='*60}")
        print(f"请求URL: {url}")
        print(f"URL参数: {query_params}")
        print(f"请求体: {json.dumps(request_body, ensure_ascii=False)}")
        print(f"响应状态码: {response.status_code}")
        
        # 解析JSON响应
        try:
            response_data = response.json()
            print(f"\n响应内容:")
            print(json.dumps(response_data, ensure_ascii=False, indent=2))
            
            # 验证响应结构 - 这个API使用response和error字段
            assert "response" in response_data, "响应中缺少response字段"
            assert "error" in response_data, "响应中缺少error字段"
            
            # 打印关键信息
            print(f"\n响应代码: {response_data.get('response')}")
            print(f"错误代码: {response_data.get('error')}")
            print(f"消息: {response_data.get('message', '')}")
            
            # 打印数据信息
            if "data" in response_data and response_data["data"]:
                data_info = response_data.get('data')
                if isinstance(data_info, dict):
                    print(f"\n数据信息:")
                    print(f"  总数: {data_info.get('total', 0)}")
                    print(f"  页码: {data_info.get('pageNum', 0)}")
                    print(f"  页大小: {data_info.get('pageSize', 0)}")
                    
                    # 显示运动员信息
                    athlete_list = data_info.get('list', [])
                    if athlete_list:
                        print(f"  运动员列表:")
                        for i, athlete in enumerate(athlete_list, 1):
                            print(f"    [{i}] 姓名: {athlete.get('athleteRealName')}")
                            print(f"        证书号: {athlete.get('certificateNo')}")
                            print(f"        性别: {athlete.get('sex')}")
                            print(f"        项目: {athlete.get('item')}")
                            print(f"        等级: {athlete.get('rankTitle')}")
                            print(f"        授予单位: {athlete.get('grantUnitName')}")
                            
        except requests.exceptions.JSONDecodeError:
            print(f"\n响应内容 (非JSON):")
            print(response.text[:500])
            if len(response.text) > 500:
                print("...")
            assert False, "响应不是有效的JSON格式"
        
        print(f"\n{'='*60}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
