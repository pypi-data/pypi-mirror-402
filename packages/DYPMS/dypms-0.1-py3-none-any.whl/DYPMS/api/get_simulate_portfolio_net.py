import requests
import pandas as pd
from .util import get_response_json_with_check

field_mapping = {
    'date': '净值日期',
    'unitNav': '单位净值',
    'accumNav': '累计净值',
    'adjustNav': '复权净值'
}


def get_simulate_portfolio_net(client,
                               simulate_portfolio_id,
                               start_date,
                               end_date):
    """
    查询模拟组合净值

    Args:
        client: DYPMS客户端实例
        simulate_portfolio_id: 模拟组合代码，必传
        start_date: 开始日期，必传
        end_date: 结束日期，必传
    """
    url = f"{client.base_url}/lib/simulate/portfolio/v1/nav"
    headers = client.get_headers()
    params = {
        'accountCode': simulate_portfolio_id,
        'startDate': start_date,
        'endDate': end_date
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        r = get_response_json_with_check(response)

        rows = []
        for item in r.get('list'):
            row = {}
            for api_field, our_field in field_mapping.items():
                row[our_field] = item.get(api_field, None)
            rows.append(row)

        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        raise e
