import React from 'react';

// FIX: Define a union type for agent statuses to ensure type safety and reusability.
type AgentStatus = 'Running' | 'Success' | 'Failed';

const StatusBadge: React.FC<{ status: AgentStatus }> = ({ status }) => {
  const colors = {
    Running: 'bg-blue-500/20 text-blue-400',
    Success: 'bg-green-500/20 text-green-400',
    Failed: 'bg-red-500/20 text-red-400',
  };
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
      {status}
    </span>
  );
};

// FIX: Define a type for the Agent object to be used in AgentCard and the agents array.
type Agent = {
  name: string;
  lastRun: string;
  status: AgentStatus;
  successRate: number;
  timeSaved: string;
};

const AgentCard: React.FC<Agent> = (
  { name, lastRun, status, successRate, timeSaved }
) => (
  <div className="card-hover bg-muted p-5 rounded-md border border-border flex flex-col justify-between">
    <div>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-foreground">{name}</h3>
        <StatusBadge status={status} />
      </div>
      <div className="space-y-3 text-sm text-muted-foreground">
        <div className="flex justify-between"><span>Last Run:</span> <span className="text-foreground">{lastRun}</span></div>
        <div className="flex justify-between"><span>Success Rate:</span> <span className="text-foreground">{successRate}%</span></div>
        <div className="flex justify-between"><span>Time Saved:</span> <span className="text-foreground">{timeSaved}</span></div>
      </div>
    </div>
    <div className="mt-6 flex gap-2">
      <button className="text-xs bg-primary/20 hover:bg-primary/40 text-primary px-3 py-1.5 rounded-md transition-colors w-full">Edit</button>
      <button className="text-xs bg-muted-foreground/20 hover:bg-muted-foreground/40 text-muted-foreground px-3 py-1.5 rounded-md transition-colors w-full">Fork</button>
      <button className="text-xs bg-muted-foreground/20 hover:bg-muted-foreground/40 text-muted-foreground px-3 py-1.5 rounded-md transition-colors w-full">Deploy</button>
    </div>
  </div>
);

const HistoryPage: React.FC = () => {
  // FIX: Explicitly type the agents array with the Agent type to resolve the type mismatch.
  const agents: Agent[] = [
    { name: 'Financial Analyst', lastRun: '2h ago', status: 'Success', successRate: 98, timeSaved: '4.2h' },
    { name: 'Content Summarizer', lastRun: '5h ago', status: 'Success', successRate: 99, timeSaved: '11.5h' },
    { name: 'DevOps Manager', lastRun: '15m ago', status: 'Running', successRate: 92, timeSaved: '23.1h' },
    { name: 'Customer Support Bot V2', lastRun: '1d ago', status: 'Failed', successRate: 85, timeSaved: '150h' },
    { name: 'Code Refactor Agent', lastRun: '3d ago', status: 'Success', successRate: 96, timeSaved: '8.7h' },
    { name: 'Data Scraper', lastRun: '8h ago', status: 'Success', successRate: 100, timeSaved: '3.2h' },
  ];

  return (
    <div className="container mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-3xl mb-2">Agent Vault</h1>
      <p className="text-muted-foreground mb-8">Manage and monitor all your deployed agents.</p>
      
      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-muted p-5 rounded-md border border-border"><div className="text-sm text-muted-foreground">Total Agents</div><div className="text-2xl mt-1">6</div></div>
        <div className="bg-muted p-5 rounded-md border border-border"><div className="text-sm text-muted-foreground">Time Saved</div><div className="text-2xl mt-1">200.7 Hours</div></div>
        <div className="bg-muted p-5 rounded-md border border-border"><div className="text-sm text-muted-foreground">Overall Success</div><div className="text-2xl mt-1">95.2%</div></div>
      </div>
      
      {/* Search and Filters */}
      <div className="flex gap-4 mb-6">
        <input type="search" placeholder="Search agents..." className="w-full bg-muted px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary" />
        {/* Filter dropdowns would go here */}
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent, index) => <AgentCard key={index} {...agent} />)}
      </div>
    </div>
  );
};

export default HistoryPage;