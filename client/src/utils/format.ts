/**
 * Format a price value (in cents/fen) as a Yuan string.
 *
 * Prices in the system are stored in cents (分), so we divide by 100
 * to display in yuan (元).
 */
export function formatPrice(price: number | string | null | undefined): string {
  const num = Number(price);
  if (!num || isNaN(num) || price === null || price === undefined) return '¥0.00';
  return `¥${(num / 100).toFixed(2)}`;
}
