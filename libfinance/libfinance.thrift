struct St_Query_Req {
    1:required string api_name,
    2:required binary params,
}

struct St_Query_Rsp {
    1:required bool status,
    2:optional string msg,
    3:optional binary result
}

service LibfinanceService {
    St_Query_Rsp query(1:St_Query_Req request),
    St_Query_Rsp auth(1:string username, 2:string password)//, 5:bool compress, 8:string mac, 10:string version),
    St_Query_Rsp auth_by_token(1: string token)
}