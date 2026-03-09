# 闲管家开放平台 - 查询卡密列表（归一化）

## 1. 用途
根据闲鱼订单号查询该订单关联的卡密列表，用于虚拟商品自动发货、卡密核销、对账及售后。

## 2. 请求路径方法
- **Base URL**: `https://open.goofish.pro`
- **Path**: `/api/open/order/kam/list`
- **Method**: `POST`
- **Content-Type**: `application/json`

## 3. 请求字段
| 字段名 | 类型 | 必填 | 说明 | 示例 |
|---|---|---|---|---|
| order_no | string | 是 | 闲鱼订单号 | `3364202298717566229` |

## 4. 返回字段
| 字段名 | 类型 | 说明 | 示例 |
|---|---|---|---|
| code | int | 业务状态码，`0` 表示成功 | 0 |
| msg | string | 状态说明 | OK |
| data.list | array\<object\> | 卡密列表 | 见下 |
| data.list[].card_no | string | 卡号 | - |
| data.list[].card_pwd | string | 卡密/密码 | - |
| data.list[].cost | int | 成本（单位：分） | 100 |
| data.list[].sold_type | int | 售出类型：11=自动发货，12=手动发货，21=手动提卡，22=手动标识已售 | 11 |

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
  1. `bodyMd5 = md5(POST原文JSON字符串)`
  2. `sign = md5("appKey,bodyMd5,timestamp,appSecret")`
- 商务对接变体：可追加 `seller_id` 参与签名。
- Base URL：`https://open.goofish.pro`

## 7. 幂等建议
- 读接口天然幂等。
- 建议以 `order_no` 作为缓存键，设置短 TTL 降低重复查询压力。

## 8. 重试建议
- 可重试：网络超时、网关 5xx、限流。
- 不可重试：参数错误、鉴权失败。
- 重试采用指数退避 + 随机抖动，最多 3 次。

## 9. 文档来源(raw_html_path)
- `raw_html_path`: 待补充
