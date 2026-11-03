import { Navigate, Route, Routes } from 'react-router'

import { CalculatePage } from '@/pages/calculate'
import { CatalogPage } from '@/pages/catalog'
import { ItemPage } from '@/pages/item'
import { SettingsPage } from '@/pages/settings'

import { AppLayout } from './AppLayout'

// Screens of cost-calculator ADR 0001; the backend serves index.html for each of these paths.
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/calculate" replace />} />
        <Route path="calculate" element={<CalculatePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="catalog/:itemId" element={<ItemPage />} />
        <Route path="*" element={<Navigate to="/calculate" replace />} />
      </Route>
    </Routes>
  )
}
