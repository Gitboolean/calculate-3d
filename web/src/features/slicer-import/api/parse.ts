import { useIsMutating, useMutation } from '@tanstack/react-query'

import { api, unwrap } from '@/shared/api'

const parseKey = ['slicer-import', 'parse'] as const

/** True while a file is being parsed, wherever the button that started it lives. */
export function useIsParsingSlicerFile() {
  return useIsMutating({ mutationKey: parseKey }) > 0
}

/**
 * Sends the slicer file as its raw bytes (ADR 0002): no JSON, no multipart. The generated type of
 * a `format: binary` body is `string`, so the File passes through an identity serializer.
 */
export function useParseSlicerFile() {
  return useMutation({
    mutationKey: parseKey,
    mutationFn: (file: File) =>
      unwrap(
        api.POST('/api/importing/parse', {
          body: file as unknown as string,
          bodySerializer: (body) => body,
          headers: { 'Content-Type': 'application/octet-stream' },
        }),
      ),
  })
}
