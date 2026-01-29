"""
商家规则群，是否能够直接根据商家匹配出购买的账户
"""

payee_rules_payee = [
    ("keyword", "RACKNERD", "Racknerd", "VPS", "Expenses:Tech:Subscriptions"),
    ("keyword", "iCloud", "Apple", "iCloud", "Expenses:Tech:Subscriptions"),
    ("keyword", "App Store & Apple Music", "Apple", "", "Expenses:Tech:Software"),
    ("keyword", "NameSilo", "NameSilo", "Domain", "Expenses:Tech:Subscriptions"),
    ("keyword", "mayproxy", "cliproxy", "住宅IP", "Expenses:Tech:Subscriptions"),
    ("keyword", "中国移动", "中国移动", "话费", "Expenses:Utilities:Phone"),
    ("keyword", "淘宝闪购", "淘宝闪购", "", "handle_commerce"),
    ("keyword", "拼多多", "拼多多", "", "handle_commerce"),
    ("keyword", "美团", "美团", "", "handle_commerce"),
    ("keyword", "知乎", "知乎", "知乎问答", "Expenses:Tech:Subscriptions"),
    ("keyword", "益禾堂", "益禾堂", "奶茶", "Expenses:Food:Snacks"),
    ("regex", r"万德隆", "origin", "", "handle_supermarket"),
    ("regex", r"宋捷|捷", "origin", "", "Assets:Receivables:SongJie"),
    (
        "regex",
        r"面|华莱士|米|饼|三色鸽|麻辣烫|杨国福|美味|拌饭|炒饭|盖饭|烩饭|饭先森",
        "origin",
        "",
        "Expenses:Food:ThreeMeals",
    ),
    (
        "regex",
        r"理发|美发|剪发|烫染|造型|快剪|美容|护肤|化妆|洗面奶|沐浴露|洗发水|剃须",
        "origin",
        "",
        "Expenses:Personal:Grooming",
    ),
    (
        "regex",
        r"零食|一鸣|鸣趣|便利店|怡家|河南省南阳市宛城区建设路店",
        "origin",
        "",
        "Expenses:Food:Snacks",
    ),
    (
        "regex",
        r"出行|滴滴|滴滴出行|打车|滴滴打车",
        "origin",
        "",
        "Expenses:Transport:General",
    ),
    (
        "regex",
        r"湖北省澄泞盼蓄科技有限公司|衢州市胥郢",
        "机场",
        "vpn",
        "Expenses:Tech:Subscriptions",
    ),
]

"""
商品规则群
如果没有根据商家规则群匹配出，那么进入此规则，根据此规则匹配出账户
"""
commodity_rules_payee = [
    # --- 1. 娱乐订阅 (注意：Apple Music 要放在 Tech 订阅之前，防止被 Apple 抢答) ---
    (
        "regex",
        r"(?i)Netflix|Spotify|YouTube|Disney|Bilibili|大会员|爱奇艺|腾讯视频|优酷|芒果TV|网易云|QQ音乐|Apple\s*Music",
        "SubscriptionService",
        "Expenses:Entertainment:Subscriptions",
    ),
    (
        "regex",
        r"(?i)六趣|66rpg|鲜花|元宝|点券|皮肤|王者荣耀|充值",
        "Game",
        "Expenses:Entertainment:Subscriptions",
    ),
    # --- 2. 科技与订阅 ---
    (
        "regex",
        r"(?i)App\s*Store|Play\s*Store|Microsoft|Adobe|JetBrains|Steam|游戏购买|软件|授权|激活码",
        "SoftwareVendor",
        "Expenses:Tech:Software",
    ),
    (
        "regex",
        r"(?i)iCloud|Apple|Google\s*One|AWS|阿里云|腾讯云|NameSilo|Godaddy|RackNerd|RACKNERD|ChatGPT|OpenAI|Copilot|Midjourney|Notion|Relingo|mayproxy|cliproxy|VPN|梯子|域名|Domain|VPS|服务器|IP",
        "TechService",
        "Expenses:Tech:Subscriptions",
    ),
    # --- 3. 饮食 (三餐) ---
    (
        "regex",
        r"(?i)饿了么|美团|外卖|麦当劳|肯德基|KFC|必胜客|汉堡|炸鸡|星巴克|瑞幸|咖啡|Coffee|茶|奶茶|华莱士|三色鸽|麻辣烫|杨国福|美味|面|粉|饭|冒菜|烧烤|火锅|料理|早餐|午餐|晚餐|食堂|拌饭|三餐",
        "Restaurant",
        "Expenses:Food:ThreeMeals",
    ),
    # --- 4. 杂货 (超市/零食) ---
    (
        "regex",
        r"(?i)杂货|超市|便利店|万德隆|永辉|沃尔玛|盒马|7-11|全家|罗森|美宜佳|零食|皇栗皇|水果|生鲜|牛奶|酸奶|饮料|饼干|面包|米|油|调料",
        "GroceryStore",
        "Expenses:Food:Groceries",
    ),
    # --- 5. 居家日用 ---
    (
        "regex",
        r"(?i)宜家|名创优品|文具|日用|百货|杂货|纸巾|抽纸|卷纸|湿巾|洗衣|洗洁精|消毒|垃圾袋|电池|插座|桌子|除臭",
        "HouseholdStore",
        "Expenses:Household:General",
    ),
    # --- 6. 通讯话费 ---
    (
        "regex",
        r"(?i)话费|中国移动|中国联通|中国电信|流量",
        "Telecom",
        "Expenses:Utilities:Phone",
    ),
    # --- 7. 健康保健 ---
    (
        "regex",
        r"(?i)维生素|钙|鱼油|蛋白粉|益生菌|多特倍斯|doctorsbest|Swisse|汤臣倍健|药|胶囊|钙片|维生素片|含片",
        "Pharmacy",
        "Expenses:Health:Supplements",
    ),
    # --- 8. 个人仪容 ---
    (
        "regex",
        r"(?i)理发|美发|剪发|烫染|造型|快剪|美容|护肤|化妆|洗面奶|沐浴露|洗发水|剃须",
        "BeautyShop",
        "Expenses:Personal:Grooming",
    ),
    # --- 9. 出行 ---
    (
        "regex",
        r"出行|滴滴|滴滴出行|打车|滴滴打车|共享单车",
        "Transport",
        "Expenses:Transport:General",
    ),
]


"""
账户规则
"""
payment_method_rules = {
    "工商银行信用卡(8393)": "Liabilities:CreditCard:ICBC-8393",
    "工商银行信用卡(8393)&工商银行立减金": "Liabilities:CreditCard:ICBC-8393",
    "工商银行信用卡(8393)&工商银行立减": "Liabilities:CreditCard:ICBC-8393",
    "工商银行信用卡(8393)&到店支付立减券": "Liabilities:CreditCard:ICBC-8393",
    "中国工商银行储蓄卡(4931)": "Assets:Bank:ICBC-4931 ",
    "工商银行储蓄卡(4931)": "Assets:Bank:ICBC-4931 ",
    "花呗": "Liabilities:CreditCard:HuaBei",
    "花呗&到店支付立减券": "Liabilities:CreditCard:HuaBei",
    "花呗&红包": "Liabilities:CreditCard:HuaBei",
    "余额宝": "Assets:EWallet:Alipay:YuEBao",
    "余额宝&门店消费券": "Assets:EWallet:Alipay:YuEBao",
    "账户余额": "Assets:EWallet:Alipay:Bience",
    "未知": "Liabilities:unknow:account",
}

"""
收益规则
"""
invest_rules = [
    ("regex", r"(?i)余额宝-[0-9]", "income", "Income:CN:Interest:YuEBao"),
]

repay_rules = [
    ("regex", r"(?i)花呗.*还款", "repay", "Liabilities:CreditCard:HuaBei"),
    ("regex", r"(?i)信用卡还款", "repay", "Liabilities:CreditCard:ICBC-8393"),
]

transfer_rules = [
    ("regex", r"(?i)余额宝-.*转入", "transfer_into", "Assets:EWallet:Alipay:YuEBao"),
    ("regex", r"(?i)余额宝-.*转出", "transfer_out", "Assets:EWallet:Alipay:YuEBao"),
]


refund_rules = [
    ("regex", r"(?i)退款", "refund"),
]
