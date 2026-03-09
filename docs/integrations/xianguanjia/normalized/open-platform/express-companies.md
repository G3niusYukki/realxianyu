# 闲管家开放平台 - 查询快递公司列表（归一化）

## 1. 用途
获取闲管家支持的快递公司列表，用于订单发货时选择 `express_code`、展示物流公司名称及热榜推荐。

## 2. 请求路径方法
- **Base URL**: `https://open.goofish.pro`
- **Path**: `/api/open/express/companies`
- **Method**: `POST`
- **Content-Type**: `application/json`

## 3. 请求字段
| 字段名 | 类型 | 必填 | 说明 | 示例 |
|---|---|---|---|---|
| （无请求体） | - | - | 本接口无请求体，可传 `{}` | {} |

## 4. 返回字段
| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 业务状态码，`0` 表示成功 | 0 |
| msg | string | 状态说明 | OK |
| data.list | array\<object\> | 快递公司列表 | 见下 |
| data.list[].code | string | 快递公司编码（发货时传入 express_code） | sf |
| data.list[].express_name | string | 快递公司名称 | 顺丰速运 |
| data.list[].express_alias | string | 快递公司别名 | - |
| data.list[].is_hot | int/bool | 是否热门/推荐 | 1 |

## 5. 错误码
| 错误码 | 含义 | 处理建议 |
|---|---|---|
| 0 | 成功 | 正常处理数据 |
| 非0 | 失败 | 记录 code/msg，按业务错误处理并人工排查 |

## 6. 签名规则
- 是否需要签名：**是**
- 参与字段：`appKey`、`bodyMd5`、`timestamp`、`appSecret`
- 算法：`MD5`
- 规则：
  1. `bodyMd5 = md5("{}")` 或 `md5(POST 原文 JSON 字符串)`，请求体与签名计算体必须一致
  2. `sign = md5("appKey,bodyMd5,timestamp,appSecret")`
- 商务对接变体：可追加 `seller_id` 参与签名。
- Base URL：`https://open.goofish.pro`

## 7. 幂等建议
- 读接口天然幂等。
- 建议本地缓存列表（如 TTL 24 小时），减少频繁请求。
- 发货前可用 `code` 校验是否在支持列表中。

## 8. 重试建议
- 可重试：网络超时、网关 5xx、限流。
- 不可重试：鉴权失败。
- 重试采用指数退避 + 随机抖动，最多 3 次。

## 9. 文档来源(raw_html_path)
- `raw_html_path`: 待补充
