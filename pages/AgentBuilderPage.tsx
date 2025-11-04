
import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

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

const icons = {
  chat: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>,
  integrations: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9V3m-9 9h18" /></svg>,
  send: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>,
  folder: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>,
  file: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>,
  play: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  stop: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M9 10h6v4H9z" /></svg>,
  deploy: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 transform rotate-[80deg]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>,
  chevronLeft: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" /></svg>,
  chevronRight: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round"d="M9 5l7 7-7 7" /></svg>,
  github: <svg viewBox="0 0 16 16" className="w-4 h-4" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>,
  save: <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M12 12v9" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 16l-3-3-3 3" /></svg>,
};

const integrationsList = [
  "Gmail", "Twilio", "Slack", "Supabase", "Google Sheets", "Airtable", "Notion", "OpenAI", "LangChain", "LangGraph", "Huggingface", "Render", "Vercel", "Docker", "DataDog", "Sentry", "PostHog", "AWS"
];

const integrationLogos: Record<string, React.ReactNode> = {
  Gmail: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#EA4335" d="M10 38h28v-2H10v2zm0-26v18h28V12H10zm23.4 2-11.4 8-11.4-8h22.8zM4 42V6h40v36H4z"/></svg>,
  Twilio: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#F22F46" d="M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm0 10c2.21 0 4 1.79 4 4s-1.79 4-4 4-4-1.79-4-4 1.79-4 4-4zm0 18c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"/></svg>,
  Slack: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#36C5F0" d="M14 18h4v12h-4z"/><path fill="#2EB67D" d="M22 18h-4v-4c0-2.21 1.79-4 4-4h8v4h-8v4z"/><path fill="#ECB22E" d="M30 30h-4V18h4z"/><path fill="#E01E5A" d="M26 30h4v4c0 2.21-1.79 4-4 4h-8v-4h8v-4z"/><path fill="#36C5F0" d="M18 14v-4h12v4z"/><path fill="#2EB67D" d="M18 22v4c0 2.21-1.79 4-4 4v-8h4z"/><path fill="#ECB22E" d="M30 34v4H18v-4z"/><path fill="#E01E5A" d="M30 26v-4c0-2.21 1.79-4 4-4v8h-4z"/></svg>,
  Supabase: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#3ECF8E" d="M24 4L4 14.5l20 10.5L44 14.5z"/><path fill="#3ECF8E" opacity=".5" d="M24 25L4 14.5V25l20 10.5L44 25V14.5z"/><path fill="#3ECF8E" opacity=".2" d="M24 46L4 35.5V25l20 10.5L44 25v10.5z"/></svg>,
  "Google Sheets": <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#188038" d="M27 4h-6l-2 4h10z"/><path fill="#0F9D58" d="M21 4h6v10h-6z"/><path fill="#34A853" d="M10 14h28v20H10z"/><path fill="#107C41" d="M10 34h28v2H10z"/><path d="M24 20h-4v8h4v-3h4v-2h-4v-3z" fill="#fff"/><path d="M26 25h4v2h-4z" fill="#fff"/></svg>,
  Airtable: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#F7C434" d="M12 12h24v12H12z"/><path fill="#FFB300" d="M12 24h12v12H12z"/><path fill="#18BFFF" d="M24 24h12v12H24z"/></svg>,
  Notion: <svg width="48" height="48" viewBox="0 0 48 48"><path d="M10 10h28v28H10z" fill="#000"/><path d="M24 14v16.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V14h8zm-2 2h-4v14.5c0 1.1.9 2 2 2s2-.9 2-2V16zm12-2v20h-8v-4h6v-2h-6v-4h6v-2h-6v-4h6v-2h-6V14h8z" fill="#fff"/></svg>,
  OpenAI: <svg width="48" height="48" viewBox="0 0 48 48"><path fill-rule="evenodd" clip-rule="evenodd" d="M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20zM14 24c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10-10-4.477-10-10z" fill="#00A67E"/><path d="M14 24c0 2.761 1.12 5.261 2.929 7.071L24 24l-7.071-7.071A9.954 9.954 0 0014 24z" fill="#212121" fill-opacity=".2"/></svg>,
  LangChain: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#009688" d="M28 12h-8c-3.31 0-6 2.69-6 6s2.69 6 6 6h8v4h-8c-5.52 0-10-4.48-10-10s4.48-10 10-10h8v4z"/><path fill="#8BC34A" d="M20 36h8c3.31 0 6-2.69 6-6s-2.69-6-6-6h-8v-4h8c5.52 0 10 4.48 10 10s-4.48 10-10 10h-8v-4z"/></svg>,
  LangGraph: <svg width="48" height="48" viewBox="0 0 48 48"><g fill="none" stroke-width="2"><circle cx="16" cy="16" r="3" stroke="#8BC34A"/><circle cx="32" cy="16" r="3" stroke="#8BC34A"/><circle cx="16" cy="32" r="3" stroke="#009688"/><circle cx="32" cy="32" r="3" stroke="#009688"/><path stroke="#8BC34A" d="M19 16h10"/><path stroke="#009688" d="M19 32h10"/><path stroke="#BDBDBD" d="M16 19v10M32 19v10"/></g></svg>,
  Huggingface: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#FFD54F" d="M36 24c0 6.627-5.373 12-12 12S12 30.627 12 24s5.373-12 12-12 12 5.373 12 12z"/><path d="M19 22c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm10 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" fill="#000"/><path d="M18 30h12c1.1 0 2-.9 2-2s-.9-2-2-2H18c-1.1 0-2 .9-2 2s.9 2 2 2z" fill="#6D4C41"/></svg>,
  Render: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#46E3B7" d="M24 4c11.046 0 20 8.954 20 20s-8.954 20-20 20S4 35.046 4 24 12.954 4 24 4zm-4 12h8v16h-8V16z"/></svg>,
  Vercel: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#fff" d="M24 4L4 40h40z"/></svg>,
  Docker: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#0db7ed" d="M44 24c0 2.21-1.79 4-4 4h-4v-8h4c2.21 0 4 1.79 4 4z"/><path fill="#0db7ed" d="M4 24c0-5.523 4.477-10 10-10h14v20H14c-5.523 0-10-4.477-10-10z"/><path d="M14 18h4v4h-4zm6 0h4v4h-4zm6 0h4v4h-4zm-12 6h4v4h-4zm6 0h4v4h-4z" fill="#fff"/></svg>,
  DataDog: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#632CA6" d="M24 4L4 16v16l20 12 20-12V16L24 4zm-4 22h-4v-8h4v8zm8 0h-4v-8h4v8z"/></svg>,
  Sentry: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#FB4226" d="M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm0 30c-5.52 0-10-4.48-10-10s4.48-10 10-10 10 4.48 10 10-4.48 10-10 10z"/><circle cx="24" cy="24" r="4" fill="#fff"/></svg>,
  PostHog: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#F6A800" d="M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4z"/><path d="M24 14c-5.523 0-10 4.477-10 10s10 14 10 14 10-8.477 10-10-4.477-10-10-10zm0 14c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" fill="#FFF"/></svg>,
  AWS: <svg width="48" height="48" viewBox="0 0 48 48"><path fill="#FF9900" d="M10 32.5c0 .83.67 1.5 1.5 1.5h25c.83 0 1.5-.67 1.5-1.5v-1c0-.83-.67-1.5-1.5-1.5h-25c-.83 0-1.5.67-1.5 1.5v1z"/><path fill="#232F3E" d="M24 12c-6.627 0-12 5.373-12 12s5.373 12 12 12c.75 0 1.48-.07 2.18-.2.53-.1 1.05-.24 1.55-.42.4-.14.78-.3 1.15-.48.33-.16.64-.34.94-.53.25-.16.49-.33.72-.51.2-.15.38-.31.56-.47.16-.14.3-.29.44-.44.12-.12.24-.25.35-.38.1-.11.19-.22.28-.33.07-.09.14-.18.2-.28.05-.08.1-.16.14-.24.03-.07.06-.14.09-.21.02-.06.04-.12.05-.18.01-.05.02-.1.02-.15.01-.04.01-.08.01-.12.01-.06.01-.12.01-.18v-.16c0-.06-.01-.12-.01-.18 0-.05-.01-.1-.01-.15-.01-.05-.02-.1-.03-.15-.02-.07-.04-.14-.06-.21-.04-.09-.08-.18-.12-.27-.06-.1-.13-.2-.2-.3-.08-.12-.17-.24-.26-.35-.1-.13-.21-.25-.32-.37-.13-.14-.26-.28-.4-.41-.16-.16-.33-.31-.5-.46-.2-.18-.41-.35-.63-.51-.27-.2-.55-.39-.84-.57-.35-.22-.72-.42-1.1-.6-.5-.24-1.03-.45-1.58-.61C26.92 18.07 25.48 18 24 18c-3.31 0-6 2.69-6 6s2.69 6 6 6h10v-4h-4v-4h4v-4H24c-5.52 0-10 4.48-10 10s4.48 10 10 10 10-4.48 10-10c0-.75-.09-1.48-.25-2.18-.04-.17-.08-.34-.13-.51-.04-.14-.09-.28-.14-.42-.05-.12-.1-.24-.16-.36-.05-.1-.1-.2-.15-.3-.04-.08-.09-.16-.13-.24-.03-.07-.07-.14-.1-.21-.02-.06-.05-.12-.07-.18-.01-.05-.03-.1-.04-.15-.01-.04-.02-.08-.02-.12 0-.06-.01-.12-.01-.18v-.16c0-.06.01-.12.01-.18.01-.05.01-.1.02-.15.02-.05.03-.1.05-.15.03-.07.05-.14.08-.21.05-.09.09-.18.14-.27.07-.1.14-.2.21-.3.1-.12.19-.24.29-.35.12-.13.24-.25.36-.37.15-.14.3-.28.45-.41.18-.16.37-.31.56-.46.22-.18.46-.35.7-.51.3-.2.61-.39.94-.57.4-.22.81-.42 1.24-.6.58-.24 1.18-.45 1.8-.61C33.08 13.07 34.52 12 36 12c3.31 0 6-2.69 6-6s-2.69-6-6-6-6 2.69-6 6v10z"/></svg>,
};


const TabButton: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode; icon: React.ReactNode }> = ({ active, onClick, children, icon }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
      active ? 'text-primary border-primary' : 'text-muted-foreground hover:text-foreground border-transparent'
    }`}
  >
    {icon} {children}
  </button>
);

const ChatInterface: React.FC = () => (
    <div className="flex flex-col h-full">
        <div className="flex-grow p-4 space-y-6 overflow-y-auto">
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary flex-shrink-0">U</div>
                <div className="bg-background p-3 rounded-lg text-sm">
                    <p>Can you create a financial analyst agent that tracks AAPL and TSLA stock prices and sends me a Slack notification if either drops by 5%?</p>
                </div>
            </div>
            <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-foreground/10 flex items-center justify-center flex-shrink-0">
                    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white"/><path d="M2 17L12 22L22 17L12 12L2 17Z" fill="#a1a1aa"/><path d="M2 7L12 12L22 7L12 2L2 7Z" stroke="#a1a1aa" strokeWidth="1.5" strokeLinejoin="round"/></svg>
                </div>
                <div className="bg-background p-3 rounded-lg text-sm">
                    <p>Of course. I've scaffolded the agent code, created a new tool for fetching stock data, and set up a trigger for Slack notifications. You'll need to connect your Slack integration to continue.</p>
                </div>
            </div>
        </div>
        <div className="p-4 border-t border-border">
            <div className="relative">
                <textarea
                    rows={2}
                    placeholder="Describe your agent..."
                    className="w-full bg-background resize-none text-sm p-3 pr-12 rounded-md border border-border focus:outline-none focus:border-primary"
                />
                <button className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md bg-primary hover:bg-opacity-90 text-primary-foreground">
                    {icons.send}
                </button>
            </div>
        </div>
    </div>
);

const IntegrationManager: React.FC = () => (
    <div className="p-4 overflow-y-auto h-full">
        <div className="grid grid-cols-3 gap-3">
            {integrationsList.map(name => (
                <div key={name} className="card-hover bg-background p-4 rounded-md border border-border flex flex-col items-center justify-between aspect-square text-center">
                    <div className="flex-grow flex items-center justify-center w-12 h-12">
                         {integrationLogos[name] || <div className="w-8 h-8 bg-muted rounded-md" />}
                    </div>
                    <span className="text-xs font-medium my-2 w-full truncate">{name}</span>
                    <button className="text-xs px-3 py-1.5 rounded-md bg-muted-foreground/20 text-muted-foreground hover:bg-muted-foreground/30 hover:text-foreground transition-colors w-full">
                        Connect
                    </button>
                </div>
            ))}
        </div>
    </div>
);

const LeftPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Chat');

  return (
    <div className="flex flex-col bg-muted rounded-lg border border-border h-full">
      <div className="flex items-center border-b border-border px-2 flex-shrink-0">
        <TabButton active={activeTab === 'Chat'} onClick={() => setActiveTab('Chat')} icon={icons.chat}>Chat</TabButton>
        <TabButton active={activeTab === 'Integrations'} onClick={() => setActiveTab('Integrations')} icon={icons.integrations}>Integrations</TabButton>
      </div>
      <div className="flex-grow overflow-hidden">
        {activeTab === 'Chat' && <ChatInterface />}
        {activeTab === 'Integrations' && <IntegrationManager />}
      </div>
    </div>
  );
};

const CodeEditor: React.FC = () => {
    // FIX: Explicitly type `children` prop for syntax highlighting components to resolve TypeScript errors.
    const Keyword = ({ children }: { children: React.ReactNode }) => <span className="text-purple-400">{children}</span>;
    const String = ({ children }: { children: React.ReactNode }) => <span className="text-green-400">{children}</span>;
    const FunctionName = ({ children }: { children: React.ReactNode }) => <span className="text-blue-400">{children}</span>;
    const ClassName = ({ children }: { children: React.ReactNode }) => <span className="text-yellow-300">{children}</span>;
    const Decorator = ({ children }: { children: React.ReactNode }) => <span className="text-yellow-500">{children}</span>;
    const Self = ({ children }: { children: React.ReactNode }) => <span className="text-orange-400">{children}</span>;
    const Comment = ({ children }: { children: React.ReactNode }) => <span className="text-gray-500">{children}</span>;

    return (
        <div className="flex-grow p-4 font-mono text-xs bg-black/20 overflow-y-auto rounded-t-lg leading-relaxed">
          <div className="flex">
            <div className="text-right pr-4 text-muted-foreground/50 select-none">
                {Array.from({ length: 24 }, (_, i) => i + 1).map(i => <div key={i}>{i}</div>)}
            </div>
            <pre className="!bg-transparent !p-0">
              <code>
                <div><Keyword>from</Keyword> vibedeploy.tools <Keyword>import</Keyword> tool</div>
                <div><Keyword>from</Keyword> vibedeploy.integrations <Keyword>import</Keyword> slack, finnhub</div>
                <br />
                <div><Decorator>@tool</Decorator></div>
                <div><Keyword>def</Keyword> <FunctionName>get_stock_price</FunctionName>(symbol: <ClassName>str</ClassName>) -&gt; <ClassName>float</ClassName>:</div>
                <div>    <String>"""Fetches the current price of a stock."""</String></div>
                <div>    <Keyword>return</Keyword> finnhub.get_quote(symbol)[<String>'c'</String>]</div>
                <br />
                <div><Keyword>class</Keyword> <ClassName>FinancialAgent</ClassName>:</div>
                <div>    <Keyword>def</Keyword> <FunctionName>__init__</FunctionName>(<Self>self</Self>, symbols, threshold):</div>
                <div>        <Self>self</Self>.symbols = symbols</div>
                <div>        <Self>self</Self>.threshold = threshold</div>
                <div>        <Self>self</Self>.initial_prices = {'{s: get_stock_price(s) for s in symbols}'}</div>
                <br />
                <div>    <Keyword>def</Keyword> <FunctionName>check_prices</FunctionName>(<Self>self</Self>):</div>
                <div>        <Keyword>for</Keyword> symbol <Keyword>in</Keyword> <Self>self</Self>.symbols:</div>
                <div>            current_price = get_stock_price(symbol)</div>
                <div>            initial_price = <Self>self</Self>.initial_prices[symbol]</div>
                <div>            <Keyword>if</Keyword> (initial_price - current_price) / initial_price &gt;= <Self>self</Self>.threshold:</div>
                <div>                <Self>self</Self>.send_alert(symbol, current_price)</div>
                <br />
                <div>    <Keyword>def</Keyword> <FunctionName>send_alert</FunctionName>(<Self>self</Self>, symbol, price):</div>
                <div>        message = <String>f"🚨 *Stock Alert* 🚨\\n&gt;{'{symbol}'} has dropped to ${'{price}'}"</String></div>
                <div>        slack.send_message(<String>"#alerts"</String>, message)</div>
              </code>
            </pre>
          </div>
        </div>
    );
};

const FileTree: React.FC = () => (
    <div className="p-3 border-t border-border text-xs text-muted-foreground flex-shrink-0 bg-background/50 rounded-b-lg">
        <div className="flex items-center">{icons.folder} src/</div>
        <div className="pl-4">
            <div className="flex items-center text-primary">{icons.file} main_agent.py</div>
            <div className="flex items-center">{icons.file} tools.py</div>
        </div>
        <div className="flex items-center">{icons.file} config.json</div>
    </div>
);

const MiddlePanel: React.FC = () => (
  <div className="flex flex-col bg-muted rounded-lg border border-border h-full overflow-hidden">
    <div className="p-2 border-b border-border text-xs text-muted-foreground flex justify-between items-center">
      <span>/src/main_agent.py</span>
      <span className="text-muted-foreground/50">Python 3.11</span>
    </div>
    <CodeEditor />
    <FileTree />
  </div>
);

const AgentVisualizer: React.FC = () => (
    <div className="flex-grow p-4 flex items-center justify-center text-muted-foreground relative bg-grid-pattern overflow-hidden">
        {/* Mockup of a node-based UI */}
        <div className="relative w-full h-full">
            {/* Lines */}
            <svg className="absolute inset-0 w-full h-full" fill="none">
                <path d="M 80 80 C 180 80, 180 160, 280 160" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                <path d="M 280 190 C 180 190, 180 280, 80 280" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
            </svg>
            {/* Nodes */}
            <div className="absolute top-16 left-4 bg-background border border-border p-3 rounded-md text-xs w-32">
                <p className="font-bold">On Message</p><p className="text-muted-foreground">Trigger</p>
            </div>
            <div className="absolute top-[132px] left-[280px] bg-background border-2 border-primary p-3 rounded-md text-xs w-32 shadow-lg shadow-primary/20">
                <p className="font-bold">Fetch Prices</p><p className="text-muted-foreground">Tool Call</p>
            </div>
            <div className="absolute top-64 left-4 bg-background border border-border p-3 rounded-md text-xs w-32">
                <p className="font-bold">Send Alert</p><p className="text-muted-foreground">Slack Integration</p>
            </div>
        </div>
    </div>
);

const TerminalOutput: React.FC = () => (
    <div className="h-1/3 border-t border-border flex flex-col flex-shrink-0">
       <div className="p-2 border-b border-border text-sm font-medium">Terminal</div>
        <div className="flex-grow p-4 font-mono text-xs bg-black/20 overflow-y-auto">
            <p className="text-muted-foreground">&gt; Agent process started. Watching AAPL, TSLA.</p>
            <p className="text-muted-foreground">&gt; [10:30:01] Fetching prices...</p>
            <p className="text-green-400">&gt; [10:30:02] Prices within threshold. Waiting...</p>
            <p className="text-muted-foreground">&gt; [10:35:01] Fetching prices...</p>
        </div>
    </div>
);

const RightPanel: React.FC<{
  isCodeEditorVisible: boolean;
  onToggleCodeEditor: () => void;
}> = ({ isCodeEditorVisible, onToggleCodeEditor }) => (
  <div className="flex flex-col bg-muted rounded-lg border border-border h-full">
    <div className="p-2 border-b border-border text-sm font-medium flex justify-between items-center">
        <div className="flex items-center gap-2">
            <button onClick={onToggleCodeEditor} className="p-1 -m-1 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-full">
                {isCodeEditorVisible ? icons.chevronLeft : icons.chevronRight}
            </button>
            <span>Agent Visualizer</span>
        </div>
        <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 text-xs bg-foreground/10 text-muted-foreground hover:text-foreground px-3 py-1 rounded-md transition-colors">{icons.github}</button>
            <button className="flex items-center gap-1.5 text-xs bg-foreground/10 text-muted-foreground hover:text-foreground px-3 py-1 rounded-md transition-colors">{icons.save} Save</button>
            <button className="flex items-center gap-1.5 text-xs bg-green-500/20 text-green-400 px-3 py-1 rounded-md hover:bg-green-500/30">{icons.play} Run</button>
            <button className="flex items-center gap-1.5 text-xs bg-red-500/20 text-red-400 px-3 py-1 rounded-md hover:bg-red-500/30">{icons.stop} Stop</button>
            <button className="flex items-center gap-1.5 text-xs bg-blue-500/20 text-blue-400 px-3 py-1 rounded-md hover:bg-blue-500/30">{icons.deploy} Deploy</button>
        </div>
    </div>
    <AgentVisualizer />
    <TerminalOutput />
  </div>
);

const StatusBar: React.FC = () => (
    <div className="flex items-center justify-between text-xs text-muted-foreground bg-muted p-2 rounded-lg border border-border mt-2">
        <div className="flex items-center gap-4">
            <span>Agent: Financial Analyst</span>
            <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span>Running</span>
            </div>
        </div>
        <div>VibeDeploy v1.0</div>
    </div>
)

const AgentBuilderPage: React.FC = () => {
  const [isMiddlePanelVisible, setIsMiddlePanelVisible] = useState(true);

  return (
    <div className="h-screen p-4 flex flex-col relative">
        <NavLink to="/" className="absolute top-4 left-4 z-50 flex items-center gap-2 text-lg">
            <Logo />
            <span className="font-semibold">VibeDeploy</span>
        </NavLink>
        <div className="flex flex-col lg:flex-row gap-2 flex-grow min-h-0 pt-16">
            <div className="w-full lg:w-3/12 min-h-[400px] lg:flex-shrink-0">
                <LeftPanel />
            </div>
            <div className={`w-full min-h-[400px] transition-all duration-500 ease-in-out ${isMiddlePanelVisible ? 'lg:w-4/12' : 'lg:w-0'}`}>
                {isMiddlePanelVisible && <MiddlePanel />}
            </div>
            <div className={`w-full min-h-[400px] transition-all duration-500 ease-in-out ${isMiddlePanelVisible ? 'lg:w-5/12' : 'lg:w-9/12'}`}>
                <RightPanel isCodeEditorVisible={isMiddlePanelVisible} onToggleCodeEditor={() => setIsMiddlePanelVisible(v => !v)} />
            </div>
        </div>
        <StatusBar />
    </div>
  );
};

export default AgentBuilderPage;
