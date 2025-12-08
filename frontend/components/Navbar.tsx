import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Logo: React.FC = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white"/>
    <path d="M2 17L12 22L22 17L12 12L2 17Z" fill="#a1a1aa"/>
    <path d="M2 7L12 12L22 7L12 2L2 7Z" stroke="#a1a1aa" strokeWidth="1.5" strokeLinejoin="round"/>
    <path d="M2 17L12 22L22 17L12 12L2 17Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
    <path d="M22 7L12 12V22L22 17V7Z" fill="#a1a1aa" fillOpacity="0.5"/>
    <path d="M2 7L12 12V22L2 17V7Z" fill="white" fillOpacity="0.5"/>
  </svg>
);


const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuth();
  const isBuilderPage = location.pathname === '/builder';

  if (isBuilderPage) {
    return null;
  }

  const navItems = [
    { name: 'Builder', path: '/builder' },
    { name: 'History', path: '/history' },
    { name: 'Product', path: '/product' },
    { name: 'Pricing', path: '/pricing' },
    { name: 'Docs', path: '/docs' },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="sticky top-4 z-50 px-4">
      <nav className={`container mx-auto max-w-6xl py-3 px-6 rounded-lg border border-border glassmorphism flex items-center justify-between`}>
        <NavLink to="/" className="flex items-center gap-2 text-lg">
          <Logo />
          <span>NodeRush</span>
        </NavLink>
        <div className="hidden md:flex items-center gap-6">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `text-sm ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground transition-colors'}`
              }
            >
              {item.name}
            </NavLink>
          ))}
        </div>
        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-foreground/10 text-foreground px-4 py-2 rounded-md text-sm font-semibold card-hover border border-border"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink
                to="/auth"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Log In
              </NavLink>
              <NavLink
                to="/auth"
                className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-semibold card-hover"
              >
                Sign Up
              </NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
