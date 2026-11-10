import { useRef, type ChangeEvent } from 'react'

import type { Schemas } from '@/shared/api'
import { Button } from '@/shared/ui'

import { useParseSlicerFile } from '../api/parse'
import { ImportRejection } from './ImportRejection'

/**
 * «Імпортувати файл»: picks a slicer file and hands its parse to `onParsed`. A rejection is shown
 * here and changes nothing (AC-06, AC-12…AC-14). Only the last chosen file counts: TanStack runs
 * a `mutate` call's own callbacks for the latest call only.
 */
export function ImportFileButton({
  onParsed,
}: {
  onParsed: (file: Schemas['SlicerFile']) => void
}) {
  const input = useRef<HTMLInputElement>(null)
  const parse = useParseSlicerFile()

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // the same file can be chosen again
    if (file) parse.mutate(file, { onSuccess: (parsed) => onParsed(parsed) })
  }

  return (
    <div className="space-y-3">
      <input
        ref={input}
        type="file"
        accept=".3mf"
        aria-label="Файл слайсера"
        className="sr-only"
        tabIndex={-1}
        onChange={choose}
      />
      <Button
        type="button"
        variant="outline"
        disabled={parse.isPending}
        onClick={() => input.current?.click()}
      >
        {parse.isPending ? 'Імпортую…' : 'Імпортувати файл'}
      </Button>
      {parse.isError && <ImportRejection error={parse.error} onManual={() => parse.reset()} />}
    </div>
  )
}
