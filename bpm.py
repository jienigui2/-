import requests

def get_srdz_data_list(page_index=1, page_count=10):
    """
    获取 SRDZ 数据列表
    参数:
        page_index: 页码 (默认: 1)
        page_count: 每页数量 (默认: 10)
    返回: 包含数据的字典
    """
    url = "https://bpmmarket.atrust.sangfor.com/DataList/GetSRDZDataList?sf_request_type=ajax"
    
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://bpmmarket.atrust.sangfor.com",
        "priority": "u=1, i",
        "referer": "https://bpmmarket.atrust.sangfor.com/DataList/DZ_RJDZSRDataList",
        "sec-ch-ua": '"Not(A:Brand)";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": "wwrtx.i18n_lan=zh; ww_lang=cn,zh; sdp_app_session-legacy-443=8a51e68d3bb9146fec3d0c23ec761654d041fe88a22ac37c2b5c972ae0f2caf00faccf5d9d0f15216d9f57bf216db57035c129167217735f772e72cf7d08f8dc8226b9a0cdc0c6ee61698c4f4ad0a1a6556160da04390b8f1366c00313d0336c336fdece4c76bf82035e4ef187ae4460; sdp_app_session-443=8a51e68d3bb9146fec3d0c23ec761654d041fe88a22ac37c2b5c972ae0f2caf00faccf5d9d0f15216d9f57bf216db57035c129167217735f772e72cf7d08f8dc8226b9a0cdc0c6ee61698c4f4ad0a1a6556160da04390b8f1366c00313d0336c336fdece4c76bf82035e4ef187ae4460; sdp_user_token-legacy=ce55dc5e-2597-4ea4-9330-bbc369930e63_0e8821da-cd06-4aa2-968e-39a47893d394; sdp_user_token=ce55dc5e-2597-4ea4-9330-bbc369930e63_0e8821da-cd06-4aa2-968e-39a47893d394; LoginUserID=59272; WEBAUTH=EBC4493A976B08968EFB6C39CA484E4C9A73B2D4EE04D49D3BFB77E63B1B2ED0B1587665B73E5C9990F2B2F28F81F88D6E7658497CAA52E9063576AC658A03B5AF1F7FA875195F50524DC5CCE6255343F87CB16FC93C7D0C3ED2D0B1734C607622373A321B425BE630ECCCDEF554EB407788732DFDDEE2DDC303A9578AEFF2CC1BE637B1328D24A977255391200E86FA3B8B358878810ED426451DCE558496AA4C5E8E9663EC58D2727F539FF92A95549D29F87791C7C669A2055DAFB053765ADE839A318AB9F9456162E04BE3BAD1134FED54573A7532A86FE3D18E750466BCFCAACA7D4AD635D8DC2D9ADB288DAE81BA3584DD9D44DEBF5E536C326A7BFD0B8DC3299BAD87F624A903571D5327C271A23A175028A97F4CE67703C9E1C964D087D7B4706CC2FEDBE529A81E477CD12C2F947783D9D2E6D77F42B2394B7FD79BFD8E0FEADD97CE5C1CC1A89F2BD6E18984632C09523B2ED6E07B8D1F6A109FC56207B889F5F4C41C3B963310B01A3621C7009BDB3FC25180BEA042D33636891E7A722E669B8568EBCCCF59A4E5331F9F5E4AD343163314EC9143A9F2646C4212F20B7AA8B452FDA63A37A7CED33F0A12A3112DC8EA2DF0AE874044B810247C1C507AAF0DF45720A30D3455991A8554C07E0AD2C0095CDF7E7A8EBCD62AFF6D2D015247EABE6500B41BFBE83338A10DDA5058DDE8905671C7B0B0CEE0199F158D41101E76E721CDD7DC5568D2ECAF85EDB64DD9B580CAEC5CB3116758095673C72AA59A4B906AFFA45061A0CA9EBEBEADF16FE04FD0C800EC3A62F2C3DFEFE455D1B9FE4FB1A3C811941F6B385E0E53FE0225BCE95E2BCC606BC46F967CD5705346B3B4B07E59B0D917538907ABBA96AF41A6766E8197A3BD6FCF156D3952977EC7003CCB71D45F077E752E1896F691FD9AD9E7642DFBAE041DF209B3DCB171FDEDE1093B9A812F8E25363E4F36591B4D053B5566C8B695398F9434D8CCCDD749A472B8260CB5C3E8A92FD1C98FBC16C8938738910CB03FF7352345F561587D87; LoginUserTicket=8DCD8643E8481A78C506DAD1B59C4A2A82C4863844DF5D0B4EFE2CB3D94FD495163AB173FBB57F6BE500DF74A4FE8640398995F26B5C4876999360FDDEE1A5D8438EE45B0C1AAF37B742710C3D9BFB4E0AF0B5BE67AE1BA2B55D3A80DDD515BC058FF83B787988604B7FFBEB8C6468AC3F2539FEB8A58F78; __RequestVerificationToken=TPlmw0Hf9KJSq859OSzO5Z--62lBMggvtX6Pyj1ma4KNibMavwKizemGEfd8UGK4_lEGwafz4MH_zdxzenyUWN4erodwWwNkwo_N2zzkSt7WSnluFdh7yo-ZdMT9-wMbGzNKNRTPA_8ERKvZeWo6OA2; ep_jwt_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjU5MjcyIiwiZGlzcGxheV9uYW1lIjoiXHU4YzJkXHU0ZmNhXHU2NzcwNTkyNzIiLCJhY2Nlc3NfaXAiOiIxMC43Mi4xMC41MSIsImlhdCI6MTc2ODkwMTE0NSwiZXhwIjoxNzY5NTA1OTQ1LCJpc19hZG1pbiI6ZmFsc2UsImVtYWlsIjoiNTkyNzJAc2FuZ2Zvci5jb20ifQ.TkusoPI7GyWWR2g__wlllwXz2kSp_7aBZp1p6IOJpBE"
    }
    
    data = {
        "pageIndex": str(page_index),
        "pageCount": str(page_count),
        "CustomerName": "",
        "PrjName": "",
        "ApprovePoint": "",
        "AreaID": "",
        "CustomCode": "",
        "ProcessType": "RJDZSR",
        "PL": "",
        "ApproveStatus": "",
        "CustomType": "",
        "Applicant": "",
        "CurrentLoginName": "59272",
        "IsHandling": "false",
        "IsHandled": "false",
        "IsMine": "false",
        "BeginDate": "",
        "EndDate": "",
        "Sales": "",
        "txtrjdzdes": ""
    }
    
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def extract_custom_fields_with_guid(data):
    """
    提取定制单号、客户名称、申请人、GUID和EncryptProcInstID
    参数:
        data: 包含数据的字典
    返回: 提取的字段列表，每个元素包含GUID和EncryptProcInstID
    """
    extracted = []
    if data.get('content'):
        for item in data['content']:
            # 查找可能包含GUID的字段
            guid = item.get('GUID') or item.get('Guid') or item.get('guid')
            # 提取EncryptProcInstID字段
            encrypt_proc_inst_id = item.get('EncryptProcInstID')
            
            extracted.append({
                '定制单号': item.get('RjdzCode'),
                '客户名称': item.get('CusName'),
                '申请人': item.get('AddByName', item.get('UserName')),
                'GUID': guid,
                'EncryptProcInstID': encrypt_proc_inst_id
            })
    return extracted


def extract_guids(data):
    """
    提取所有记录的GUID
    参数:
        data: 包含数据的字典
    返回: GUID列表
    """
    guids = []
    if data.get('content'):
        for item in data['content']:
            # 查找可能包含GUID的字段
            guid = item.get('GUID') or item.get('Guid') or item.get('guid')
            if guid:
                guids.append(guid)
    return guids

if __name__ == "__main__":
    # 获取用户输入的记录数量
    try:
        count = int(input("请输入要提取的记录数量: "))
        if count <= 0:
            print("请输入大于0的数字")
            exit(1)
    except ValueError:
        print("请输入有效的数字")
        exit(1)
    
    # 获取数据（使用足够大的pageCount确保能获取到足够的数据）
    result = get_srdz_data_list(page_index=1, page_count=max(count, 50))
    print(f"总记录数: {result.get('total')}")
    print(f"返回记录数: {len(result.get('content', []))}")
    print(f"消息: {result.get('message')}")
    
    # 提取指定字段（包含GUID）
    extracted_fields = extract_custom_fields_with_guid(result)
    # 只取前count条记录
    extracted_fields = extracted_fields[:count]
    
    print(f"\n提取的前{count}条记录:")
    for i, item in enumerate(extracted_fields, 1):
        print(f"{i}. 定制单号: {item['定制单号']}, 客户名称: {item['客户名称']}, 申请人: {item['申请人']}, GUID: {item['GUID']}, EncryptProcInstID: {item['EncryptProcInstID']}")