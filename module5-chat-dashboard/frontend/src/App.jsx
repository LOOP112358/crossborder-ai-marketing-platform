import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <span className="brand-icon">AI</span>
            <div>
              <h1>AI电商平台</h1>
              <p>成员5 · 智能客服 & 运营看板</p>
            </div>
          </div>
          <nav>
            <NavLink to="/" end>智能客服</NavLink>
            <NavLink to="/dashboard">运营看板</NavLink>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
