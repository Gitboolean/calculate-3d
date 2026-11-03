const uah = new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH' })

/** Kopecks from the API → «115,25 ₴». Display only: no arithmetic happens on the result. */
export function formatMoney(kop: number): string {
  return uah.format(kop / 100)
}
