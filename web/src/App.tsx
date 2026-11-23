import { useEffect } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { ToastProvider } from './components/Toast'
import { AuthProvider } from './lib/auth'
import { AccountPage } from './pages/AccountPage'
import { AwardsPage } from './pages/AwardsPage'
import { CheckinPage } from './pages/CheckinPage'
import { EventPage } from './pages/EventPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { TicketPage } from './pages/TicketPage'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <ScrollToTop />
          <Routes>
            <Route element={<AppShell />}>
              <Route index element={<EventPage />} />
              <Route path="awards" element={<AwardsPage />} />
              <Route path="ingresso" element={<TicketPage />} />
              <Route path="conta" element={<AccountPage />} />
              <Route path="entrar" element={<LoginPage />} />
              <Route path="esqueci-senha" element={<ForgotPasswordPage />} />
              <Route path="redefinir-senha" element={<ResetPasswordPage />} />
              <Route path="checkin/:code" element={<CheckinPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
