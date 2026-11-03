import type { Schemas } from './client'

export type ValidationIssue = Schemas['ValidationIssue']

/** RFC 9457 body the API sends for every error, with the optional extension members. */
export type Problem = Schemas['Problem'] &
  Partial<
    Pick<Schemas['FieldProblem'], 'field'> &
      Pick<Schemas['PlasticInUseProblem'], 'items'> &
      Pick<Schemas['SettingsMissingProblem'], 'missing'> &
      Pick<Schemas['ValidationProblem'], 'errors'>
  >

export class ApiError extends Error {
  readonly status: number
  readonly problem: Problem

  constructor(status: number, problem: Problem) {
    super(problem.detail)
    this.name = 'ApiError'
    this.status = status
    this.problem = problem
  }
}

export function isProblem(error: unknown, code: string): error is ApiError {
  return error instanceof ApiError && error.problem.code === code
}

function toProblem(body: unknown, status: number): Problem {
  if (typeof body === 'object' && body !== null && 'code' in body) return body as Problem
  return { type: 'about:blank', title: 'Error', status, detail: String(body), code: 'http_error' }
}

type FetchResult<T> = { data?: T; error?: unknown; response: Response }

/** Awaits an `api.*` call: the data on success, an `ApiError` with the problem otherwise. */
export async function unwrap<T>(request: Promise<FetchResult<T>>): Promise<T> {
  const { data, error, response } = await request
  if (!response.ok) throw new ApiError(response.status, toProblem(error, response.status))
  return data as T
}

/** `["body", "plastics", 0, "usage_cg"]` → `"plastics.0.usage_cg"` (same shape as `field`). */
export function issueField(issue: ValidationIssue): string {
  return issue.loc.filter((part) => part !== 'body').join('.')
}
