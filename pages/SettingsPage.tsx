import React, { useState } from 'react';

type Section = 'Profile' | 'Billing' | 'API Keys' | 'Integrations' | 'Team';

const SettingsSidebar: React.FC<{ activeSection: Section; setSection: (section: Section) => void }> = ({ activeSection, setSection }) => {
  const navItems: Section[] = ['Profile', 'Billing', 'API Keys', 'Integrations', 'Team'];

  return (
    <aside className="w-56 flex-shrink-0">
      <nav className="flex flex-col space-y-1">
        {navItems.map(item => (
          <button
            key={item}
            onClick={() => setSection(item)}
            className={`px-4 py-2 text-left text-sm rounded-md transition-colors ${
              activeSection === item ? 'bg-muted text-foreground' : 'text-muted-foreground hover:bg-muted/50'
            }`}
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
};

const SettingsContent: React.FC<{ activeSection: Section }> = ({ activeSection }) => (
  <div className="flex-grow">
    <h2 className="text-2xl mb-6">{activeSection}</h2>
    
    {activeSection === 'Profile' && (
      <div className="bg-muted p-6 rounded-md border border-border">Profile Settings Form Placeholder</div>
    )}
    {activeSection === 'Billing' && (
      <div className="bg-muted p-6 rounded-md border border-border">Billing History Table Placeholder</div>
    )}
    {activeSection === 'API Keys' && (
      <div className="bg-muted p-6 rounded-md border border-border">API Key Management Placeholder</div>
    )}
    {activeSection === 'Integrations' && (
      <div className="bg-muted p-6 rounded-md border border-border">Integrations Manager Placeholder</div>
    )}
    {activeSection === 'Team' && (
      <div className="bg-muted p-6 rounded-md border border-border">Team Management Placeholder</div>
    )}

    {activeSection === 'Profile' && (
        <div className="mt-8 bg-red-900/20 border border-red-500/30 p-6 rounded-md">
            <h3 className="text-red-400">Danger Zone</h3>
            <p className="text-sm text-red-400/80 mt-2 mb-4">Deleting your account is permanent and cannot be undone.</p>
            <button className="bg-red-500/80 hover:bg-red-500 text-white text-sm px-4 py-2 rounded-md font-semibold">
                Delete Account
            </button>
        </div>
    )}
  </div>
);

const SettingsPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState<Section>('Profile');

  return (
    <div className="container mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl mb-8">Settings</h1>
      <div className="flex gap-12">
        <SettingsSidebar activeSection={activeSection} setSection={setActiveSection} />
        <SettingsContent activeSection={activeSection} />
      </div>
    </div>
  );
};

export default SettingsPage;