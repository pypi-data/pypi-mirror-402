
def get_response_json_with_check(response):
    if response.status_code != 200:
        response.raise_for_status()
    r = response.json()
    if r.get('code') == -403:
        raise Exception("token认证失败")
    if r.get('code') != 'S00000':
        raise Exception(r.get('message'))
    return r


# 仅校验http状态码，不校验业务状态码（适用于比较老的接口）
def get_response_json_with_check2(response):
    if response.status_code != 200:
        response.raise_for_status()
    return response.json()
