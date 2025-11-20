import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_rank_search_api(name, fetch_all=True):
    """运动员等级查询 API
    
    Args:
        name: 运动员姓名
        fetch_all: 是否自动翻页获取所有记录
    """
    
    # API 端点
    url = "https://www.univsport.com/index.php"
    
    # 请求头
    headers = {
    }
    
    all_athletes = []  # 存储所有运动员记录
    page = 1
    total_records = 0
    
    def fetch_page(page_num):
        """获取指定页的数据"""
        params = {
            'm': 'api',
            'c': 'rank',
            'a': 'search',
            'page': str(page_num),
            'page_size': '10',
            'number': '',
            'name': name,
            'rank': '',
            'dict_value': '',
            'danwei': '',
            'nation_danwei': '',
            'item': '',
            'starttime': '',
            'endtime': '',
            'type': '""'
        }
        
        response = requests.post(url, params=params, headers=headers, timeout=10)
        return page_num, response.json()
    
    try:
        # 先获取第一页，确定总记录数
        print(f"\n正在请求第 1 页...")
        first_page_data = fetch_page(1)
        page_num, json_data = first_page_data
        
        print(f"状态码: 200")
        
        if json_data.get('response') != 1 or json_data.get('error') != 0:
            print(f"API 返回错误: {json_data.get('message')}")
            return None
        
        if 'data' not in json_data:
            print("响应中没有数据")
            return None
        
        data = json_data['data']
        total_records = int(data.get('total', 0))
        print(f"总记录数: {total_records}")
        
        list_data = data.get('list_data', [])
        print(f"第 1 页返回 {len(list_data)} 条记录")
        all_athletes.extend(list_data)
        
        if not fetch_all or len(all_athletes) >= total_records or not list_data:
            # 如果只有一页或不需要获取全部
            print("\n" + "=" * 80)
            print(f"共获取到 {len(all_athletes)} 条记录（总数: {total_records}）")
            print("=" * 80)
            
            for i, athlete in enumerate(all_athletes, 1):
                print(f"\n记录 {i}:")
                print(f"  ID: {athlete.get('athletes_info_id')}")
                print(f"  姓名: {athlete.get('athlete_realname')}")
                print(f"  证书编号: {athlete.get('athlete_number')}")
                print(f"  性别: {athlete.get('sex')}")
                print(f"  等级: {athlete.get('rank')}")
                print(f"  项目: {athlete.get('item')}")
                print(f"  审核单位: {athlete.get('audit_danwei')}")
            
            return all_athletes
        
        # 计算需要请求的页数（假设每页最多返回6条）
        estimated_pages = (total_records + 5) // 6  # 向上取整
        remaining_pages = list(range(2, estimated_pages + 1))
        
        print(f"\n开始并发请求剩余 {len(remaining_pages)} 页...")
        
        # 使用线程池并发请求剩余页面
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_page, page): page for page in remaining_pages}
            
            page_results = {}
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    result_page, result_data = future.result()
                    if result_data.get('response') == 1 and 'data' in result_data:
                        page_data = result_data['data'].get('list_data', [])
                        if page_data:
                            page_results[result_page] = page_data
                            print(f"第 {result_page} 页返回 {len(page_data)} 条记录")
                        else:
                            print(f"第 {result_page} 页没有更多记录")
                except Exception as e:
                    print(f"获取第 {page_num} 页失败: {e}")
        
        # 按页码顺序合并结果
        for page_num in sorted(page_results.keys()):
            all_athletes.extend(page_results[page_num])
            if len(all_athletes) >= total_records:
                break
        
        # 显示所有记录
        print("\n" + "=" * 80)
        print(f"共获取到 {len(all_athletes)} 条记录（总数: {total_records}）")
        print("=" * 80)
        
        for i, athlete in enumerate(all_athletes, 1):
            print(f"\n记录 {i}:")
            print(f"  姓名: {athlete.get('athlete_realname')}")
            print(f"  证书编号: {athlete.get('athlete_number')}")
            print(f"  性别: {athlete.get('sex')}")
            print(f"  等级: {athlete.get('rank')}")
            print(f"  项目: {athlete.get('item')}")
            print(f"  审核单位: {athlete.get('audit_danwei')}")
            print(f"  ID: {athlete.get('athletes_info_id')}")
        
        return all_athletes
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("运动员等级查询 API")
    print("=" * 60)
    
    # 用户输入姓名
    name = input("\n请输入要查询的运动员姓名: ").strip()
    
    if not name:
        print("姓名不能为空！")
    else:
        test_rank_search_api(name=name)
