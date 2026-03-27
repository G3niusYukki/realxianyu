import { api } from './index';
import type { AxiosResponse } from 'axios';
import type { ApiResponse } from './index';

export interface AccountInfo {
  user_id: string;
  nick_name: string;
  avatar_url?: string;
  cookie_valid?: boolean;
  last_checked?: string;
}

export const getAccounts = (): Promise<AxiosResponse<ApiResponse<AccountInfo[]>>> =>
  api.get('/accounts');
