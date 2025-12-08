import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import HomePage from './pages/HomePage';
import AgentBuilderPage from './pages/AgentBuilderPage';
import HistoryPage from './pages/HistoryPage';
import ProductPage from './pages/ProductPage';
import PricingPage from './pages/PricingPage';
import DocsPage from './pages/DocsPage';
import AuthPage from './pages/AuthPage';
import SettingsPage from './pages/SettingsPage';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

const App: React.FC = () => {
  return (
    <HashRouter>
      <AuthProvider>
        <div className="bg-background text-foreground font-sans min-h-screen flex flex-col tracking-wide-custom">
          <Navbar />
          <main className="flex-grow">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/product" element={<ProductPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/docs" element={<DocsPage />} />
              <Route path="/auth" element={<AuthPage />} />

              {/* Protected Routes - Require Authentication */}
              <Route
                path="/builder"
                element={
                  <ProtectedRoute>
                    <AgentBuilderPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/history"
                element={
                  <ProtectedRoute>
                    <HistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <SettingsPage />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </HashRouter>
  );
};

export default App;
