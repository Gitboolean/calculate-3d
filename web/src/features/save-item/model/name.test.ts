import { ApiError } from '@/shared/api'

import { saveError, validateItemName } from './name'

const TOO_LONG = 'Назва — не довше 100 символів'

test('an item name of 100 emoji (100 code points, 200 UTF-16 units) is accepted (AC-11)', () => {
  expect(validateItemName('😀'.repeat(100))).toBeUndefined()
})

test('an item name of 101 emoji is rejected as too long (AC-11)', () => {
  expect(validateItemName('😀'.repeat(101))).toBe(TOO_LONG)
})

test('an item name that NFC-expands past 100 code points is rejected as too long (AC-11)', () => {
  expect(validateItemName('̈́'.repeat(60))).toBe(TOO_LONG)
})

test('a server 422 on name says the length range, not "required" (AC-11)', () => {
  const error = new ApiError(422, {
    type: 'about:blank',
    title: 'Validation error',
    status: 422,
    detail: 'Invalid request',
    code: 'validation_error',
    errors: [{ loc: ['body', 'name'], msg: 'String should have at most 100 characters' }],
  })

  expect(saveError(error).name).toBe('Назва — від 1 до 100 символів')
})
