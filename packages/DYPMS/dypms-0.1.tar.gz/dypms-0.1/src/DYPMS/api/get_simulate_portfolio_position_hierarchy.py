import requests
import pandas as pd
from .util import get_response_json_with_check

field_mapping = {
    'symbol': 'symbol',
    'symbolName': 'symbol_name',
    'securityId': 'security_id',
    'exchangeCd': 'exchange_code',
    'channel': 'channel',
    'ticker': 'ticker',
    'mdSecurityId': 'md_security_id',
    'securityType': 'security_type',
    'positionDate': 'position_date',
    'direction': 'direction',

    'value': 'market_value',
    'positionValue': 'position_value',
    'closePrice': 'close_price',
    'amount': 'quantity',
    'canSellQuantity': 'available_sell_quantity',
    'totalBuyCost': 'total_buy_cost',
    'buyCost': 'buy_cost',
    'cost': 'holding_cost',
    'profit': 'realized_profit',
    'dailyProfitValue': 'daily_pnl_value',
    'dailyProfitRate': 'daily_pnl_rate',
    'floatingProfitValue': 'unrealized_pnl_value',
    'floatingProfitRate': 'unrealized_pnl_rate',
    'cumulativeProfitValue': 'cumulative_pnl_value',
    'cumulativeProfitRate': 'cumulative_pnl_rate',
    'cumulativeProfitRateTw': 'cumulative_pnl_rate_tw',  # TW 可能指 Time-Weighted
    'weight': 'weight',
    'coveredQuantity': 'covered_quantity',
    'buyCostHke': 'buy_cost_hke',
    'costHke': 'holding_cost_hke',
    'orgBuyCost': 'original_buy_cost',
    'orgCost': 'original_holding_cost',
    'margin': 'margin',
    'dueDate': 'due_date',
    'aiRate': 'accrued_interest_rate',
    'netPrice': 'net_price',
    'positionTime': 'position_time',
    'changePct': 'price_change_pct',
    'partialWeight': 'partial_weight',
    'marginWeight': 'margin_weight',
    'netPricePnlRate': 'net_price_pnl_rate',
    'fundReportDate': 'fund_report_date',
    'includeFofPerspective': 'include_fof_perspective',
    'category1': 'category_level_1',
    'category2': 'category_level_2',
    'cumulativeDividendValue': 'cumulative_dividend_value',
    'freezeAllotCash': 'frozen_allotment_cash',
    'receivableShareAmount': 'receivable_shares',
    'receivableDividendValue': 'receivable_dividend_value',
    'informationId': 'information_id',
    'positionReason': 'position_reason',
    'firstHoldingDate': 'first_holding_date',
    'transCurrCd': 'transaction_currency_code',
    'fxRate': 'exchange_rate',
}


def get_simulate_portfolio_position_hierarchy(client,
                                              simulate_portfolio_id,
                                              date):
    """
    查询模拟组合持仓平铺

    Args:
        client: DYPMS客户端实例
        simulate_portfolio_id: 模拟组合代码，必传
        date: 特定日期，必传
    """
    url = f"{client.base_url}/lib/simulate/portfolio/v1/positionHierarchy"
    headers = client.get_headers()

    data = {
        'accountCode': simulate_portfolio_id,
        'date': date
    }

    try:
        response = requests.post(url, headers=headers, json=data)
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
