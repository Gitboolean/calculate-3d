// Test-only fake of the HTTP API: routes are 'METHOD /path' → handler; every call is recorded.

export type ApiCall = {
  method: string
  path: string
  search: string
  contentType: string | null
  /** Parsed JSON, or the raw bytes of a non-JSON body (the slicer file). */
  body: unknown
}
type Handler = (call: ApiCall) => Response | Promise<Response>
export type ApiRoutes = Record<string, Handler | Response | (() => Response)>

export function json(body: unknown, status = 200): Response {
  return status === 204
    ? new Response(null, { status })
    : Response.json(body, { status, headers: { 'content-type': 'application/json' } })
}

export function problem(status: number, code: string, extra: Record<string, unknown> = {}) {
  return new Response(
    JSON.stringify({ type: 'about:blank', title: 'Error', status, detail: code, code, ...extra }),
    { status, headers: { 'content-type': 'application/problem+json' } },
  )
}

export function mockApi(routes: ApiRoutes) {
  const calls: ApiCall[] = []
  const fetchMock = vi.fn(async (request: Request) => {
    const url = new URL(request.url)
    const contentType = request.headers.get('content-type')
    const bytes = new Uint8Array(await request.arrayBuffer())
    const isJson = contentType === null || contentType.startsWith('application/json')
    const text = isJson ? new TextDecoder().decode(bytes) : ''
    const call: ApiCall = {
      method: request.method,
      path: url.pathname,
      search: url.search,
      contentType,
      body: isJson ? (text ? JSON.parse(text) : undefined) : bytes,
    }
    calls.push(call)
    const route = routes[`${call.method} ${call.path}`]
    if (route === undefined) return problem(404, 'not_found')
    if (route instanceof Response) return route.clone()
    return route(call)
  })
  vi.stubGlobal('fetch', fetchMock)
  const callsTo = (method: string, path: string) =>
    calls.filter((c) => c.method === method && c.path === path)
  return { calls, callsTo }
}
