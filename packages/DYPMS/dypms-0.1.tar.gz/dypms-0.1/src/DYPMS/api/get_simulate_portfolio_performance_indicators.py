import requests
import pandas as pd
from .util import get_response_json_with_check

field_mapping = {
    'accountCode': 'simulate_portfolio_id',
    'benchmark': 'benchmark',
    'startDate': 'start_date',
    'endDate': 'end_date',
    'totalReturn': 'cumulative_return',
    'activeReturn': 'active_return',
    'latestWeekReturn': 'recent_week_return',
    'thisWeekReturn': 'weekly_return',
    'latestMonthReturn': 'recent_month_return',
    'thisMonthReturn': 'monthly_return',
    'ytdReturn': 'YTD_return',
    'annualTotalReturn': 'annualized_total_return',
    'annualActiveReturn': 'annualized_active_return',
    'annualTotalRisk': 'annualized_total_risk',
    'annualActiveRisk': 'annualized_active_risk',
    'maxDrawdown': 'maximum_drawdown',
    'sharpRatio': 'sharpe_ratio',
    'infoRatio': 'information_ratio',
    'sortinoRatio': 'sortino_ratio',
    'calmarRatio': 'calmar_ratio'
}


def get_simulate_portfolio_performance_indicators(client,
                                                  simulate_portfolio_id):
    """
    查询模拟组合业绩指标

    Args:
        client: DYPMS客户端实例
        simulate_portfolio_id: 模拟组合代码，必传
    """
    url = f"{client.base_url}/lib/simulate/portfolio/v1/perf"
    headers = client.get_headers()
    params = {'accountCode': simulate_portfolio_id}

    try:
        response = requests.get(url, headers=headers, params=params)
        r = get_response_json_with_check(response)

        # 转换单个对象为DataFrame
        data = r.get('data')
        if data:
            row = {}
            for api_field, our_field in field_mapping.items():
                row[our_field] = data.get(api_field, None)
            df = pd.DataFrame([row])
        else:
            df = pd.DataFrame()

        return df
    except Exception as e:
        raise e
