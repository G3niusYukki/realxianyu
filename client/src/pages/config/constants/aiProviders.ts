export interface AIModel {
  value: string;
  label: string;
}

export interface AIProviderConfig {
  name: string;
  baseUrl: string;
  model: string;
  applyUrl: string;
  tip: string;
  models: AIModel[];
}

export const AI_PROVIDER_GUIDES: Record<string, AIProviderConfig> = {
  qwen: {
    name: '百炼千问 (Qwen)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus-latest',
    applyUrl: 'https://bailian.console.aliyun.com/',
    tip: '推荐。兼容 OpenAI 接口，中文电商场景最稳定。支持联网搜索和多模态。',
    models: [
      { value: 'qwen-plus-latest', label: 'Qwen-Plus（推荐，性价比高）' },
      { value: 'qwen-max-latest', label: 'Qwen-Max（最强推理）' },
      { value: 'qwen-turbo-latest', label: 'Qwen-Turbo（最快速度）' },
      { value: 'qwen-flash', label: 'Qwen-Flash（极速低成本）' },
      { value: 'qwen3-max', label: 'Qwen3-Max（Qwen3 旗舰）' },
      { value: 'qwen3.5-plus', label: 'Qwen3.5-Plus（最新一代）' },
      { value: 'qwq-plus-latest', label: 'QwQ-Plus（深度思考）' },
      { value: 'qwen3-coder-plus', label: 'Qwen3-Coder-Plus（代码优化）' },
      { value: 'qwen3-235b-a22b', label: 'Qwen3-235B（开源免费）' },
      { value: 'qwen3-32b', label: 'Qwen3-32B（开源免费）' },
    ],
  },
  deepseek: {
    name: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    applyUrl: 'https://platform.deepseek.com/',
    tip: '性价比高，长文本能力强，适合复杂商品描述场景。',
    models: [
      { value: 'deepseek-chat', label: 'DeepSeek-Chat（通用对话）' },
      { value: 'deepseek-reasoner', label: 'DeepSeek-Reasoner（深度推理）' },
    ],
  },
  openai: {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    applyUrl: 'https://platform.openai.com/',
    tip: '需海外网络，英文能力最强，中文电商场景建议搭配 System Prompt 优化。',
    models: [
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini（经济实惠）' },
      { value: 'gpt-4o', label: 'GPT-4o（强力多模态）' },
      { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini（最新轻量）' },
      { value: 'gpt-4.1', label: 'GPT-4.1（最新旗舰）' },
    ],
  },
};

export const AI_PROVIDERS = Object.entries(AI_PROVIDER_GUIDES).map(([id, config]) => ({
  id,
  label: config.name,
  model: config.model,
  base_url: config.baseUrl,
}));
