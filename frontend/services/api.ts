/**
 * API Service - Centralized API calls to NodeRush backend
 * Handles authentication, error handling, and type safety
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types based on backend schemas
export interface User {
  id: string;
  email: string;
  subscription_tier: string;
  subscription_status: string;
  created_at: string;
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  vibe_prompt: string;
  architecture?: string;
  generated_code?: string;
  review_notes?: string;
  final_code?: string;
  file_structure?: any[];
  docker_image_url?: string;
  status: string; // draft, generating, ready, deployed, error
  integrations: string[];
  flow_data: any;
  created_at: string;
  updated_at?: string;
}

export interface AgentCreate {
  name: string;
  description?: string;
  vibe_prompt: string;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  vibe_prompt?: string;
  status?: string;
}

export interface AgentGenerateRequest {
  name: string;
  description?: string;
  vibe_prompt: string;
}

export interface Analytics {
  total_agents: number;
  time_saved_hours: number;
  overall_success_rate: number;
  total_executions: number;
}

/**
 * Get authorization header with JWT token
 */
function getAuthHeader(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('No authentication token found');
  }
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

/**
 * Handle API errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// ============= Agent API =============

/**
 * Get all agents for the current user
 */
export async function getAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_URL}/api/agents`, {
    headers: getAuthHeader(),
  });
  return handleResponse<Agent[]>(response);
}

/**
 * Get a specific agent by ID
 */
export async function getAgent(agentId: string): Promise<Agent> {
  const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
    headers: getAuthHeader(),
  });
  return handleResponse<Agent>(response);
}

/**
 * Create a new agent
 */
export async function createAgent(data: AgentCreate): Promise<Agent> {
  const response = await fetch(`${API_URL}/api/agents`, {
    method: 'POST',
    headers: getAuthHeader(),
    body: JSON.stringify(data),
  });
  return handleResponse<Agent>(response);
}

/**
 * Update an existing agent
 */
export async function updateAgent(agentId: string, data: AgentUpdate): Promise<Agent> {
  const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
    method: 'PUT',
    headers: getAuthHeader(),
    body: JSON.stringify(data),
  });
  return handleResponse<Agent>(response);
}

/**
 * Delete an agent
 */
export async function deleteAgent(agentId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/agents/${agentId}`, {
    method: 'DELETE',
    headers: getAuthHeader(),
  });
  return handleResponse<void>(response);
}

/**
 * Generate code for an existing agent using 3-agent workflow
 */
export async function generateAgentCode(agentId: string): Promise<any> {
  const response = await fetch(`${API_URL}/api/agents/${agentId}/generate-code`, {
    method: 'POST',
    headers: getAuthHeader(),
  });
  return handleResponse<any>(response);
}

/**
 * Create and generate agent in one call
 */
export async function generateNewAgent(data: AgentGenerateRequest): Promise<any> {
  const response = await fetch(`${API_URL}/api/agents/generate`, {
    method: 'POST',
    headers: getAuthHeader(),
    body: JSON.stringify(data),
  });
  return handleResponse<any>(response);
}

/**
 * Get user analytics
 */
export async function getAnalytics(): Promise<Analytics> {
  const response = await fetch(`${API_URL}/api/analytics`, {
    headers: getAuthHeader(),
  });
  return handleResponse<Analytics>(response);
}

// ============= Auth API (for reference) =============

/**
 * Login user
 */
export async function login(email: string, password: string): Promise<{ access_token: string; user: User }> {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(response);
}

/**
 * Register new user
 */
export async function register(email: string, password: string): Promise<User> {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse(response);
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  const response = await fetch(`${API_URL}/api/auth/logout`, {
    method: 'POST',
    headers: getAuthHeader(),
  });
  return handleResponse(response);
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: getAuthHeader(),
  });
  return handleResponse(response);
}
