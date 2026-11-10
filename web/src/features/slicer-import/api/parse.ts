import { useMutation } from '@tanstack/react-query'

import { api, unwrap } from '@/shared/api'

/**
 * Sends the slicer file as its raw bytes (ADR 0002): no JSON, no multipart. The generated type of
 * a `format: binary` body is `string`, so the File passes through an identity serializer.
 */
export function useParseSlicerFile() {
  return useMutation({
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
