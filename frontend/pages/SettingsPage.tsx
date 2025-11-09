
import React, { useState } from 'react';
import { integrations, integrationCategories, Integration, IntegrationCategory } from '../data/integrations';
import IntegrationModal from '../components/IntegrationModal';


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

const IntegrationsManager: React.FC = () => {
    const [activeCategory, setActiveCategory] = useState<IntegrationCategory | 'All'>('All');
    const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);

    const filteredIntegrations = activeCategory === 'All' 
        ? integrations 
        : integrations.filter(integration => integration.category === activeCategory);

    return (
        <>
            {selectedIntegration && (
                <IntegrationModal 
                    integration={selectedIntegration} 
                    onClose={() => setSelectedIntegration(null)} 
                />
            )}
            <div className="mb-6 flex flex-wrap gap-2">
                <button 
                    onClick={() => setActiveCategory('All')}
                    className={`px-3 py-1.5 text-sm rounded-md transition-colors ${activeCategory === 'All' ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'}`}
                >
                    All
                </button>
                {integrationCategories.map(category => (
                    <button 
                        key={category}
                        onClick={() => setActiveCategory(category)}
                        className={`px-3 py-1.5 text-sm rounded-md transition-colors ${activeCategory === category ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'}`}
                    >
                        {category}
                    </button>
                ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredIntegrations.map(integration => (
                    <div key={integration.name} className="card-hover bg-muted p-5 rounded-md border border-border flex flex-col justify-between">
                        <div>
                            <div className="flex justify-between items-start mb-4">
                                <div className="w-10 h-10 flex items-center justify-center rounded-lg bg-background border border-border">
                                    {integration.logo}
                                </div>
                                {integration.connected ? (
                                    <span className="text-xs font-medium text-green-400 bg-green-500/10 px-2 py-1 rounded-full">Connected</span>
                                ) : (
                                    <span className="text-xs font-medium text-muted-foreground bg-white/5 px-2 py-1 rounded-full">Not Connected</span>
                                )}
                            </div>
                            <h3 className="text-foreground font-semibold mb-1">{integration.name}</h3>
                            <p className="text-sm text-muted-foreground h-16">{integration.description}</p>
                        </div>
                        <button 
                            onClick={() => setSelectedIntegration(integration)}
                            className="mt-4 text-sm bg-foreground/10 hover:bg-foreground/20 text-foreground px-3 py-2 rounded-md transition-colors w-full font-semibold"
                        >
                            {integration.connected ? 'Manage' : 'Connect'}
                        </button>
                    </div>
                ))}
            </div>
        </>
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
      <IntegrationsManager />
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
  const [activeSection, setActiveSection] = useState<Section>('Integrations');

  return (
    <div className="container mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl mb-8">Settings</h1>
      <div className="flex flex-col md:flex-row gap-8 md:gap-12">
        <SettingsSidebar activeSection={activeSection} setSection={setActiveSection} />
        <SettingsContent activeSection={activeSection} />
      </div>
    </div>
  );
};

export default SettingsPage;
