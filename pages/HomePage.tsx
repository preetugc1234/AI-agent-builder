import React from 'react';

const HeroSection: React.FC = () => (
  <section className="relative text-center py-20 md:py-32 overflow-hidden">
    {/* Container for all background effects */}
    <div aria-hidden="true" className="absolute inset-0 -z-10">
      {/* Grid pattern */}
      <div 
        className="absolute inset-0" 
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}
      />
      
      {/* Vivid Cyan and Pink rising glow effect */}
      <div 
        className="absolute bottom-0 left-1/2 h-2/3 w-full max-w-5xl -translate-x-1/2"
        style={{
          background: `radial-gradient(ellipse 40% 80% at 40% 100%, rgba(34, 211, 238, 0.5), transparent),
                       radial-gradient(ellipse 40% 80% at 60% 100%, rgba(244, 114, 182, 0.4), transparent)`,
          filter: 'blur(120px)',
        }}
      />
    </div>

    <div className="container mx-auto max-w-4xl px-6 relative z-10">
      <h1 className="text-4xl md:text-5xl mb-6 leading-[1.14]">Build Intelligent Workflows <br /> No Code, Limitless Possibilities.</h1>
      <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto mb-10">
        Describe your vision in plain English. Our AI takes care of the code, infrastructure, and deployment.
      </p>
      <div className="max-w-3xl mx-auto">
        <div className="bg-muted border border-border rounded-lg p-4 shadow-lg">
          <textarea
            className="w-full bg-transparent text-foreground placeholder-muted-foreground resize-none focus:outline-none text-lg"
            rows={4}
            placeholder="Ask to build..."
          ></textarea>
          <div className="flex justify-end items-center mt-3">
            <button className="bg-foreground/10 hover:bg-foreground/20 text-foreground p-2 rounded-md border border-border">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
);

const TrustLogos: React.FC = () => (
  <section className="py-24">
    <div className="container mx-auto max-w-6xl px-6">
      <p className="text-center text-xs tracking-widest text-muted-foreground mb-8">TRUSTED BY DEVELOPERS AT THE WORLD'S MOST INNOVATIVE COMPANIES</p>
      <div className="flex justify-around items-center gap-8 md:gap-12 flex-wrap">
        <span className="text-muted-foreground/80 font-semibold text-xl">Logoipsum</span>
        <span className="text-muted-foreground/80 font-semibold text-xl">Acme Corp</span>
        <span className="text-muted-foreground/80 font-semibold text-xl">Stark Industries</span>
        <span className="text-muted-foreground/80 font-semibold text-xl">Wayne Enterprises</span>
        <span className="text-muted-foreground/80 font-semibold text-xl">Cyberdyne</span>
      </div>
    </div>
  </section>
);

const TemplateCard: React.FC<{ title: string; description: string }> = ({ title, description }) => (
  <div className="card-hover bg-background p-6 rounded-md border border-border h-full flex flex-col">
    <div className="aspect-video bg-grid-pattern rounded-md mb-6 border border-border"></div>
    <h3 className="text-lg mb-2">{title}</h3>
    <p className="text-sm text-muted-foreground flex-grow">{description}</p>
    <button className="text-sm mt-4 text-primary font-semibold text-left">Use Template →</button>
  </div>
);

const TemplateGrid: React.FC = () => (
  <section className="py-24">
    <div className="container mx-auto max-w-6xl px-6">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-5xl">Start with a Proven Template</h2>
        <p className="text-muted-foreground mt-6 text-lg max-w-2xl mx-auto">Jumpstart your project with pre-built agents for common use cases.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <TemplateCard title="Customer Support Bot" description="Automate responses to common customer questions and issues." />
        <TemplateCard title="Data Extraction Agent" description="Scrape and structure data from websites and documents." />
        <TemplateCard title="Code Generation Assistant" description="Generate boilerplate code, write tests, and refactor." />
      </div>
    </div>
  </section>
);

const FeatureCard: React.FC<{ icon: React.ReactNode; title: string; description: string }> = ({ icon, title, description }) => (
  <div className="card-hover bg-background p-6 rounded-md border border-border">
    <div className="w-10 h-10 mb-4 flex items-center justify-center rounded-md bg-muted border border-border">
      {icon}
    </div>
    <h3 className="text-lg mb-2">{title}</h3>
    <p className="text-sm text-muted-foreground">{description}</p>
  </div>
);

const features = [
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>,
    title: "Code Generation",
    description: "From a simple prompt, generate robust Python code for your agent's core logic and tools."
  },
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.783-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>,
    title: "Managed Infrastructure",
    description: "We handle the servers, scaling, and dependencies, so you can focus purely on building."
  },
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
    title: "One-Click Deployment",
    description: "Go from local development to a live, scalable agent with a single command or click."
  },
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>,
    title: "Extensible Tooling",
    description: "Easily create and integrate custom tools. If you can write it in Python, you can add it to your agent."
  },
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>,
    title: "Full Observability",
    description: "Deeply understand your agent's behavior with built-in logging, tracing, and monitoring tools."
  },
  {
    icon: <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15.91 15.91a4.5 4.5 0 01-6.328 0M12 12v3.75m0-11.25V9" /></svg>,
    title: "Built-in Auth & Security",
    description: "Secure your agents and their data with enterprise-grade authentication and security features out of the box."
  }
];


const FeaturesSection: React.FC = () => (
  <section className="py-24">
    <div className="container mx-auto max-w-6xl px-6">
      <div className="text-center mb-16">
        <h2 className="text-3xl md:text-5xl">Your Complete Agent Toolkit</h2>
        <p className="text-muted-foreground mt-6 text-lg max-w-2xl mx-auto">Everything you need to ship robust, production-ready AI agents.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {features.map((feature, index) => (
          <FeatureCard key={index} {...feature} />
        ))}
      </div>
    </div>
  </section>
);

const CommentsIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <radialGradient id="comments-gradient" cx="0.5" cy="0.5" r="0.5" fx="0.25" fy="0.25">
                <stop offset="0%" stopColor="rgba(251, 191, 36, 1)" />
                <stop offset="100%" stopColor="rgba(239, 68, 68, 0.8)" />
            </radialGradient>
        </defs>
        <path d="M36 8H12C9.79086 8 8 9.79086 8 12V30C8 32.2091 9.79086 34 12 34H18.5L24 40L29.5 34H36C38.2091 34 40 32.2091 40 30V12C40 9.79086 38.2091 8 36 8Z" fill="url(#comments-gradient)" />
    </svg>
);

const TextEditorIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="text-editor-gradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#818CF8" />
                <stop offset="100%" stopColor="#3B82F6" />
            </linearGradient>
        </defs>
        <text x="24" y="36" fontFamily="sans-serif" fontSize="38" fontWeight="bold" textAnchor="middle" fill="url(#text-editor-gradient)">T</text>
    </svg>
);

const RealtimeAPIsIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="realtime-apis-gradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#F472B6" />
                <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
        </defs>
        <path d="M12 8H28C32.4183 8 36 11.5817 36 16V36H28V16H12V8Z" fill="url(#realtime-apis-gradient)" transform="translate(2 4)" />
    </svg>
);

const DashboardIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="dashboard-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
            </filter>
        </defs>
        <path d="M18 8L16 22H28L24 30L26 40L30 26H18L22 18L18 8Z" fill="white" opacity="0.3" filter="url(#dashboard-glow)" transform="translate(2 0)" />
        <path d="M18 8L16 22H28L24 30L26 40L30 26H18L22 18L18 8Z" fill="white" transform="translate(2 0)" />
    </svg>
);

const InfrastructureIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="infra-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="3" />
            </filter>
        </defs>
        <path d="M24 8L38.3137 16V32L24 40L9.6863 32V16L24 8Z" fill="white" opacity="0.3" filter="url(#infra-glow)" />
        <path d="M24 8L38.3137 16V32L24 40L9.6863 32V16L24 8Z" fill="white" />
    </svg>
);

const AIIntegrationsIcon = () => (
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="ai-gradient" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#A78BFA" />
                <stop offset="100%" stopColor="#34D399" />
            </linearGradient>
        </defs>
        <path d="M24 10C24 10 18 10 18 16C18 22 24 22 24 22M24 10C24 10 30 10 30 16C30 22 24 22 24 22M24 26C24 26 18 26 18 32C18 38 24 38 24 38M24 26C24 26 30 26 30 32C30 38 24 38 24 38M16 24C16 24 10 24 10 30C10 36 16 36 16 36M16 24C16 24 10 18 10 18C10 12 16 12 16 12M32 24C32 24 38 24 38 30C38 36 32 36 32 36M32 24C32 24 38 18 38 18C38 12 32 12 32 12" stroke="url(#ai-gradient)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

const toolkitFeatures = [
    {
        icon: <CommentsIcon />,
        title: 'Live chat with AI',
        description: 'Enable real-time, AI-powered conversations in your product.',
    },
    {
        icon: <TextEditorIcon />,
        title: 'Code Editor',
        description: 'A powerful editor with collaborative features for developers.',
        beta: true,
    },
    {
        icon: <RealtimeAPIsIcon />,
        title: 'Realtime APIs',
        description: 'Build any realtime collaborative experience.',
    },
    {
        icon: <DashboardIcon />,
        title: 'Dashboard',
        description: 'Monitor and manage your collaborative product.',
    },
    {
        icon: <InfrastructureIcon />,
        title: 'Infrastructure',
        description: 'Build, host, and scale your collaborative product.',
    },
    {
        icon: <AIIntegrationsIcon />,
        title: 'Integrations',
        description: 'Connect with tools like Supabase, AWS, Docker, LangChain, and OpenAI.',
    },
];

const CollaborationToolkit: React.FC = () => (
    <section className="py-32">
        <div className="container mx-auto max-w-6xl px-6">
            <div className="text-center mb-16">
                <p className="text-sm uppercase tracking-widest text-muted-foreground mb-4">MORE THAN JUST TEXT EDITOR</p>
                <h2 className="text-4xl md:text-5xl">A fully integrated collaboration toolkit</h2>
                <p className="text-muted-foreground mt-6 text-lg max-w-3xl mx-auto">
                    Engage users, fuel creativity, and drive growth with just a few lines of code. Ship collaborative features into your product in days, not months.
                </p>
            </div>

            <div className="rounded-lg overflow-hidden border border-border">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-border">
                    {toolkitFeatures.map(({ icon, title, description, beta }) => (
                        <div key={title} className="p-8 bg-background">
                            <div className="mb-6 h-12 w-12 flex items-center justify-center">{icon}</div>
                            <div className="flex items-center gap-2 mb-2">
                                <h3 className="text-lg">{title}</h3>
                                {beta && <span className="text-xs font-bold text-blue-400 bg-blue-500/20 px-2 py-0.5 rounded-full">BETA</span>}
                            </div>
                            <p className="text-sm text-muted-foreground">{description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    </section>
);


const testimonials = [
  {
    quote: "VibeDeploy is super easy to set up. Loving the modern approach the team is taking with supercharging our development workflow.",
    author: "Brelk Goin",
    title: "Founder of Hammr",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704d",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#A78BFA" /><path d="M2 17L12 22L22 17L12 12L2 17Z" fill="#fff" /></svg>
  },
  {
    quote: "Our team loves this. It makes shipping AI features so easy and reliable. After we switched, our deliverability improved tremendously.",
    author: "Vlad Matsiako",
    title: "Co-founder of Infisical",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704e",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" fill="#34D399" /></svg>
  },
  {
    quote: "I've used them all... Mailgun, Sendgrid, etc. and none of them come close to providing the amazing developer experience you get with VibeDeploy.",
    author: "Brandon Strittmatter",
    title: "Co-founder of Overload",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704f",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 4H20V20H4V4Z" fill="#F472B6" /></svg>
  },
  {
    quote: "This is the agentic framework I've been dreaming of. It cut my development time by 90% and the results are simply amazing.",
    author: "Jane Doe",
    title: "Lead AI Engineer, Future Systems",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704a",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L22 20H2L12 2Z" fill="#60A5FA" /></svg>
  },
  {
    quote: "The transition from a 'vibe' to a deployed agent is unbelievably smooth. The developer experience is second to none.",
    author: "John Smith",
    title: "Founder, AI Innovations Co.",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704b",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="4" width="16" height="16" rx="8" fill="#FBBF24" /></svg>
  },
  {
    quote: "VibeDeploy's one-click deployment saved us countless hours of DevOps work. We can now focus on what truly matters: building great products.",
    author: "Emily White",
    title: "CTO, ScaleUp",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704c",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 12L12 20L4 12L12 4L20 12Z" fill="#F87171" /></svg>
  },
  {
    quote: "The observability tools are top-notch. We can finally understand what our agents are doing under the hood. It's a game-changer for debugging.",
    author: "Michael Brown",
    title: "Staff Engineer, DataCorp",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704g",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 2L2 12L12 22L22 12L12 2Z" fill="#C084FC" /></svg>
  },
  {
    quote: "We integrated our entire data pipeline in a single afternoon. The flexibility of custom tools is just incredible. Cannot recommend enough.",
    author: "Sarah Green",
    title: "Head of AI, QuantumLeap",
    avatarUrl: "https://i.pravatar.cc/40?u=a042581f4e29026704h",
    companyLogo: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12Z" fill="#4ADE80" /><path d="M7 12L12 7L17 12L12 17L7 12Z" fill="#0A0A0A" /></svg>
  },
];

const TestimonialCard: React.FC<{ quote: string; author: string; title: string; avatarUrl: string; companyLogo: React.ReactNode }> = ({ quote, author, title, avatarUrl, companyLogo }) => (
  <div className="testimonial-card-fade flex-shrink-0 w-[400px] bg-muted p-8 rounded-lg border border-border mr-6">
    <p className="text-foreground mb-6 h-24">"{quote}"</p>
    <div className="flex items-center gap-4">
      <div className="relative flex-shrink-0">
        <img src={avatarUrl} alt={author} className="w-10 h-10 rounded-full" />
        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-background rounded-full flex items-center justify-center border border-border">
          {companyLogo}
        </div>
      </div>
      <div>
        <p className="font-semibold text-sm">{author}</p>
        <p className="text-xs text-muted-foreground">{title}</p>
      </div>
    </div>
  </div>
);

const Testimonials: React.FC = () => {
  const firstRow = testimonials.slice(0, 4);
  const secondRow = testimonials.slice(4, 8);

  return (
    <section className="py-32 overflow-hidden">
      <div className="container mx-auto max-w-6xl px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl">Beyond expectations</h2>
          <p className="text-muted-foreground mt-6 text-lg max-w-3xl mx-auto">
            VibeDeploy is driving remarkable developer experiences that enable success stories, empower businesses, and fuel growth across industries and individuals.
          </p>
        </div>
      </div>
      <div className="relative marquee-container">
        <div className="flex animate-marquee-left space-x-6 py-3">
          {[...firstRow, ...firstRow].map((t, i) => <TestimonialCard key={`first-${i}`} {...t} />)}
        </div>
        <div className="flex animate-marquee-right space-x-6 py-3">
          {[...secondRow, ...secondRow].map((t, i) => <TestimonialCard key={`second-${i}`} {...t} />)}
        </div>
      </div>
    </section>
  );
};


const FinalCTA: React.FC = () => (
    <section className="py-32">
        <div className="container relative mx-auto max-w-3xl px-6 text-center">
            <div
                aria-hidden="true"
                className="absolute inset-x-0 bottom-0 -z-10"
                style={{
                    height: '300px',
                    background: 'radial-gradient(ellipse 50% 80% at 50% 100%, rgba(255, 255, 255, 0.1), transparent)',
                    filter: 'blur(100px)',
                }}
            />
            <div className="relative z-10">
                <h2 className="text-3xl md:text-5xl">Ready to Build Your First Agent?</h2>
                <p className="text-muted-foreground mt-6 text-lg mb-8">Get started for free. Deploy your first agent in under 5 minutes.</p>
                <button className="bg-primary text-primary-foreground px-8 py-3 rounded-md font-semibold card-hover text-lg">
                    Start Building Now
                </button>
            </div>
        </div>
    </section>
);


const HomePage: React.FC = () => {
  return (
    <div>
      <HeroSection />
      <TrustLogos />
      <TemplateGrid />
      <FeaturesSection />
      <CollaborationToolkit />
      <Testimonials />
      <FinalCTA />
    </div>
  );
};

export default HomePage;