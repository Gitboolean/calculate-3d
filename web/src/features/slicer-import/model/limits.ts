/**
 * Mirrors MAX_BODY_BYTES in backend/src/calculate3d/modules/importing/router.py. Only a courtesy
 * pre-check that spares the upload; the server stays the real check (AC-13).
 */
export const MAX_FILE_BYTES = 100_000_000
