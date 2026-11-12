import { useRef, useState, type ChangeEvent } from 'react'

import { ApiError, type Schemas } from '@/shared/api'
import { Button } from '@/shared/ui'

import { useParseSlicerFile } from '../api/parse'
import { MAX_FILE_BYTES } from '../model/limits'
import { ImportRejection } from './ImportRejection'

const TOO_LARGE = new ApiError(413, {
  type: 'about:blank',
  title: 'Payload Too Large',
  status: 413,
  detail: 'File too large',
  code: 'importing.file_too_large',
})

/**
 * «Імпортувати файл»: picks a slicer file and hands its parse to `onParsed`. A rejection is shown
 * here and changes nothing (AC-06, AC-12…AC-14). Only the last chosen file counts: TanStack runs
 * a `mutate` call's own callbacks for the latest call only.
 */
export function ImportFileButton({
  onParsed,
  disabled = false,
}: {
  onParsed: (file: Schemas['SlicerFile']) => void
  /** The screen is busy elsewhere, e.g. saving: a new import would swap the file under it. */
  disabled?: boolean
}) {
  const input = useRef<HTMLInputElement>(null)
  const parse = useParseSlicerFile()
  const [tooLarge, setTooLarge] = useState(false)

  function choose(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // the same file can be chosen again
    if (!file) return
    if (file.size > MAX_FILE_BYTES) {
      parse.reset()
      setTooLarge(true)
      return
    }
    setTooLarge(false)
    parse.mutate(file, { onSuccess: (parsed) => onParsed(parsed) })
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
        disabled={disabled || parse.isPending}
        onClick={() => input.current?.click()}
      >
        {parse.isPending ? 'Імпортую…' : 'Імпортувати файл'}
      </Button>
      {tooLarge ? (
        <ImportRejection error={TOO_LARGE} onManual={() => setTooLarge(false)} />
      ) : (
        parse.isError && <ImportRejection error={parse.error} onManual={() => parse.reset()} />
      )}
    </div>
  )
}
