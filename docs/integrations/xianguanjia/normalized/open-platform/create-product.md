# 创建商品（单个）

## method
`POST`

## path
`/api/open/product/create`

## 请求字段表

### Query 参数
| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| appid | string | 是 | 开放平台 AppKey |
| timestamp | string | 是 | 秒级时间戳，5 分钟有效 |
| sign | string | 是 | MD5 签名 |
| seller_id | string | 否 | 商家 ID（仅商务对接） |

### Body 参数（顶层）
| 字段名 | 类型 | 必填 | 说明 |
|---|---|---|---|
| item_biz_type | integer | 是 | 商品类型（2=闲置、0=二手、10=虚拟等） |
| sp_biz_type | integer | 是 | 商品行业 |
| channel_cat_id | string | 是 | 商品类目 ID（通过查询商品类目接口获取） |
| price | integer | 是 | 商品售价（分）。多规格时须为某个 SKU 金额 |
| express_fee | integer | 是 | 运费（分），0=包邮 |
| stock | integer | 是 | 商品库存（1-399960） |
| publish_shop | array[object] | 是 | 发布店铺列表，详见下方 |
| channel_pv | array[object] | 否 | 商品属性（通过查询商品属性接口获取） |
| original_price | integer | 否 | 商品原价（分）。item_biz_type=24 时必填 |
| stuff_status | string | 否 | 商品成色（1=全新、100=几乎全新等） |
| outer_id | string | 否 | 商家编码（1-64字符） |
| sku_items | array[object] | 否 | 多规格信息 |
| detail_images | array[string] | 否 | 详情图片 URL |
| book_data | object | 否 | 图书信息（图书类商品） |
| food_data | object | 否 | 食品信息（食品类商品） |
| report_data | object | 否 | 验货报告信息 |
| flash_sale_type | integer | 否 | 闲鱼特卖类型 |

### publish_shop[] 内部字段
| 字段名 | 类型 | 必填 | 说明 | 示例 |
|---|---|---|---|---|
| user_name | string | 是 | 闲鱼会员名 | tb924343042 |
| title | string | 是 | 商品标题（1-60字符，一个中文算2字符） | iPhone 12 128G 黑色 |
| content | string | 是 | 商品描述（5-5000字符，不支持 HTML，可用 \n 换行） | 全新未拆封，非诚勿扰~~ |
| images | array[string] | 是 | 商品图片 URL（第1张为主图，前9张发布到闲鱼） | ["https://..."] |
| province | integer | 是 | 发货省份行政区划编码 | 440000 |
| city | integer | 是 | 发货城市行政区划编码 | 440300 |
| district | integer | 是 | 发货地区行政区划编码 | 440305 |
| white_images | string | 否 | 白底图 URL。item_biz_type=24 时必填 | https://... |
| service_support | string | 否 | 商品服务（如 SDR） | SDR |

## 返回字段表
| 字段名 | 类型 | 说明 |
|---|---|---|
| code | int | 0 成功，非 0 失败 |
| msg | string | 状态描述 |
| data.product_id | int64 | 管家商品 ID |
| data.product_status | int | 管家商品状态 |

## 请求示例
```json
{
  "item_biz_type": 2,
  "sp_biz_type": 1,
  "channel_cat_id": "e11455b218c06e7ae10cfa39bf43dc0f",
  "price": 550000,
  "express_fee": 10,
  "stock": 10,
  "stuff_status": "100",
  "publish_shop": [
    {
      "user_name": "闲鱼会员名",
      "title": "商品标题",
      "content": "商品描述。",
      "images": ["https://xxx.com/xxx1.jpg", "https://xxx.com/xxx2.jpg"],
      "province": 130000,
      "city": 130100,
      "district": 130101,
      "service_support": "SDR"
    }
  ]
}
```

## 错误码
| 错误码 | 含义 | 处理建议 |
|---|---|---|
| 0 | 成功 | 正常处理业务结果。 |
| 400 | 参数错误/强校验失败 | 按字段类型与必填约束修正后重试。 |
| 401 | 签名错误或鉴权失败 | 重新计算签名并校准服务器时间。 |
| 429 | 请求过频 | 指数退避后重试。 |
| 500 | 服务内部错误 | 短暂重试；持续失败联系闲管家。 |

## 签名规则
- 使用 **MD5**。
- 先计算请求体原文的 `bodyMd5 = md5(bodyString)`。
- 普通对接签名串：`md5("appKey,bodyMd5,timestamp,appSecret")`。
- 商务对接（传 seller_id）签名串：`md5("appKey,bodyMd5,timestamp,seller_id,appSecret")`。

## 重要提示
- `item_biz_type`、`sp_biz_type`、`channel_cat_id` 存在依赖关系，务必传入正确。
- 创建为异步操作，最终结果以商品回调通知为准。
- `province`、`city`、`district` 为**整数行政区划编码**（如 440000），不是中文名称。
