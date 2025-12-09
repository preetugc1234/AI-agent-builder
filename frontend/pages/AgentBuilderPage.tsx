import React, { useState, useEffect } from 'react';
import { NavLink, useSearchParams } from 'react-router-dom';
import { createAgent, generateNewAgent, getAgent, type Agent } from '../services/api';
import { integrations } from '../data/integrations';
import IntegrationModal from '../components/IntegrationModal';

const Logo: React.FC = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white"/>
    <path d="M2 17L12 22L22 17L12 12L2 17Z" fill="#a1a1aa"/>
  </svg>
);

const AgentBuilderPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('agent');

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [vibePrompt, setVibePrompt] = useState('');

  // Agent state
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);

  // Load existing agent if ID is provided
  useEffect(() => {
    if (agentId) {
      loadAgent(agentId);
    }
  }, [agentId]);

  const loadAgent = async (id: string) => {
    try {
      const data = await getAgent(id);
      setAgent(data);
      setName(data.name);
      setDescription(data.description || '');
      setVibePrompt(data.vibe_prompt);
    } catch (err: any) {
      setError(err.message || 'Failed to load agent');
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsGenerating(true);

    try {
      const result = await generateNewAgent({
        name,
        description,
        vibe_prompt: vibePrompt,
      });

      setAgent(result as any);
    } catch (err: any) {
      setError(err.message || 'Generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <NavLink to="/" className="flex items-center gap-2 text-lg">
          <Logo />
          <span className="font-semibold">NodeRush</span>
        </NavLink>
        <NavLink
          to="/history"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          View All Agents →
        </NavLink>
      </div>

      <div className="max-w-6xl mx-auto w-full flex-grow">
        <h1 className="text-3xl mb-2">AI Agent Builder</h1>
        <p className="text-muted-foreground mb-8">
          Describe your agent and let our 3-agent AI system build it for you
        </p>

        {/* Agent Creation Form */}
        {!agent && (
          <div className="bg-muted p-6 rounded-lg border border-border mb-6">
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Agent Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Financial Analyst"
                  className="w-full bg-background px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description (Optional)</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="A brief description of what this agent does"
                  className="w-full bg-background px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Vibe Prompt *</label>
                <textarea
                  value={vibePrompt}
                  onChange={(e) => setVibePrompt(e.target.value)}
                  placeholder="Describe what you want your agent to do...

Example: Create a financial analyst agent that tracks AAPL and TSLA stock prices and sends me a Slack notification if either drops by 5%"
                  rows={6}
                  className="w-full bg-background px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary resize-none"
                  required
                  minLength={10}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Minimum 10 characters. Be specific about what the agent should do.
                </p>
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500 text-red-400 p-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isGenerating || !name || !vibePrompt || vibePrompt.length < 10}
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-3 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    Generating Agent... This may take 1-2 minutes
                  </span>
                ) : (
                  'Generate Agent with AI'
                )}
              </button>
            </form>
          </div>
        )}

        {/* Generated Agent Display */}
        {agent && (
          <div className="space-y-6">
            {/* Agent Info */}
            <div className="bg-muted p-6 rounded-lg border border-border">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-medium">{agent.name}</h2>
                  {agent.description && (
                    <p className="text-muted-foreground mt-1">{agent.description}</p>
                  )}
                </div>
                <span className={`px-3 py-1 text-sm rounded-full ${
                  agent.status === 'ready' ? 'bg-green-500/20 text-green-400' :
                  agent.status === 'generating' ? 'bg-blue-500/20 text-blue-400' :
                  agent.status === 'error' ? 'bg-red-500/20 text-red-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                </span>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowIntegrationModal(true)}
                  className="flex items-center gap-2 bg-primary/20 hover:bg-primary/30 text-primary px-4 py-2 rounded-md text-sm"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9V3m-9 9h18" />
                  </svg>
                  Integrations ({agent.integrations?.length || 0})
                </button>
                <button
                  onClick={() => setAgent(null)}
                  className="bg-muted-foreground/20 hover:bg-muted-foreground/30 text-foreground px-4 py-2 rounded-md text-sm"
                >
                  Create New Agent
                </button>
              </div>
            </div>

            {/* Architecture (Agent 1 Output) */}
            {agent.architecture && (
              <div className="bg-muted p-6 rounded-lg border border-border">
                <h3 className="text-lg font-medium mb-3">📐 Architecture (Agent 1: Architect)</h3>
                <pre className="text-sm bg-background p-4 rounded-md overflow-x-auto whitespace-pre-wrap">
                  {agent.architecture}
                </pre>
              </div>
            )}

            {/* Generated Code (Agent 2 Output) */}
            {agent.generated_code && (
              <div className="bg-muted p-6 rounded-lg border border-border">
                <h3 className="text-lg font-medium mb-3">💻 Generated Code (Agent 2: Coder)</h3>
                <pre className="text-sm bg-black/20 p-4 rounded-md overflow-x-auto font-mono max-h-96">
                  <code>{agent.generated_code}</code>
                </pre>
              </div>
            )}

            {/* Review Notes (Agent 3 Output) */}
            {agent.review_notes && (
              <div className="bg-muted p-6 rounded-lg border border-border">
                <h3 className="text-lg font-medium mb-3">✅ Review Notes (Agent 3: Reviewer)</h3>
                <pre className="text-sm bg-background p-4 rounded-md overflow-x-auto whitespace-pre-wrap">
                  {agent.review_notes}
                </pre>
              </div>
            )}

            {/* Final Code */}
            {agent.final_code && (
              <div className="bg-muted p-6 rounded-lg border border-border">
                <h3 className="text-lg font-medium mb-3">🎯 Final Code (Reviewed & Ready)</h3>
                <pre className="text-sm bg-black/20 p-4 rounded-md overflow-x-auto font-mono max-h-96">
                  <code>{agent.final_code}</code>
                </pre>
                <div className="flex gap-3 mt-4">
                  <button className="bg-green-500/20 hover:bg-green-500/30 text-green-400 px-4 py-2 rounded-md text-sm">
                    ⬇️ Download Code
                  </button>
                  <button className="bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 px-4 py-2 rounded-md text-sm">
                    🚀 Deploy
                  </button>
                </div>
              </div>
            )}

            {/* File Structure */}
            {agent.file_structure && agent.file_structure.length > 0 && (
              <div className="bg-muted p-6 rounded-lg border border-border">
                <h3 className="text-lg font-medium mb-3">📁 File Structure</h3>
                <div className="bg-background p-4 rounded-md font-mono text-sm">
                  {agent.file_structure.map((file: any, idx: number) => (
                    <div key={idx} className="text-muted-foreground">
                      {typeof file === 'string' ? file : file.path || file.name}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Integration Modal */}
      {showIntegrationModal && (
        <IntegrationModal
          integrations={integrations}
          onClose={() => setShowIntegrationModal(false)}
        />
      )}
    </div>
  );
};

export default AgentBuilderPage;
