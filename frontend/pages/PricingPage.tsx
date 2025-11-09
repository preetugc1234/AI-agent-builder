import React, { useState, useMemo } from 'react';

const CheckIcon: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-primary flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

const LaunchIcon: React.FC = () => (
    <div className="text-primary">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="7" r="1.5" fill="currentColor" />
            <circle cx="17" cy="12" r="1.5" fill="currentColor" />
            <circle cx="12" cy="17" r="1.5" fill="currentColor" />
            <circle cx="7" cy="12" r="1.5" fill="currentColor" />
            <path d="M8.05 8.05L15.95 15.95" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
        </svg>
    </div>
);

const GrowIcon: React.FC = () => (
    <div className="text-primary">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="7" cy="7" r="1.5" fill="currentColor" />
            <circle cx="17" cy="7" r="1.5" fill="currentColor" />
            <circle cx="12" cy="12" r="1.5" fill="currentColor" />
            <circle cx="7" cy="17" r="1.5" fill="currentColor" />
            <circle cx="17" cy="17" r="1.5" fill="currentColor" />
            <path d="M8.05 8.05L15.95 15.95" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
            <path d="M15.95 8.05L8.05 15.95" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
        </svg>
    </div>
);

const ScaleIcon: React.FC = () => (
    <div className="text-primary">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="5" r="1.5" fill="currentColor" />
            <circle cx="12" cy="19" r="1.5" fill="currentColor" />
            <circle cx="5" cy="12" r="1.5" fill="currentColor" />
            <circle cx="19" cy="12" r="1.5" fill="currentColor" />
            <circle cx="8" cy="8" r="1.5" fill="currentColor" />
            <circle cx="16" cy="16" r="1.5" fill="currentColor" />
            <circle cx="16" cy="8" r="1.5" fill="currentColor" />
            <circle cx="8" cy="16" r="1.5" fill="currentColor" />
        </svg>
    </div>
);

const creditTiers = [
    { credits: 500, price: 29 }, { credits: 1000, price: 49 }, { credits: 1500, price: 69 },
    { credits: 2000, price: 89 }, { credits: 2500, price: 109 }, { credits: 3000, price: 129 },
    { credits: 3500, price: 149 },
];

const PricingPage: React.FC = () => {
    const [billingCycle, setBillingCycle] = useState('yearly');
    const [growPlanTier, setGrowPlanTier] = useState(creditTiers[0]);

    const getPrice = (monthlyPrice: number) => {
        return billingCycle === 'yearly' ? Math.round(monthlyPrice * 0.8) : monthlyPrice;
    };

    const growPrice = useMemo(() => getPrice(growPlanTier.price), [billingCycle, growPlanTier]);

    return (
        <div className="container mx-auto max-w-6xl px-6 py-12">
            <div className="text-center max-w-3xl mx-auto mb-12">
                <h1 className="text-4xl md:text-5xl mb-4">Pricing plans for every team</h1>
                <p className="text-lg text-muted-foreground">
                    Start for free and scale as you grow. All plans include our core agentic framework and deployment tools.
                </p>
            </div>

            <div className="flex justify-center items-center gap-4 mb-12">
                <span>Monthly</span>
                <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={billingCycle === 'yearly'} className="sr-only peer" onChange={() => setBillingCycle(p => p === 'monthly' ? 'yearly' : 'monthly')} />
                    <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
                <span>Yearly</span>
                <span className="text-xs text-primary bg-primary/10 px-3 py-1 rounded-full">SAVE 20%</span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                {/* Launch Plan */}
                <div className="p-8 rounded-lg border border-border bg-muted flex flex-col h-full">
                    <div className="flex items-center gap-3 mb-8">
                        <LaunchIcon />
                        <h3 className="text-xl">Launch</h3>
                    </div>
                    <div className="flex items-baseline mb-8">
                        <span className="text-5xl">$0</span>
                        <span className="text-sm text-muted-foreground ml-1.5">/ MONTH</span>
                    </div>
                    <ul className="space-y-3 mb-8 flex-grow">
                        {['10 executions / month', '150 free credits / month', 'Standard agent creation', 'Supabase integration', 'GitHub deployment'].map(feature => (
                            <li key={feature} className="flex items-start gap-3"><CheckIcon /><span className="text-sm">{feature}</span></li>
                        ))}
                    </ul>
                    <button className="w-full py-3 rounded-md font-semibold bg-foreground/10 hover:bg-foreground/20 text-foreground transition-colors">Start for free</button>
                </div>

                {/* Grow Plan */}
                <div className="p-8 rounded-lg border-2 border-primary bg-muted flex flex-col h-full relative lg:-top-3 shadow-2xl shadow-primary/10">
                    <div className="flex items-center gap-3 mb-8">
                        <GrowIcon />
                        <h3 className="text-xl">Grow</h3>
                    </div>
                    <div className="flex items-baseline mb-4">
                        <span className="text-5xl">${growPrice}</span>
                         <span className="text-sm text-muted-foreground ml-1.5">/ MONTH</span>
                    </div>
                    <div className="mb-8">
                        <select
                            value={growPlanTier.price}
                            onChange={(e) => setGrowPlanTier(creditTiers.find(t => t.price === parseInt(e.target.value))!)}
                            className="w-full bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            {creditTiers.map(tier => (
                                <option key={tier.credits} value={tier.price}>{tier.credits} credits / month</option>
                            ))}
                        </select>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">Everything in Launch, plus:</p>
                    <ul className="space-y-3 mb-8 flex-grow">
                        {['10,000 executions / month', 'Unlimited integrations', 'Custom UI Builder', 'Vercel & Render deployments', 'Priority Support & Error Resolution'].map(feature => (
                            <li key={feature} className="flex items-start gap-3"><CheckIcon /><span className="text-sm">{feature}</span></li>
                        ))}
                    </ul>
                    <button className="w-full py-3 rounded-md font-semibold bg-primary hover:bg-opacity-90 text-primary-foreground transition-colors">Get Started</button>
                </div>

                {/* Scale Plan */}
                <div className="p-8 rounded-lg border border-border bg-muted flex flex-col h-full">
                    <div className="flex items-center gap-3 mb-8">
                        <ScaleIcon />
                        <h3 className="text-xl">Scale</h3>
                    </div>
                    <div className="flex items-baseline mb-8">
                        <span className="text-5xl">Enterprise</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">Everything in Grow, plus:</p>
                    <ul className="space-y-3 mb-8 flex-grow">
                        {['Unlimited executions / month', 'Dedicated infrastructure', 'Advanced Security & Compliance', 'Custom model training', '24/7 enterprise-grade support'].map(feature => (
                            <li key={feature} className="flex items-start gap-3"><CheckIcon /><span className="text-sm">{feature}</span></li>
                        ))}
                    </ul>
                    <button className="w-full py-3 rounded-md font-semibold bg-foreground/10 hover:bg-foreground/20 text-foreground transition-colors">Contact Us</button>
                </div>
            </div>
        </div>
    );
};

export default PricingPage;