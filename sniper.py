"""
运动员等级证书编号查询工具
"""
import asyncio
import aiohttp
import json
import os
from datetime import datetime
from tqdm.asyncio import tqdm


class SimpleAthleteQuery:
    """运动员等级证书编号查询工具"""
    
    def __init__(self):
        self.base_url = "https://www.univsport.com/index.php"
        self.cache_file = "history.json"
        self.results_file = "query_results.json"
        self.found_certificates_file = "certificates.txt"
        self.cache = self.load_cache()
        self.found_certificates = self.load_found_certificates()
        
        # API参数
        self.params = {
            "m": "api", "c": "AthleteLevel", "a": "get_athlete_level_list",
            "v": "5.9.8", "os_source": "h5"
        }
        
        self.headers = {
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
    
    def load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 如果是数组格式，转换为字典
                if isinstance(cache_data, list):
                    cache_dict = {}
                    for item in cache_data:
                        if isinstance(item, dict) and 'name' in item and 'cert_no' in item:
                            key = f"{item['name']}_{item['cert_no']}"
                            cache_dict[key] = item
                    return cache_dict
                # 如果已经是字典格式，直接返回
                elif isinstance(cache_data, dict):
                    return cache_data
            except:
                pass
        return {}
    
    def load_found_certificates(self):
        """加载已找到的证书记录"""
        found = set()
        if os.path.exists(self.found_certificates_file):
            try:
                with open(self.found_certificates_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('==='):
                            # 提取证书号（格式：证书编号: XXX | 姓名 - 等级 - 项目）
                            if line.startswith('证书编号:'):
                                # 提取冒号和竖线之间的证书号
                                parts = line.split('|')
                                if parts:
                                    cert_part = parts[0].replace('证书编号:', '').strip()
                                    if cert_part:
                                        found.add(cert_part)
            except:
                pass
        return found
    
    def save_found_certificate(self, athlete_info):
        """保存找到的证书信息到txt文件"""
        cert_no = athlete_info.get('certificateNo', '')
        if not cert_no or cert_no in self.found_certificates:
            return  # 已存在，不重复写入
        
        # 标记为已找到
        self.found_certificates.add(cert_no)
        
        # 追加到文件
        with open(self.found_certificates_file, 'a', encoding='utf-8') as f:
            # 如果是新文件，先写标题
            if os.path.getsize(self.found_certificates_file) == 0:
                f.write("=" * 60 + "\n")
                f.write("查询到的等级证书编号\n")
                f.write("=" * 60 + "\n\n")
            
            # 写入证书信息
            name = athlete_info.get('athleteRealName', '未知')
            rank = athlete_info.get('rankTitle', '未知')
            item = athlete_info.get('item', '未知')
            f.write(f"证书编号: {cert_no} | {name} - {rank} - {item}\n")
    
    def save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            f.write('[\n')
            cache_items = list(self.cache.values())
            for i, item in enumerate(cache_items):
                json_str = json.dumps(item, ensure_ascii=False)
                if i < len(cache_items) - 1:
                    f.write(f'  {json_str},\n')
                else:
                    f.write(f'  {json_str}\n')
            f.write(']')
    
    def get_cache_key(self, name, cert_no):
        """生成缓存键"""
        return f"{name}_{cert_no}"
    
    async def query_one(self, session, name, cert_no):
        """查询单个证书号"""
        cache_key = self.get_cache_key(name, cert_no)
        
        # 检查缓存
        if cache_key in self.cache:
            return cert_no, self.cache[cache_key], True  # True表示来自缓存
        
        # 发送请求
        data = {
            "applySource": "1",
            "certificateNo": cert_no,
            "athleteRealName": name,
            "pageNo": 1
        }
        
        try:
            await asyncio.sleep(0.05)  # 小延迟避免过于频繁
            async with session.post(self.base_url, params=self.params, 
                                  headers=self.headers, json=data, timeout=15) as resp:
                
                if resp.status == 200:
                    try:
                        # 先尝试正常的JSON解析
                        result = await resp.json()
                    except Exception:
                        try:
                            # 如果失败，强制从文本解析JSON（忽略content-type）
                            text_content = await resp.text()
                            result = json.loads(text_content)
                        except Exception as e:
                            # 最终失败才报错
                            text_content = await resp.text()
                            result = {
                                "query_success": False,
                                "has_data": False,
                                "error": f"JSON解析失败: {str(e)}",
                                "content_type": resp.headers.get('content-type', '未知'),
                                "response_text": text_content[:500]
                            }
                    
                    # 检查是否只有error字段（无response字段），或error为null/空字符串且没有其他有效字段
                    # 这种情况视为查询失败，不缓存
                    if isinstance(result, dict):
                        # 情况1: 只有error字段，且为空字符串或null
                        if "response" not in result and "error" in result:
                            error_value = result.get("error")
                            if error_value is None or error_value == "":
                                return cert_no, {
                                    "time": datetime.now().isoformat(),
                                    "cert_no": cert_no,
                                    "name": name,
                                    "response": {
                                        "query_success": False,
                                        "has_data": False,
                                        "error": "API返回无效响应（error为空或null），视为查询失败"
                                    }
                                }, False  # 不缓存
                        
                        # 情况2: 有response字段，但error不为0，视为查询失败
                        if "response" in result and "error" in result:
                            error_value = result.get("error")
                            # error不为0（可能是数字或字符串），视为失败
                            if error_value != 0 and error_value != "0":
                                return cert_no, {
                                    "time": datetime.now().isoformat(),
                                    "cert_no": cert_no,
                                    "name": name,
                                    "response": {
                                        "query_success": False,
                                        "has_data": False,
                                        "error": f"API返回error={error_value}，查询失败"
                                    }
                                }, False  # 不缓存
                    
                    # 标记查询是否成功和是否有数据
                    if isinstance(result, dict):
                        # 如果结果包含response字段，说明是API正常响应
                        if "response" in result:
                            result["query_success"] = True
                            result["has_data"] = (
                                result.get("response") == 0 and 
                                result.get("error") == 0 and 
                                result.get("data", {}).get("total", 0) > 0
                            )
                        # 如果没有response字段但也不是错误结构，可能是其他格式
                        elif "query_success" not in result:
                            result["query_success"] = True
                            result["has_data"] = False
                else:
                    result = {
                        "query_success": False,
                        "has_data": False,
                        "error": f"HTTP {resp.status}"
                    }
                
                # 缓存结果
                self.cache[cache_key] = {
                    "time": datetime.now().isoformat(),
                    "cert_no": cert_no,
                    "name": name,
                    "response": result
                }
                return cert_no, self.cache[cache_key], False  # False表示新查询
                
        except Exception as e:
            # 缓存错误结果
            error_result = {
                "time": datetime.now().isoformat(),
                "cert_no": cert_no,
                "name": name,
                "response": {
                    "query_success": False,
                    "has_data": False,
                    "error": str(e)
                }
            }
            self.cache[cache_key] = error_result
            return cert_no, error_result, False
    
    async def batch_query(self, name, start_num, end_num):
        """批量查询"""
        cert_numbers = [str(i) for i in range(start_num, end_num + 1)]
        total = len(cert_numbers)
        
        # 统计缓存情况
        cached_count = sum(1 for cert in cert_numbers 
                          if self.get_cache_key(name, cert) in self.cache)
        
        print(f"查询运动员: {name}")
        print(f"证书号范围: {start_num} - {end_num} (共{total}个)")
        print(f"已缓存: {cached_count}个, 需查询: {total - cached_count}个")
        print("-" * 50)
        
        # 确保logs文件夹存在
        os.makedirs("logs", exist_ok=True)
        
        # 准备结果文件（临时文件名，最后会重命名）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        temp_results_file = os.path.join("logs", f"results_{name}_{timestamp}_{start_num}_{end_num}_temp.json")
        results_file_handle = open(temp_results_file, 'w', encoding='utf-8')
        results_file_handle.write('[\n')
        
        # 执行分批并发查询
        batch_size = 100
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            results = []
            cached_hits = 0
            new_queries = 0
            successful_queries = 0
            valid_data_count = 0
            found_athletes = 0
            
            # 使用进度条，分批并发查询
            with tqdm(total=total, desc="查询进度") as pbar:
                for batch_start in range(0, total, batch_size):
                    batch_end = min(batch_start + batch_size, total)
                    batch_certs = cert_numbers[batch_start:batch_end]
                    
                    # 并发查询这一批
                    tasks = [self.query_one(session, name, cert) for cert in batch_certs]
                    batch_results = await asyncio.gather(*tasks)
                    
                    # 按顺序处理这一批的结果
                    for idx, (cert_no, data, from_cache) in enumerate(batch_results):
                        global_idx = batch_start + idx
                        results.append(data)
                        
                        # 立即写入文件
                        json_str = json.dumps(data, ensure_ascii=False)
                        if global_idx < total - 1:
                            results_file_handle.write(f'  {json_str},\n')
                        else:
                            results_file_handle.write(f'  {json_str}')
                        results_file_handle.flush()  # 强制写入磁盘
                        
                        if from_cache:
                            cached_hits += 1
                        else:
                            new_queries += 1
                        
                        # 统计查询结果
                        response = data.get("response", {})
                        if isinstance(response, dict):
                            # 统计成功的查询（网络请求成功）
                            if response.get("query_success", False):
                                successful_queries += 1
                            
                            # 统计有效数据（有运动员信息）
                            if response.get("has_data", False):
                                valid_data_count += 1
                                # 计算找到的运动员数量并保存到txt
                                if "data" in response and isinstance(response["data"], dict):
                                    athletes = response["data"].get("list", [])
                                    if isinstance(athletes, list):
                                        found_athletes += len(athletes)
                                        # 保存每个找到的运动员信息
                                        for athlete in athletes:
                                            self.save_found_certificate(athlete)
                        
                        pbar.update(1)
        
        # 保存缓存
        self.save_cache()
        
        # 关闭结果文件
        results_file_handle.write('\n]')
        results_file_handle.close()
        
        # 重命名文件，加上总结果项数
        final_results_file = os.path.join("logs", f"results_{name}_{timestamp}_{start_num}_{end_num}_{total}.json")
        os.rename(temp_results_file, final_results_file)
        
        # 显示统计
        print(f"\n查询完成!")
        print(f"缓存命中: {cached_hits}个")
        print(f"新查询: {new_queries}个")
        print(f"成功查询: {successful_queries}个")
        print(f"成功率: {(successful_queries/total*100):.1f}%")
        print(f"缓存文件: {final_results_file}")
        print(f"\n{'='*50}")
        if found_athletes > 0:
            print(f"✓ 找到有效证书编号: {found_athletes} 个")
            print(f"  已保存到: certificates.txt")
        else:
            print(f"✗ 未找到有效证书编号")
        print(f"{'='*50}")
        
        # 显示找到的证书编号详情
        if found_athletes > 0:
            print(f"\n查询到的等级证书编号:")
            count = 0
            for result in results:
                response = result.get("response", {})
                if isinstance(response, dict) and response.get("has_data", False):
                    if "data" in response and isinstance(response["data"], dict):
                        athletes = response["data"].get("list", [])
                        if isinstance(athletes, list):
                            for athlete in athletes:
                                count += 1
                                cert_no = athlete.get('certificateNo', '未知')
                                name = athlete.get('athleteRealName', '未知')
                                rank = athlete.get('rankTitle', '未知')
                                item = athlete.get('item', '未知')
                                print(f"  {count}. 证书编号: {cert_no} | {name} - {rank} - {item}")
        
        # 显示一些无效查询的示例（用于调试）
        failed_queries = [r for r in results if not r.get("response", {}).get("query_success", False)]
        if failed_queries:
            print(f"\n查询失败示例 (前3个):")
            for i, failed in enumerate(failed_queries[:3], 1):
                print(f"  {i}. 证书号: {failed.get('cert_no')} - "
                      f"错误: {failed.get('response', {}).get('error', '未知错误')}")
        
        return results


def main():
    """主程序"""
    print("=" * 60)
    print("运动员等级证书编号查询工具")
    print("=" * 60)
    
    # 获取用户输入
    name = input("请输入运动员姓名: ").strip()
    if not name:
        print("姓名不能为空!")
        return
    
    try:
        start_str = input("请输入起始证书号 (如 20210000): ").strip()
        start_num = int(start_str)
        
        end_str = input("请输入结束证书号 (如 20210099): ").strip()  
        end_num = int(end_str)
        
        if start_num > end_num:
            print("起始号不能大于结束号!")
            return
            
        if end_num - start_num > 10001:
            confirm = input(f"查询数量较大({end_num - start_num + 1}个), 继续? (y/N): ")
            if confirm.lower() != 'y':
                return
    
    except ValueError:
        print("证书号必须是数字!")
        return
    
    # 执行查询
    query_tool = SimpleAthleteQuery()
    
    try:
        asyncio.run(query_tool.batch_query(name, start_num, end_num))
    except KeyboardInterrupt:
        print("\n查询被中断")
    except Exception as e:
        print(f"查询出错: {e}")


if __name__ == "__main__":
    main()