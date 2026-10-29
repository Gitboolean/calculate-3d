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
