import { BrowserRouter } from 'react-router'

import { AppRoutes } from './layout/AppRoutes'
import { QueryProvider } from './providers/QueryProvider'

export function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryProvider>
  )
}
