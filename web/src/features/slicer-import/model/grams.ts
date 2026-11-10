import { formatDecimal } from '@/shared/lib'

/** Exact milligrams as the slicer shows grams: 11 540 → «11,54 г», 11 543 → «11,543 г». */
export function formatMg(usageMg: number): string {
  return `${formatDecimal(usageMg, 3).replace(/0+$/, '').replace(/,$/, '')} г`
}
