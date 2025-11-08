
import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { integrations } from '../data/integrations';

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
            {integrations.map(integration => (
                <div key={integration.name} className="card-hover bg-background p-3 rounded-md border border-border flex flex-col items-center justify-between aspect-square text-center">
                    <div className="flex-grow flex items-center justify-center w-8 h-8">
                         {integration.logo}
                    </div>
                    <span className="text-xs font-medium my-2 w-full truncate">{integration.name}</span>
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

const Keyword = ({ children }: { children: React.ReactNode }) => <span className="text-purple-400">{children}</span>;
const String = ({ children }: { children: React.ReactNode }) => <span className="text-green-400">{children}</span>;
const FunctionName = ({ children }: { children: React.ReactNode }) => <span className="text-blue-400">{children}</span>;
const ClassName = ({ children }: { children: React.ReactNode }) => <span className="text-yellow-300">{children}</span>;
const Decorator = ({ children }: { children: React.ReactNode }) => <span className="text-yellow-500">{children}</span>;
const Self = ({ children }: { children: React.ReactNode }) => <span className="text-orange-400">{children}</span>;

const CodeEditor: React.FC = () => {
    // FIX: Corrected self-closing component tags to wrap their text content, resolving missing 'children' prop errors.
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
                <path d="M 144 92 C 212 92, 212 188, 280 188" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
                <path d="M 280 188 C 212 188, 212 284, 144 284" stroke="rgba(255,255,255,0.2)" strokeWidth="2" />
            </svg>
            {/* Nodes */}
            <div className="absolute top-[63px] left-4 bg-background border border-border p-3 rounded-md text-xs w-32">
                <p className="font-bold">On Message</p><p className="text-muted-foreground">Trigger</p>
            </div>
            <div className="absolute top-[159px] left-[280px] bg-background border-2 border-primary p-3 rounded-md text-xs w-32 shadow-lg shadow-primary/20">
                <p className="font-bold">Fetch Prices</p><p className="text-muted-foreground">Tool Call</p>
            </div>
            <div className="absolute top-[255px] left-4 bg-background border border-border p-3 rounded-md text-xs w-32">
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