export interface PricingPreset {
  label: string;
  desc: string;
  min_margin_percent: number;
  max_discount_percent: number;
  auto_adjust: boolean;
}

export const PRICING_PRESETS: Record<string, PricingPreset> = {
  conservative: { 
    label: '保守定价', 
    desc: '高利润率，低降价幅度', 
    min_margin_percent: 20, 
    max_discount_percent: 10, 
    auto_adjust: false 
  },
  balanced: { 
    label: '均衡定价', 
    desc: '平衡利润与销量', 
    min_margin_percent: 10, 
    max_discount_percent: 20, 
    auto_adjust: true 
  },
  aggressive: { 
    label: '激进定价', 
    desc: '低利润率，高降价幅度，追求销量', 
    min_margin_percent: 5, 
    max_discount_percent: 35, 
    auto_adjust: true 
  },
};
