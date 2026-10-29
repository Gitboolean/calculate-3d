import type { Problem } from './errors'

test('Problem extension members are typed from the generated schemas (S1-8)', () => {
  expectTypeOf<Problem['missing']>().toEqualTypeOf<('plastics' | 'price_settings')[] | undefined>()
})
