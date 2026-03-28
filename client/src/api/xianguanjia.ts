import { api } from './index';
import type { AxiosResponse } from 'axios';
import type { ApiResponse } from './index';

// --- Product types ---

export interface ProductGoods {
  title?: string;
  images?: string[];
  [key: string]: unknown;
}

export interface ProductItem {
  product_id: string;
  title?: string;
  pic_url?: string;
  price?: number;
  stock?: number;
  status?: number;
  sold?: number;
  goods?: ProductGoods;
  [key: string]: unknown;
}

export interface ProductListResponse {
  list: ProductItem[];
  total?: number;
  page_no?: number;
  page_size?: number;
}

// --- Order types ---

export interface OrderGoods {
  title?: string;
  images?: string[];
  [key: string]: unknown;
}

export interface OrderItem {
  order_no?: string;
  order_id?: string;
  order_status?: number;
  order_time?: number | string;
  buyer_nick?: string;
  buyer_name?: string;
  title?: string;
  pic_url?: string;
  total_amount?: number;
  total_fee?: number;
  goods?: OrderGoods;
  [key: string]: unknown;
}

export interface OrderDetail {
  buyer_nick?: string;
  receiver_mobile?: string;
  prov_name?: string;
  city_name?: string;
  area_name?: string;
  town_name?: string;
  address?: string;
  waybill_no?: string;
  pay_time?: number | string;
  seller_remark?: string;
  total_amount?: number;
  pay_amount?: number;
  [key: string]: unknown;
}

export interface OrderListResponse {
  list: OrderItem[];
  total?: number;
  page_no?: number;
  page_size?: number;
}

// --- API functions ---

export const proxyXgjApi = (apiPath: string, payload?: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
  api.post('/xgj/proxy', { apiPath, payload });

export const getProducts = (pageNo = 1, pageSize = 20): Promise<AxiosResponse<ApiResponse<ProductListResponse>>> =>
  proxyXgjApi('/api/open/product/list', { page_no: pageNo, page_size: pageSize });

export const getOrders = (payload: Record<string, unknown>): Promise<AxiosResponse<ApiResponse<OrderListResponse>>> =>
  proxyXgjApi('/api/open/order/list', payload);

export const unpublishProduct = (productId: string): Promise<AxiosResponse<ApiResponse>> =>
  proxyXgjApi('/api/open/product/downShelf', { product_id: productId });

export const publishProduct = (productId: string): Promise<AxiosResponse<ApiResponse>> =>
  proxyXgjApi('/api/open/product/publish', { product_id: productId });
