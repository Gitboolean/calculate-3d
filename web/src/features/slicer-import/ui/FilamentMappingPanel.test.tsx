import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'

import type { Schemas } from '@/shared/api'
import { json, mockApi, renderWithProviders } from '@/shared/testing'

import { compose } from '../model/compose'
import { startImport, type ImportState } from '../model/state'
import { FilamentMappingPanel } from './FilamentMappingPanel'

afterEach(() => vi.unstubAllGlobals())

const PLA = 'Bambu PLA Basic @BBL A1M'
const PLASTICS = [
  { id: 'green', name: 'PLA зелений', price_per_kg_kop: 40000 },
  { id: 'black', name: 'PLA чорний', price_per_kg_kop: 40000 },
  { id: 'yellow', name: 'PLA жовтий', price_per_kg_kop: 40000 },
]

const filament = (
  filament_color: string,
  usage_mg: number,
  plastic_id: string | null,
  filament_name = PLA,
): Schemas['SlicerFilament'] => ({
  filament_name,
  filament_type: 'PLA',
  filament_color,
  usage_mg,
  plastic_id,
})

const LITTLE_TREES: Schemas['SlicerFile'] = {
  plate: { index: 1, name: 'mini christmas tree' },
  print_time_s: 5460,
  filaments: [
    filament('#3F8E43', 15490, 'green'),
    filament('#000000', 2230, 'black'),
    filament('#FEC600', 2360, null),
  ],
}

/** The page's role: hold the state and price only a ready composition. */
function Harness({ file }: { file: Schemas['SlicerFile'] }) {
  const [state, setState] = useState<ImportState>(() => startImport(file))
  const composition = compose(state.file, state.choice, state.confirmed)
  return (
    <>
      <FilamentMappingPanel state={state} onChange={setState} />
      <output aria-label="Рядки">
        {composition.kind === 'ready' ? JSON.stringify(composition.plastics) : composition.kind}
      </output>
    </>
  )
}

function renderPanel(file = LITTLE_TREES, plastics = PLASTICS) {
  mockApi({ 'GET /api/pricing/plastics': json({ items: plastics }) })
  return renderWithProviders(<Harness file={file} />)
}

test('shows the imported plate and each filament as the slicer wrote it (AC-02, AC-07)', async () => {
  renderPanel()

  expect(screen.getByText('Пластина 1 · mini christmas tree')).toBeInTheDocument()
  const row = (await screen.findByRole('row', { name: /#FEC600/ })) as HTMLElement
  expect(within(row).getByText(PLA)).toBeInTheDocument()
  expect(within(row).getByText('PLA')).toBeInTheDocument()
  expect(within(row).getByText('2,36 г')).toBeInTheDocument()
  expect(within(row).getByTestId('swatch')).toHaveStyle({ backgroundColor: '#FEC600' })
  expect(within(row).getByRole('combobox')).toHaveValue('')
})

test('a remembered plastic is preselected and marked as substituted', async () => {
  renderPanel()

  const green = (await screen.findByRole('row', { name: /#3F8E43/ })) as HTMLElement
  await vi.waitFor(() => expect(within(green).getByRole('combobox')).toHaveValue('green'))
  expect(within(green).getByText('підставлено з зіставлення')).toBeInTheDocument()
})

test('no rows are priced until every filament has a plastic (AC-09)', async () => {
  const user = userEvent.setup()
  renderPanel()

  expect(await screen.findByText(/Оберіть пластик для:.*#FEC600/)).toBeInTheDocument()
  expect(screen.getByLabelText('Рядки')).toHaveTextContent('unmapped')

  const yellow = (await screen.findByRole('row', { name: /#FEC600/ })) as HTMLElement
  await vi.waitFor(() => expect(within(yellow).getAllByRole('option')).toHaveLength(4))
  await user.selectOptions(within(yellow).getByRole('combobox'), 'yellow')

  expect(screen.getByLabelText('Рядки')).toHaveTextContent(
    JSON.stringify([
      { plastic_id: 'green', usage_cg: 1549 },
      { plastic_id: 'black', usage_cg: 223 },
      { plastic_id: 'yellow', usage_cg: 236 },
    ]),
  )
  expect(screen.queryByText(/Оберіть пластик для:/)).not.toBeInTheDocument()
})

test('no plastics yet: add one in the settings and upload the file again (AC-09b)', async () => {
  renderPanel(LITTLE_TREES, [])

  const hint = await screen.findByText(/Спершу додайте пластик у налаштуваннях цін/)
  expect(hint).toHaveTextContent(/завантажити знову/)
  expect(screen.getByRole('link', { name: 'Налаштування цін' })).toHaveAttribute(
    'href',
    '/settings',
  )
})

test('two different filaments on one plastic ask before summing (AC-10)', async () => {
  const user = userEvent.setup()
  renderPanel({
    ...LITTLE_TREES,
    filaments: [filament('#3F8E43', 2001, 'green'), filament('#000000', 2001, 'green')],
  })

  const dialog = await screen.findByRole('alertdialog')
  expect(within(dialog).getByText(/#3F8E43/)).toBeInTheDocument()
  expect(within(dialog).getByText(/#000000/)).toBeInTheDocument()
  expect(screen.getByLabelText('Рядки')).toHaveTextContent('merge-conflict')

  await user.click(within(dialog).getByRole('button', { name: 'Сумувати' }))

  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  expect(screen.getByLabelText('Рядки')).toHaveTextContent(
    JSON.stringify([{ plastic_id: 'green', usage_cg: 401 }]),
  )
})

test('choosing another plastic instead closes the question until it is resolved', async () => {
  const user = userEvent.setup()
  renderPanel({
    ...LITTLE_TREES,
    filaments: [filament('#3F8E43', 1000, 'green'), filament('#000000', 2000, 'green')],
  })

  await user.click(
    within(await screen.findByRole('alertdialog')).getByRole('button', {
      name: 'Обрати інший пластик',
    }),
  )
  expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  expect(screen.getByText(/ведуть до одного пластику/)).toBeInTheDocument()

  const black = screen.getByRole('row', { name: /#000000/ })
  await user.selectOptions(within(black).getByRole('combobox'), 'black')

  expect(screen.getByLabelText('Рядки')).toHaveTextContent(
    JSON.stringify([
      { plastic_id: 'green', usage_cg: 100 },
      { plastic_id: 'black', usage_cg: 200 },
    ]),
  )
})

test('a markup-like filament name is plain text (PRD §6.1)', async () => {
  const name = '<img src=x onerror=alert(1)>'
  renderPanel({ ...LITTLE_TREES, filaments: [filament('#FFFFFF', 1000, 'green', name)] })

  expect(await screen.findByText(name)).toBeInTheDocument()
  expect(document.querySelector('img')).toBeNull()
})

test('a plate without a name shows only its number', () => {
  renderPanel({ ...LITTLE_TREES, plate: { index: 1, name: '' } })

  expect(screen.getByText('Пластина 1')).toBeInTheDocument()
})
