from .api.heartbeat import heartbeat
from .api.get_simulate_portfolio_list import get_simulate_portfolio_list
from .api.get_simulate_portfolio_position import get_simulate_portfolio_position
from .api.get_simulate_portfolio_position_hierarchy import get_simulate_portfolio_position_hierarchy
from .api.get_simulate_portfolio_performance_indicators import get_simulate_portfolio_performance_indicators
from .api.get_simulate_portfolio_net import get_simulate_portfolio_net
from .api.get_style_attr_trend import get_style_attr_trend


class Client:

    _instance = None

    def __init__(self, token='', env='prd'):
        self.token = token
        if env == 'prd':
            self.base_url = "https://gw.datayes.com/aladdin_mof"
        elif env == 'qa':
            self.base_url = "https://gw.datayes-stg.com/mom_aladdin_qa"
        elif env == 'stg':
            self.base_url = "https://gw.datayes-stg.com/mom_aladdin_stg"
        else:
            raise ValueError("error env")
        heartbeat(self)
        Client._instance = self

    @staticmethod
    def get_instance():
        if Client._instance is None:
            raise RuntimeError("Client未初始化，请先实例化Client")
        return Client._instance

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }


Client.get_simulate_portfolio_list = get_simulate_portfolio_list
Client.get_simulate_portfolio_position = get_simulate_portfolio_position
Client.get_simulate_portfolio_position_hierarchy = get_simulate_portfolio_position_hierarchy
Client.get_simulate_portfolio_performance_indicators = get_simulate_portfolio_performance_indicators
Client.get_simulate_portfolio_net = get_simulate_portfolio_net
Client.get_style_attr_trend = get_style_attr_trend
