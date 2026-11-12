import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import type { Schemas } from '@/shared/api'
import { json, mockApi, problem, renderWithProviders } from '@/shared/testing'

import { ImportFileButton } from './ImportFileButton'

afterEach(() => vi.unstubAllGlobals())

const PARSED: Schemas['SlicerFile'] = {
  plate: { index: 1, name: '' },
  print_time_s: 5880,
  filaments: [
    {
      filament_name: 'Bambu PLA Basic @BBL A1M',
      filament_type: 'PLA',
      filament_color: '#FFFFFF',
      usage_mg: 11540,
      plastic_id: 'pla',
    },
  ],
}

function slicerFile(name = 'vtulka_A.gcode.3mf', bytes = [0x50, 0x4b, 3, 4, 9]) {
  return new File([new Uint8Array(bytes)], name, { type: '' })
}

test('the chosen file is sent as its raw bytes in an octet-stream body (ADR 0002)', async () => {
  const api = mockApi({ 'POST /api/importing/parse': json(PARSED) })
  const onParsed = vi.fn()
  renderWithProviders(<ImportFileButton onParsed={onParsed} />)

  await userEvent.upload(screen.getByLabelText('Файл слайсера'), slicerFile())

  await vi.waitFor(() => expect(onParsed).toHaveBeenCalledWith(PARSED))
  const [call] = api.callsTo('POST', '/api/importing/parse')
  expect(call?.contentType).toBe('application/octet-stream')
  expect(call?.body).toEqual(new Uint8Array([0x50, 0x4b, 3, 4, 9]))
})

test('the button opens the file picker for .3mf files', () => {
  renderWithProviders(<ImportFileButton onParsed={vi.fn()} />)

  expect(screen.getByRole('button', { name: 'Імпортувати файл' })).toBeEnabled()
  expect(screen.getByLabelText('Файл слайсера')).toHaveAttribute('accept', '.3mf')
})

test('a rejected file is explained, nothing is passed on, and manual entry dismisses it', async () => {
  mockApi({ 'POST /api/importing/parse': problem(422, 'importing.not_sliced') })
  const onParsed = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<ImportFileButton onParsed={onParsed} />)

  await user.upload(screen.getByLabelText('Файл слайсера'), slicerFile('vtulka_A.3mf'))

  expect(await screen.findByRole('alert')).toHaveTextContent('Файл не нарізаний')
  await user.click(screen.getByRole('button', { name: 'Ввести вручну' }))
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(onParsed).not.toHaveBeenCalled()
})

test('only the last chosen file fills the form when answers arrive out of order', async () => {
  let release: (() => void) | undefined
  const slow = new Promise<void>((resolve) => (release = resolve))
  const newer = { ...PARSED, print_time_s: 60 }
  mockApi({
    'POST /api/importing/parse': async (call) => {
      if ((call.body as Uint8Array)[4] === 1) {
        await slow
        return json(PARSED)
      }
      return json(newer)
    },
  })
  const onParsed = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<ImportFileButton onParsed={onParsed} />)
  const input = screen.getByLabelText('Файл слайсера')

  await user.upload(input, slicerFile('old.3mf', [0x50, 0x4b, 3, 4, 1]))
  await user.upload(input, slicerFile('new.3mf', [0x50, 0x4b, 3, 4, 2]))
  await vi.waitFor(() => expect(onParsed).toHaveBeenCalledWith(newer))
  release?.()
  await new Promise((r) => setTimeout(r, 20))

  expect(onParsed).toHaveBeenCalledTimes(1)
})

// Mirrors MAX_BODY_BYTES in backend/src/calculate3d/modules/importing/router.py (AC-13).
const MAX_FILE_BYTES = 100_000_000

function fileOfSize(size: number) {
  const file = slicerFile('big.3mf')
  Object.defineProperty(file, 'size', { value: size })
  return file
}

test('a file over 100 MB is rejected in the browser with the size explanation and never uploaded', async () => {
  const api = mockApi({ 'POST /api/importing/parse': json(PARSED) })
  const onParsed = vi.fn()
  const user = userEvent.setup()
  renderWithProviders(<ImportFileButton onParsed={onParsed} />)

  await user.upload(screen.getByLabelText('Файл слайсера'), fileOfSize(MAX_FILE_BYTES + 1))

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Файл більший за 100 МБ — такий файл не імпортується.',
  )
  expect(api.callsTo('POST', '/api/importing/parse')).toHaveLength(0)
  expect(onParsed).not.toHaveBeenCalled()
})

test('a file of exactly 100 MB is still sent', async () => {
  const api = mockApi({ 'POST /api/importing/parse': json(PARSED) })
  const onParsed = vi.fn()
  renderWithProviders(<ImportFileButton onParsed={onParsed} />)

  await userEvent.upload(screen.getByLabelText('Файл слайсера'), fileOfSize(MAX_FILE_BYTES))

  await vi.waitFor(() => expect(onParsed).toHaveBeenCalledWith(PARSED))
  expect(api.callsTo('POST', '/api/importing/parse')).toHaveLength(1)
})
