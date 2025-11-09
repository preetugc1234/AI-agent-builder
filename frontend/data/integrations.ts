
import React from 'react';

// FIX: Replaced JSX with React.createElement to be valid in a .ts file.
const integrationLogos: Record<string, React.ReactNode> = {
  Gmail: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, React.createElement('path', { fill: '#EA4335', d: 'M10 38h28v-2H10v2zm0-26v18h28V12H10zm23.4 2-11.4 8-11.4-8h22.8zM4 42V6h40v36H4z' })),
  Twilio: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg' }, React.createElement('circle', { cx: '12', cy: '12', r: '10', fill: '#F22F46' }), React.createElement('circle', { cx: '12', cy: '12', r: '3', stroke: 'white', strokeWidth: '2' })),
  Slack: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, 
    React.createElement('path', { fill: '#36C5F0', d: 'M14 18h4v12h-4z' }),
    React.createElement('path', { fill: '#2EB67D', d: 'M22 18h-4v-4c0-2.21 1.79-4 4-4h8v4h-8v4z' }),
    React.createElement('path', { fill: '#ECB22E', d: 'M30 30h-4V18h4z' }),
    React.createElement('path', { fill: '#E01E5A', d: 'M26 30h4v4c0 2.21-1.79 4-4 4h-8v-4h8v-4z' }),
    React.createElement('path', { fill: '#36C5F0', d: 'M18 14v-4h12v4z' }),
    React.createElement('path', { fill: '#2EB67D', d: 'M18 22v4c0 2.21-1.79 4-4 4v-8h4z' }),
    React.createElement('path', { fill: '#ECB22E', d: 'M30 34v4H18v-4z' }),
    React.createElement('path', { fill: '#E01E5A', d: 'M30 26v-4c0-2.21 1.79-4 4-4v8h-4z' })
  ),
  Supabase: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#3ECF8E', d: 'M24 4L4 14.5l20 10.5L44 14.5z' }),
    React.createElement('path', { fill: '#3ECF8E', opacity: '.5', d: 'M24 25L4 14.5V25l20 10.5L44 25V14.5z' }),
    React.createElement('path', { fill: '#3ECF8E', opacity: '.2', d: 'M24 46L4 35.5V25l20 10.5L44 25v10.5z' })
  ),
  "Google Sheets": React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#188038', d: 'M27 4h-6l-2 4h10z' }),
    React.createElement('path', { fill: '#0F9D58', d: 'M21 4h6v10h-6z' }),
    React.createElement('path', { fill: '#34A853', d: 'M10 14h28v20H10z' }),
    React.createElement('path', { fill: '#107C41', d: 'M10 34h28v2H10z' }),
    React.createElement('path', { d: 'M24 20h-4v8h4v-3h4v-2h-4v-3z', fill: '#fff' }),
    React.createElement('path', { d: 'M26 25h4v2h-4z', fill: '#fff' })
  ),
  Airtable: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#F7C434', d: 'M12 12h24v12H12z' }),
    React.createElement('path', { fill: '#FFB300', d: 'M12 24h12v12H12z' }),
    React.createElement('path', { fill: '#18BFFF', d: 'M24 24h12v12H24z' })
  ),
  Notion: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { d: 'M10 10h28v28H10z', fill: '#000' }),
    React.createElement('path', { d: 'M24 14v16.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V14h8zm-2 2h-4v14.5c0 1.1.9 2 2 2s2-.9 2-2V16zm12-2v20h-8v-4h6v-2h-6v-4h6v-2h-6v-4h6v-2h-6V14h8z', fill: '#fff' })
  ),
  OpenAI: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fillRule: 'evenodd', clipRule: 'evenodd', d: 'M24 44c11.046 0 20-8.954 20-20S35.046 4 24 4 4 12.954 4 24s8.954 20 20 20zM14 24c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10-10-4.477-10-10z', fill: '#00A67E' }),
    React.createElement('path', { d: 'M14 24c0 2.761 1.12 5.261 2.929 7.071L24 24l-7.071-7.071A9.954 9.954 0 0014 24z', fill: '#212121', fillOpacity: '.2' })
  ),
  LangChain: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#009688', d: 'M28 12h-8c-3.31 0-6 2.69-6 6s2.69 6 6 6h8v4h-8c-5.52 0-10-4.48-10-10s4.48-10 10-10h8v4z' }),
    React.createElement('path', { fill: '#8BC34A', d: 'M20 36h8c3.31 0 6-2.69 6-6s-2.69-6-6-6h-8v-4h8c5.52 0 10 4.48 10 10s-4.48 10-10 10h-8v-4z' })
  ),
  LangGraph: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, 
    React.createElement('g', { fill: 'none', strokeWidth: '2' },
      React.createElement('circle', { cx: '16', cy: '16', r: '3', stroke: '#8BC34A' }),
      React.createElement('circle', { cx: '32', cy: '16', r: '3', stroke: '#8BC34A' }),
      React.createElement('circle', { cx: '16', cy: '32', r: '3', stroke: '#009688' }),
      React.createElement('circle', { cx: '32', cy: '32', r: '3', stroke: '#009688' }),
      React.createElement('path', { stroke: '#8BC34A', d: 'M19 16h10' }),
      React.createElement('path', { stroke: '#009688', d: 'M19 32h10' }),
      React.createElement('path', { stroke: '#BDBDBD', d: 'M16 19v10M32 19v10' })
    )
  ),
  Vercel: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, React.createElement('path', { fill: '#fff', d: 'M24 4L4 40h40z' })),
  Docker: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#0db7ed', d: 'M44 24c0 2.21-1.79 4-4 4h-4v-8h4c2.21 0 4 1.79 4 4z' }),
    React.createElement('path', { fill: '#0db7ed', d: 'M4 24c0-5.523 4.477-10 10-10h14v20H14c-5.523 0-10-4.477-10-10z' }),
    React.createElement('path', { d: 'M14 18h4v4h-4zm6 0h4v4h-4zm6 0h4v4h-4zm-12 6h4v4h-4zm6 0h4v4h-4z', fill: '#fff' })
  ),
  Sentry: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' },
    React.createElement('path', { fill: '#FB4226', d: 'M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm0 30c-5.52 0-10-4.48-10-10s4.48-10 10-10 10 4.48 10 10-4.48 10-10 10z' }),
    React.createElement('circle', { cx: '24', cy: '24', r: '4', fill: '#fff' })
  ),
  Redis: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, React.createElement('path', { fill: '#D82C20', d: 'M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm-4 14h8v4h-8v-4zm0 6h8v4h-8v-4zm-4 4h16v4H16v-4z' })),
  Cloudflare: React.createElement('svg', { width: '24', height: '24', viewBox: '0 0 48 48' }, React.createElement('path', { fill: '#F38020', d: 'M24 4C12.95 4 4 12.95 4 24s8.95 20 20 20 20-8.95 20-20S35.05 4 24 4zm-6 14h12v4H18v-4zm0 6h12v4H18v-4z' })),
};

export type IntegrationCategory = 'Communication' | 'Data & Storage' | 'AI & ML' | 'DevOps';

export type Credential = {
  id: string;
  label: string;
  type: 'text' | 'password';
  placeholder: string;
};

export interface Integration {
  name: string;
  logo: React.ReactNode;
  description: string;
  category: IntegrationCategory;
  connected: boolean;
  setupGuide: string[];
  apiDocs: string;
  credentials: Credential[];
}

export const integrations: Integration[] = [
    {
        name: 'Slack',
        logo: integrationLogos['Slack'],
        description: 'Send notifications and messages to your Slack channels to keep your team updated on agent activities.',
        category: 'Communication',
        connected: true,
        setupGuide: [
            "Navigate to the Slack App Directory and create a new app.",
            "Enable 'Incoming Webhooks' for your app.",
            "Add a new webhook to your desired workspace and channel.",
            "Copy the generated Webhook URL and paste it into the credentials section.",
        ],
        apiDocs: "from vibedeploy.integrations import slack\n\nslack.send_message(\n  channel=\"#alerts\",\n  message=\"Agent run completed successfully.\"\n)",
        credentials: [{id: 'webhook_url', label: 'Webhook URL', type: 'password', placeholder: 'https://hooks.slack.com/services/...'}]
    },
    {
        name: 'Gmail',
        logo: integrationLogos['Gmail'],
        description: 'Enable your agents to read and send emails, perfect for automating customer support or outreach.',
        category: 'Communication',
        connected: false,
        setupGuide: ["Go to Google Cloud Console and create a new project.", "Enable the Gmail API.", "Create OAuth 2.0 credentials.", "Download the client secret JSON file and provide it here."],
        apiDocs: "from vibedeploy.integrations import gmail\n\ngmail.send_email(\n  to=\"user@example.com\",\n  subject=\"Update from your agent\",\n  body=\"Hello, this is an automated message.\"\n)",
        credentials: [{ id: 'client_secret', label: 'OAuth Client Secret', type: 'password', placeholder: 'Paste your JSON credentials here' }]
    },
     {
        name: 'Twilio',
        logo: integrationLogos['Twilio'],
        description: 'Send and receive SMS messages or make phone calls programmatically to interact with users.',
        category: 'Communication',
        connected: false,
        setupGuide: ["Log in to your Twilio Console.", "Find your Account SID and Auth Token on the dashboard.", "Copy and paste both credentials into the fields provided."],
        apiDocs: "from vibedeploy.integrations import twilio\n\ntwilio.send_sms(\n  to=\"+1...\",\n  from_=\"+1...\",\n  body=\"Your agent has an update for you!\"\n)",
        credentials: [
            { id: 'account_sid', label: 'Account SID', type: 'text', placeholder: 'AC...' },
            { id: 'auth_token', label: 'Auth Token', type: 'password', placeholder: 'Your Twilio auth token' }
        ]
    },
    {
        name: 'Supabase',
        logo: integrationLogos['Supabase'],
        description: 'Connect to your Supabase project to store and retrieve data, manage users, and more.',
        category: 'Data & Storage',
        connected: true,
        setupGuide: ["In your Supabase project settings, go to the 'API' section.", "Find your Project URL and anon public key.", "Copy both values into the fields below."],
        apiDocs: "from vibedeploy.integrations import supabase\n\nresponse = supabase.table('users').select('*').execute()",
        credentials: [
            { id: 'project_url', label: 'Project URL', type: 'text', placeholder: 'https://....supabase.co' },
            { id: 'anon_key', label: 'Anon (public) Key', type: 'password', placeholder: 'eyJ...' }
        ]
    },
    {
        name: 'Google Sheets',
        logo: integrationLogos['Google Sheets'],
        description: 'Read from and write to Google Sheets. Ideal for data logging, reporting, or simple databases.',
        category: 'Data & Storage',
        connected: false,
        setupGuide: ["Follow the Google Cloud instructions to enable the Sheets API.", "Create a service account and download the JSON key.", "Share your Google Sheet with the service account's email address."],
        apiDocs: "from vibedeploy.integrations import gsheets\n\ngsheets.append_row('MySheet', ['value1', 'value2'])",
        credentials: [{ id: 'service_account_json', label: 'Service Account JSON', type: 'password', placeholder: 'Paste your JSON credentials' }]
    },
    {
        name: 'Airtable',
        logo: integrationLogos['Airtable'],
        description: 'Use Airtable bases as a flexible database for your agents to read from and write to.',
        category: 'Data & Storage',
        connected: false,
        setupGuide: ["Go to your Airtable account page to find your API key.", "Provide the API key and the Base ID for the database you want to access."],
        apiDocs: "from vibedeploy.integrations import airtable\n\nrecords = airtable.get_all('MyTable')",
        credentials: [
            { id: 'api_key', label: 'API Key', type: 'password', placeholder: 'key...' },
            { id: 'base_id', label: 'Base ID', type: 'text', placeholder: 'app...' }
        ]
    },
    {
        name: 'Notion',
        logo: integrationLogos['Notion'],
        description: 'Connect to Notion to create, read, and update pages and databases within your workspaces.',
        category: 'Data & Storage',
        connected: false,
        setupGuide: ["Go to notion.so/my-integrations and create a new internal integration.", "Copy the 'Internal Integration Token'.", "Share the specific pages or databases you want to access with your new integration."],
        apiDocs: "from vibedeploy.integrations import notion\n\nnotion.pages.create(...)",
        credentials: [{ id: 'api_key', label: 'Internal Integration Token', type: 'password', placeholder: 'secret_...' }]
    },
    {
        name: 'Redis',
        logo: integrationLogos['Redis'],
        description: 'Use Redis as a fast, in-memory key-value store for caching or session management for your agents.',
        category: 'Data & Storage',
        connected: false,
        setupGuide: ["Obtain the connection URL for your Redis instance (e.g., from Upstash, Redis Labs, or your own server).", "The URL should include the username, password, host, and port.", "Paste the full connection URL below."],
        apiDocs: "from vibedeploy.integrations import redis\n\nredis.set('agent:status', 'running')",
        credentials: [{ id: 'redis_url', label: 'Redis Connection URL', type: 'password', placeholder: 'redis://user:pass@host:port' }]
    },
    {
        name: 'OpenAI',
        logo: integrationLogos['OpenAI'],
        description: 'Leverage powerful models from OpenAI like GPT-4 for advanced reasoning and content generation.',
        category: 'AI & ML',
        connected: true,
        setupGuide: ["Visit the OpenAI platform to get your API key.", "Copy the key and paste it below."],
        apiDocs: "from vibedeploy.integrations import openai\n\nresponse = openai.chat.completions.create(...) ",
        credentials: [{ id: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...' }]
    },
    {
        name: 'LangChain',
        logo: integrationLogos['LangChain'],
        description: 'Integrate with the LangChain ecosystem to build complex, stateful agent workflows.',
        category: 'AI & ML',
        connected: false,
        setupGuide: ["No direct connection needed, but you can configure LangSmith tracing.", "Get your LangSmith API key from your account settings."],
        apiDocs: "# No SDK call, but set environment variables:\n# LANGCHAIN_TRACING_V2=true\n# LANGCHAIN_API_KEY=...",
        credentials: [{ id: 'langsmith_api_key', label: 'LangSmith API Key (Optional)', type: 'password', placeholder: 'ls__...' }]
    },
    {
        name: 'LangGraph',
        logo: integrationLogos['LangGraph'],
        description: 'Build stateful, multi-agent applications with cycles using this powerful LangChain extension.',
        category: 'AI & ML',
        connected: false,
        setupGuide: ["LangGraph is a library that extends LangChain. No direct connection is needed.", "Simply import and use it within your agent's code.", "Enable LangSmith tracing to visualize your graphs."],
        apiDocs: "from langgraph.graph import StateGraph\n\n# Define your agent state and nodes\nworkflow = StateGraph(...)\n# ...add nodes and edges\napp = workflow.compile()",
        credentials: []
    },
    {
        name: 'Vercel',
        logo: integrationLogos['Vercel'],
        description: 'Deploy your agents and frontends seamlessly on Vercel for scalable, global hosting.',
        category: 'DevOps',
        connected: false,
        setupGuide: ["Go to your Vercel account settings and create a new access token.", "Paste the token below to allow VibeDeploy to manage deployments."],
        apiDocs: "# This integration is used via the Deploy button\n# in the Agent Builder UI.",
        credentials: [{ id: 'access_token', label: 'Vercel Access Token', type: 'password', placeholder: 'Your token...' }]
    },
    {
        name: 'Docker',
        logo: integrationLogos['Docker'],
        description: 'Containerize your agents for consistent, portable deployments across any environment.',
        category: 'DevOps',
        connected: false,
        setupGuide: ["This integration works locally with your Docker Desktop or Docker Engine.", "Ensure Docker is running on your machine before using Docker-based deployments."],
        apiDocs: "# Docker is used via the CLI or UI for local\n# builds and deployments. No API key required.",
        credentials: []
    },
     {
        name: 'Sentry',
        logo: integrationLogos['Sentry'],
        description: 'Capture errors and monitor the performance of your agents in real-time to ensure reliability.',
        category: 'DevOps',
        connected: false,
        setupGuide: ["Create a new project in your Sentry organization.", "Navigate to Project Settings > Client Keys (DSN).", "Copy the DSN and paste it below."],
        apiDocs: "# Sentry is configured via environment variables.\n# Set this in your agent's configuration.\nSENTRY_DSN=...",
        credentials: [{ id: 'sentry_dsn', label: 'Sentry DSN', type: 'password', placeholder: 'https://...@....sentry.io/...' }]
    },
    {
        name: 'Cloudflare',
        logo: integrationLogos['Cloudflare'],
        description: 'Manage Cloudflare resources like DNS, Workers, and R2 storage programmatically.',
        category: 'DevOps',
        connected: false,
        setupGuide: ["Log in to your Cloudflare dashboard.", "Go to My Profile > API Tokens and create a new token.", "Use a template like 'Edit Cloudflare Workers' or create a custom token with the necessary permissions.", "Copy the generated token and provide it here."],
        apiDocs: "from vibedeploy.integrations import cloudflare\n\ncloudflare.workers.deploy('my-agent-worker', ...)",
        credentials: [{ id: 'api_token', label: 'Cloudflare API Token', type: 'password', placeholder: 'Your API Token...' }]
    }
];

export const integrationCategories: IntegrationCategory[] = ['Communication', 'Data & Storage', 'AI & ML', 'DevOps'];
