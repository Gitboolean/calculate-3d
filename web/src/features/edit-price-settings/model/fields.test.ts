import { validate, type FieldName, type FieldValues } from './fields'

const SEP = '[\\s  ]?'
const num = (...groups: string[]) => new RegExp(groups.join(SEP))

const VALID: FieldValues = {
  tariff_per_kwh_kop: '4,32',
  printer_power_w: '150',
  printer_price_kop: '20000',
  printer_lifetime_h: '5000',
  parts_per_hour_kop: '1,50',
  scrap_rate_permille: '5,0',
}

test.each<[FieldName, string, string, string[]]>([
  ['tariff_per_kwh_kop', '10000', '10000,01', ['10', '000']],
  ['printer_power_w', '1000000', '1000001', ['1', '000', '000']],
  ['printer_price_kop', '100000000', '100000000,01', ['100', '000', '000']],
  ['printer_lifetime_h', '1000000', '1000001', ['1', '000', '000']],
  ['parts_per_hour_kop', '1000000', '1000000,01', ['1', '000', '000']],
])(
  '%s: the cap is accepted, one unit over is rejected naming the maximum (AC-05)',
  (field, atCap, over, groups) => {
    expect(validate({ ...VALID, [field]: atCap }).ok).toBe(true)

    const result = validate({ ...VALID, [field]: over })
    expect(result.ok).toBe(false)
    if (result.ok) return
    expect(result.errors[field]).toMatch(num(...groups))
  },
)

const RULE: Record<FieldName, string> = {
  tariff_per_kwh_kop: 'Тариф — від 0 до 10 000 ₴ за кВт·год з точністю до копійки',
  printer_power_w: 'Потужність — ціле число ват від 0 до 1 000 000',
  printer_price_kop: 'Ціна принтера — від 0 до 100 000 000 ₴ з точністю до копійки',
  printer_lifetime_h: 'Термін служби — ціле число годин від 1 до 1 000 000',
  parts_per_hour_kop: 'Деталі — від 0 до 1 000 000 ₴ за годину з точністю до копійки',
  scrap_rate_permille: 'Брак — від 0 до 100 % з точністю до 0,1',
}

test.each<[FieldName, string]>([
  ['tariff_per_kwh_kop', ''],
  ['tariff_per_kwh_kop', 'abc'],
  ['tariff_per_kwh_kop', '4,321'],
  ['tariff_per_kwh_kop', '-1'],
  ['tariff_per_kwh_kop', '10000,01'],
  ['tariff_per_kwh_kop', '1' + '0'.repeat(20)],
  ['printer_power_w', ''],
  ['printer_power_w', '1,5'],
  ['printer_power_w', '1000001'],
  ['printer_power_w', '1' + '0'.repeat(20)],
  ['printer_price_kop', '100000000,01'],
  ['printer_price_kop', '1' + '0'.repeat(20)],
  ['printer_lifetime_h', '0'],
  ['printer_lifetime_h', '1000001'],
  ['printer_lifetime_h', '1' + '0'.repeat(20)],
  ['parts_per_hour_kop', '-1'],
  ['parts_per_hour_kop', '1000000,01'],
  ['parts_per_hour_kop', '1' + '0'.repeat(20)],
  ['scrap_rate_permille', '100,1'],
  ['scrap_rate_permille', '1' + '0'.repeat(20)],
])('%s: %j is rejected with the one rule stating range and precision (AC-05)', (field, bad) => {
  const result = validate({ ...VALID, [field]: bad })

  expect(result.ok).toBe(false)
  if (result.ok) return
  expect(result.errors[field]).toBe(RULE[field])
})
