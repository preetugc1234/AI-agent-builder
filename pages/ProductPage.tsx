import React from 'react';

const ProductPage: React.FC = () => {
  return (
    <div className="container mx-auto max-w-5xl px-6 py-12">
      <section className="text-center py-20">
        <h1 className="text-4xl md:text-5xl mb-4">How Vibe-to-Deploy Works</h1>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
          We've abstracted away the complexity of building and shipping AI agents, so you can focus on creating value.
        </p>
      </section>

      <section className="py-16">
        <h2 className="text-3xl text-center mb-12">From Idea to Production in 4 Steps</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-primary text-2xl font-bold mb-4">1</div>
            <h3 className="mb-2">Vibe</h3>
            <p className="text-sm text-muted-foreground">Describe your agent's goal in natural language.</p>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-primary text-2xl font-bold mb-4">2</div>
            <h3 className="mb-2">Generate</h3>
            <p className="text-sm text-muted-foreground">Our framework generates the agent's codebase and structure.</p>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-primary text-2xl font-bold mb-4">3</div>
            <h3 className="mb-2">Integrate</h3>
            <p className="text-sm text-muted-foreground">Connect to your data sources and tools with ease.</p>
          </div>
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center text-primary text-2xl font-bold mb-4">4</div>
            <h3 className="mb-2">Deploy</h3>
            <p className="text-sm text-muted-foreground">Launch your agent on our scalable infrastructure.</p>
          </div>
        </div>
      </section>

      <section className="py-16">
        <h2 className="text-3xl text-center mb-12">Built on a Modern, Scalable Stack</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {['Python', 'Supabase', 'Redis', 'Docker'].map(tech => (
            <div key={tech} className="bg-muted p-6 rounded-md border border-border text-center card-hover">
              <h3 className="text-lg">{tech}</h3>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16">
        <h2 className="text-3xl text-center mb-12">See It in Action</h2>
        <div className="aspect-video bg-muted rounded-md border border-border flex items-center justify-center text-muted-foreground card-hover">
          <p>Embedded Video / Demo Placeholder</p>
        </div>
      </section>

      <section className="py-16 text-center">
        <h2 className="text-3xl mb-4">Ready to build?</h2>
        <p className="text-muted-foreground mb-8">Start creating your first agent in minutes.</p>
        <button className="bg-primary text-primary-foreground px-8 py-3 rounded-md font-semibold card-hover text-lg">
          Get Started for Free
        </button>
      </section>
    </div>
  );
};

export default ProductPage;