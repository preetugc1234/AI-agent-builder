
import React, { useState } from 'react';
import type { Integration } from '../data/integrations';

type ModalTab = 'Setup' | 'API' | 'Connect';

const icons = {
  close: <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>,
};

const ModalTabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
    <button onClick={onClick} className={`px-4 py-2 text-sm font-semibold rounded-md transition-colors ${active ? 'bg-foreground/10 text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
        {children}
    </button>
);

const InputField: React.FC<{ id: string; type: string; label: string; placeholder: string }> = ({ id, type, label, placeholder }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium mb-2 text-muted-foreground">{label}</label>
        <input 
            type={type} 
            id={id} 
            placeholder={placeholder}
            className="w-full bg-background px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary" 
        />
    </div>
);

const IntegrationModal: React.FC<{ integration: Integration; onClose: () => void; }> = ({ integration, onClose }) => {
    const [activeTab, setActiveTab] = useState<ModalTab>('Connect');

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" role="dialog" aria-modal="true" onClick={onClose}>
            <div className="w-full max-w-3xl h-[80vh] max-h-[700px] bg-muted rounded-lg border border-border glassmorphism flex flex-col" onClick={e => e.stopPropagation()}>
                <header className="flex items-center justify-between p-6 border-b border-border flex-shrink-0">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-background border border-border">
                            {integration.logo}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">{integration.name}</h2>
                            <p className="text-sm text-muted-foreground">{integration.category}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 -m-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-foreground/10 transition-colors">
                        {icons.close}
                    </button>
                </header>

                <div className="flex-grow flex flex-col md:flex-row gap-6 p-6 overflow-hidden">
                    <aside className="w-full md:w-48 flex-shrink-0">
                        <nav className="flex flex-row md:flex-col gap-2">
                            <ModalTabButton active={activeTab === 'Connect'} onClick={() => setActiveTab('Connect')}>Connect API</ModalTabButton>
                            <ModalTabButton active={activeTab === 'Setup'} onClick={() => setActiveTab('Setup')}>Setup Guide</ModalTabButton>
                            <ModalTabButton active={activeTab === 'API'} onClick={() => setActiveTab('API')}>API Docs</ModalTabButton>
                        </nav>
                    </aside>
                    <main className="flex-grow overflow-y-auto pr-2">
                        {activeTab === 'Connect' && (
                            <div className="space-y-6">
                                <h3 className="text-lg font-semibold">Connect to {integration.name}</h3>
                                {integration.credentials.map(cred => (
                                    <InputField key={cred.id} {...cred} />
                                ))}

                                <div className="flex gap-4 items-center pt-4">
                                     <button className="bg-primary text-primary-foreground px-5 py-2 rounded-md font-semibold card-hover text-sm">
                                        Save & Connect
                                    </button>
                                    {integration.connected && (
                                        <button className="bg-red-500/20 text-red-400 px-5 py-2 rounded-md font-semibold card-hover text-sm">
                                            Disconnect
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                        {activeTab === 'Setup' && (
                           <div className="prose prose-sm prose-invert max-w-none">
                                <h3 className="!mb-4">Setup Guide</h3>
                                <p>Follow these steps to connect your {integration.name} account:</p>
                                <ol>
                                    {integration.setupGuide.map((step, index) => (
                                        <li key={index}>{step}</li>
                                    ))}
                                </ol>
                           </div>
                        )}
                         {activeTab === 'API' && (
                           <div className="prose prose-sm prose-invert max-w-none">
                                <h3>API Documentation</h3>
                                <p>Here's an example of how to use the {integration.name} API within the VibeDeploy SDK:</p>
                                <pre className="bg-background !text-xs p-4 rounded-md border border-border">
                                    <code>{integration.apiDocs}</code>
                                </pre>
                           </div>
                        )}
                    </main>
                </div>
            </div>
        </div>
    );
};

export default IntegrationModal;
