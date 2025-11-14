import React from 'react';

const SidebarNav: React.FC = () => (
    <aside className="w-64 flex-shrink-0 hidden md:block">
        <div className="sticky top-24">
            <h3 className="mb-4 text-sm uppercase text-muted-foreground">Getting Started</h3>
            <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-primary">Introduction</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground">Installation</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground">Your First Agent</a></li>
            </ul>

            <h3 className="mb-4 mt-8 text-sm uppercase text-muted-foreground">Core Concepts</h3>
            <ul className="space-y-2 text-sm">
                <li><a href="#" className="text-muted-foreground hover:text-foreground">The Agent Loop</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground">Tools & Integrations</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground">Memory</a></li>
                <li><a href="#" className="text-muted-foreground hover:text-foreground">Deployment</a></li>
            </ul>
        </div>
    </aside>
);

const ArticleContent: React.FC = () => (
    <article className="prose prose-invert max-w-none">
        <div className="pb-4 mb-8 border-b border-border">
            <p className="text-sm text-muted-foreground">Getting Started &gt; Introduction</p>
            <h1 className="text-4xl text-foreground !mb-2">Introduction</h1>
            <p className="text-lg text-muted-foreground">Welcome to the VibeDeploy documentation.</p>
        </div>
        
        <p>VibeDeploy is an agentic framework designed to help you build, test, and deploy autonomous AI agents. Our goal is to provide a robust and flexible platform that abstracts away the complexities of agent development, allowing you to focus on creating intelligent and useful applications.</p>
        
        <h2 className="text-2xl text-foreground">Core Philosophy</h2>
        <p>We believe in a "vibe-driven" development process. You start with a high-level goal or "vibe," and our framework provides the tools to progressively add structure, logic, and integrations until you have a production-ready agent.</p>

        <h2 className="text-2xl text-foreground">Example Code</h2>
        <p>Here's a simple example of defining an agent in Python using our SDK:</p>
        <pre className="bg-muted p-4 rounded-md border border-border">
            <code>
{`from vibedeploy import Agent

agent = Agent(
    name="research_assistant",
    description="An agent that researches topics online.",
    vibe="Find the latest trends in AI for 2024."
)

agent.run()`}
            </code>
        </pre>
    </article>
);


const DocsPage: React.FC = () => {
  return (
    <div className="container mx-auto max-w-6xl px-6 py-12">
        <div className="flex gap-12">
            <SidebarNav />
            <main className="flex-grow">
                <ArticleContent />
            </main>
        </div>
    </div>
  );
};

export default DocsPage;