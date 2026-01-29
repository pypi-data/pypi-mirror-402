import requests
import time
import pandas as pd
from .util import get_response_json_with_check2


field_mapping = {
    'date': 'date',
    'name': 'style_factor',
    'value': 'value'  # 这里需要根据实际返回的字段名进行调整
}


def get_style_attr_trend(client, simulate_portfolio_id):
    """
    获取风格归因趋势

    Args:
        client: DYPMS客户端实例
        simulate_portfolio_id: 组合代码，必传
    """
    # 1. 调用计算接口
    calc_url = f"{client.base_url}/lib/simulate/portfolio/v1/styleAttrTrend"
    headers = client.get_headers()
    params = {
        'accountCode': simulate_portfolio_id
    }

    try:
        # 发送计算请求
        response = requests.get(calc_url, headers=headers, params=params)
        calc_result = get_response_json_with_check2(response)

        # 获取计算任务ID
        task_id = calc_result.get('id')
        if not task_id:
            raise Exception("计算接口未返回有效的任务ID")

        # 2. 轮询接口，每隔3秒一次，最多轮询10分钟
        polling_url = f"{client.base_url}/lib/common/v1/polling"
        max_polling_time = 10 * 60  # 10分钟
        polling_interval = 3  # 3秒
        start_time = time.time()

        while True:
            # 检查是否超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_polling_time:
                raise Exception(f"轮询超时，超过{max_polling_time}秒")

            # 发送轮询请求
            polling_params = {'id': task_id}
            polling_response = requests.get(polling_url, headers=headers, params=polling_params)
            polling_result = get_response_json_with_check2(polling_response)

            # 检查轮询结果
            if polling_result.get('error'):
                raise Exception(f"计算失败: {polling_result.get('errorMsg', '未知错误')}")

            if polling_result.get('complete'):
                final_result = polling_result.get('finalResult')
                if not final_result:
                    raise Exception("计算完成但未返回结果数据")

                # 3. 解析结果并转换为DataFrame
                # 初始化数据存储结构
                data_by_date_factor = {}

                # 定义数据类型与字段的映射关系
                data_mappings = [
                    ('portfolioReturn', 'accumulated_style_return'),
                    ('activeReturn', 'active_accumulated_style_return'),
                    ('portfolioWeight', 'style_exposure'),  # weight就是暴露
                    ('activeWeight', 'active_style_exposure')  # weight就是暴露
                ]

                # 处理所有数据类型
                for data_key, field_name in data_mappings:
                    data_list = final_result.get(data_key, [])
                    for item in data_list:
                        date = item.get('date')
                        factor_name = item.get('name')
                        factor_type = item.get('factorType')
                        value = item.get('value')

                        # 只处理风格因子
                        if factor_type != 'style':
                            continue

                        # 确保数据结构存在
                        key = (date, factor_name)
                        if key not in data_by_date_factor:
                            data_by_date_factor[key] = {
                                'date': date,
                                'style_factor': factor_name,
                                'style_exposure': 0.0,
                                'active_style_exposure': 0.0,
                                'accumulated_style_return': 0.0,
                                'active_accumulated_style_return': 0.0
                            }

                        # 设置对应字段的值
                        data_by_date_factor[key][field_name] = value

                # 转换为数据行列表
                rows = list(data_by_date_factor.values())

                # 转换为DataFrame
                df = pd.DataFrame(rows)

                # 按日期降序，因子名称降序排序
                df = df.sort_values(by=['date', 'style_factor'], ascending=[False, False])

                return df

            # 等待指定时间后继续轮询
            time.sleep(polling_interval)

    except Exception as e:
        raise e
