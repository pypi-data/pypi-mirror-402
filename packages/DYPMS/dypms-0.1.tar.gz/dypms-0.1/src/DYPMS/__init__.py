from .client import Client

__all__ = ['Client']


def get_simulate_portfolio_list(*args, **kwargs):
    return Client.get_instance().get_simulate_portfolio_list(*args, **kwargs)


def get_simulate_portfolio_position(*args, **kwargs):
    return Client.get_instance().get_simulate_portfolio_position(*args, **kwargs)


def get_simulate_portfolio_position_hierarchy(*args, **kwargs):
    return Client.get_instance().get_simulate_portfolio_position_hierarchy(*args, **kwargs)


def get_simulate_portfolio_performance_indicators(*args, **kwargs):
    return Client.get_instance().get_simulate_portfolio_performance_indicators(*args, **kwargs)


def get_simulate_portfolio_net(*args, **kwargs):
    return Client.get_instance().get_simulate_portfolio_net(*args, **kwargs)


def get_style_attr_trend(*args, **kwargs):
    return Client.get_instance().get_style_attr_trend(*args, **kwargs)
