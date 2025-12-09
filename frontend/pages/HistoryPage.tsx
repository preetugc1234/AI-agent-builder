import React, { useState, useEffect } from 'react';
import { getAgents, getAnalytics, deleteAgent, type Agent, type Analytics } from '../services/api';

type AgentStatus = 'draft' | 'generating' | 'ready' | 'deployed' | 'error';

const StatusBadge: React.FC<{ status: AgentStatus }> = ({ status }) => {
  const colors: Record<AgentStatus, string> = {
    draft: 'bg-gray-500/20 text-gray-400',
    generating: 'bg-blue-500/20 text-blue-400',
    ready: 'bg-green-500/20 text-green-400',
    deployed: 'bg-purple-500/20 text-purple-400',
    error: 'bg-red-500/20 text-red-400',
  };

  const labels: Record<AgentStatus, string> = {
    draft: 'Draft',
    generating: 'Generating',
    ready: 'Ready',
    deployed: 'Deployed',
    error: 'Failed',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
      {labels[status]}
    </span>
  );
};

const AgentCard: React.FC<{
  agent: Agent;
  onDelete: (id: string) => void;
}> = ({ agent, onDelete }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete "${agent.name}"?`)) return;

    setIsDeleting(true);
    try {
      await onDelete(agent.id);
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete agent');
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="card-hover bg-muted p-5 rounded-md border border-border flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-foreground font-medium">{agent.name}</h3>
          <StatusBadge status={agent.status as AgentStatus} />
        </div>
        {agent.description && (
          <p className="text-sm text-muted-foreground mb-4">{agent.description}</p>
        )}
        <div className="space-y-2 text-sm text-muted-foreground">
          <div className="flex justify-between">
            <span>Created:</span>
            <span className="text-foreground">{formatDate(agent.created_at)}</span>
          </div>
          {agent.integrations && agent.integrations.length > 0 && (
            <div className="flex justify-between">
              <span>Integrations:</span>
              <span className="text-foreground">{agent.integrations.length}</span>
            </div>
          )}
        </div>
      </div>
      <div className="mt-6 flex gap-2">
        <button
          onClick={() => window.location.href = `/builder?agent=${agent.id}`}
          className="text-xs bg-primary/20 hover:bg-primary/40 text-primary px-3 py-1.5 rounded-md transition-colors w-full"
        >
          {agent.status === 'ready' || agent.status === 'deployed' ? 'View' : 'Edit'}
        </button>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="text-xs bg-red-500/20 hover:bg-red-500/40 text-red-400 px-3 py-1.5 rounded-md transition-colors w-full disabled:opacity-50"
        >
          {isDeleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  );
};

const HistoryPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch agents and analytics on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [agentsData, analyticsData] = await Promise.all([
        getAgents(),
        getAnalytics(),
      ]);

      setAgents(agentsData);
      setAnalytics(analyticsData);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    await deleteAgent(agentId);
    setAgents(agents.filter(a => a.id !== agentId));

    // Refresh analytics
    const newAnalytics = await getAnalytics();
    setAnalytics(newAnalytics);
  };

  // Filter agents by search query
  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (agent.description && agent.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="container mx-auto max-w-6xl px-6 py-12">
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-6xl px-6 py-12">
        <div className="bg-red-500/10 border border-red-500 text-red-400 p-4 rounded-md">
          <p className="font-medium">Error loading agents</p>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={loadData}
            className="mt-3 text-xs bg-red-500/20 hover:bg-red-500/30 px-3 py-1.5 rounded-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl mb-2">Agent Vault</h1>
      <p className="text-muted-foreground mb-8">Manage and monitor all your deployed agents.</p>

      {/* Analytics Overview */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-muted p-5 rounded-md border border-border">
            <div className="text-sm text-muted-foreground">Total Agents</div>
            <div className="text-2xl mt-1">{analytics.total_agents}</div>
          </div>
          <div className="bg-muted p-5 rounded-md border border-border">
            <div className="text-sm text-muted-foreground">Time Saved</div>
            <div className="text-2xl mt-1">{analytics.time_saved_hours} Hours</div>
          </div>
          <div className="bg-muted p-5 rounded-md border border-border">
            <div className="text-sm text-muted-foreground">Overall Success</div>
            <div className="text-2xl mt-1">{analytics.overall_success_rate}%</div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="flex gap-4 mb-6">
        <input
          type="search"
          placeholder="Search agents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-muted px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary"
        />
      </div>

      {/* Agents Grid */}
      {filteredAgents.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <p className="text-lg mb-4">
            {searchQuery ? 'No agents found matching your search' : 'No agents created yet'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => window.location.href = '/builder'}
              className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md"
            >
              Create Your First Agent
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onDelete={handleDeleteAgent} />
          ))}
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
