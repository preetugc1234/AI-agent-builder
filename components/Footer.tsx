import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Footer: React.FC = () => {
  const location = useLocation();
  if (location.pathname === '/builder') {
    return null;
  }
  
  const footerLinks = {
    'Product': ['Builder', 'History', 'Pricing', 'Docs'],
    'Company': ['About Us', 'Careers', 'Contact'],
    'Legal': ['Privacy Policy', 'Terms of Service'],
  };

  return (
    <footer className="border-t border-border mt-24">
      <div className="container mx-auto max-w-6xl px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1">
             <Link to="/" className="flex items-center gap-2 text-lg">
              <span>VibeDeploy</span>
            </Link>
            <p className="text-muted-foreground mt-2 text-sm">Deploy AI agents with just a vibe.</p>
          </div>
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-foreground mb-4">{title}</h3>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground">&copy; {new Date().getFullYear()} VibeDeploy. All rights reserved.</p>
          <div className="flex gap-4 mt-4 md:mt-0">
            {/* Placeholder for social icons */}
            <span className="text-muted-foreground text-sm">Follow Us</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;