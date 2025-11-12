
import React, { useState } from 'react';

const AuthTab: React.FC<{ active: boolean; onClick: () => void; children: React.ReactNode }> = ({ active, onClick, children }) => (
  <button onClick={onClick} className={`w-full py-3 text-sm font-semibold transition-colors ${active ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}>
    {children}
  </button>
);

const InputField: React.FC<{ id: string; type: string; label: string; placeholder: string }> = ({ id, type, label, placeholder }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium mb-2">{label}</label>
        <input 
            type={type} 
            id={id} 
            placeholder={placeholder}
            className="w-full bg-muted/50 px-4 py-2 rounded-md border border-border focus:outline-none focus:border-primary" 
        />
    </div>
);


const LoginForm: React.FC = () => (
    <form className="space-y-6">
        <InputField id="email" type="email" label="Email" placeholder="you@example.com" />
        <InputField id="password" type="password" label="Password" placeholder="••••••••" />
        <div className="flex justify-between items-center text-sm">
            <a href="#" className="text-primary hover:underline">Forgot Password?</a>
        </div>
        <button type="submit" className="w-full bg-primary text-primary-foreground py-3 rounded-md font-semibold card-hover">
            Log In
        </button>
    </form>
);

const SignupForm: React.FC = () => (
    <form className="space-y-6">
        <InputField id="signup-email" type="email" label="Email" placeholder="you@example.com" />
        <InputField id="signup-password" type="password" label="Password" placeholder="Create a strong password" />
        <InputField id="signup-confirm-password" type="password" label="Confirm Password" placeholder="Confirm your password" />
        <button type="submit" className="w-full bg-primary text-primary-foreground py-3 rounded-md font-semibold card-hover">
            Create Account
        </button>
    </form>
);


const AuthPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState('login');

    return (
        <div className="flex items-center justify-center py-24">
            <div className="w-full max-w-md bg-muted p-8 rounded-md border border-border">
                <div className="grid grid-cols-2 gap-4 bg-background p-1 rounded-md border border-border mb-8">
                    <AuthTab active={activeTab === 'login'} onClick={() => setActiveTab('login')}>Log In</AuthTab>
                    <AuthTab active={activeTab === 'signup'} onClick={() => setActiveTab('signup')}>Sign Up</AuthTab>
                </div>
                
                {activeTab === 'login' ? <LoginForm /> : <SignupForm />}

                <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-border" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-muted px-2 text-muted-foreground">Or continue with</span>
                    </div>
                </div>

                <button className="w-full flex items-center justify-center gap-3 bg-foreground/5 text-foreground py-3 rounded-md font-semibold card-hover border border-border">
                   {/* Google Icon SVG */}
                   <svg className="w-5 h-5" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                       <path d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12s5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24s8.955,20,20,20s20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z" fill="#FFC107"/><path d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z" fill="#FF3D00"/><path d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.222,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z" fill="#4CAF50"/><path d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571l6.19,5.238C42.022,35.244,44,30.036,44,24C44,22.659,43.862,21.35,43.611,20.083z" fill="#1976D2"/>
                   </svg>
                    Google
                </button>
            </div>
        </div>
    );
};

export default AuthPage;
   