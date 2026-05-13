from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

@export_as_api
def login(username, password):
    return get_client().login(username=username,password=password)