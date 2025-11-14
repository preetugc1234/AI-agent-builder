
import React from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
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
      <div className="bg-background text-foreground font-sans min-h-screen flex flex-col tracking-wide-custom">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/builder" element={<AgentBuilderPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/product" element={<ProductPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </HashRouter>
  );
};

export default App;