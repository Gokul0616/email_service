import React, { useState, useEffect } from 'react';
import './App.css';

// Component imports
import Dashboard from './components/Dashboard';
import CampaignManager from './components/CampaignManager';
import ContactManager from './components/ContactManager';
import TemplateManager from './components/TemplateManager';
import Analytics from './components/Analytics';
import Settings from './components/Settings';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [user, setUser] = useState({
    name: 'PixelRise WebCo',
    email: 'admin@pixelrisewebco.com'
  });
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const navigationItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊', description: 'Overview & Analytics' },
    { id: 'campaigns', name: 'Campaigns', icon: '📧', description: 'Manage Email Campaigns' },
    { id: 'contacts', name: 'Contacts', icon: '👥', description: 'Contact Management' },
    { id: 'templates', name: 'Templates', icon: '📝', description: 'Email Templates' },
    { id: 'analytics', name: 'Analytics', icon: '📈', description: 'Campaign Performance' },
    { id: 'settings', name: 'Settings', icon: '⚙️', description: 'System Configuration' },
  ];

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard backendUrl={backendUrl} />;
      case 'campaigns':
        return <CampaignManager backendUrl={backendUrl} />;
      case 'contacts':
        return <ContactManager backendUrl={backendUrl} />;
      case 'templates':
        return <TemplateManager backendUrl={backendUrl} />;
      case 'analytics':
        return <Analytics backendUrl={backendUrl} />;
      case 'settings':
        return <Settings backendUrl={backendUrl} />;
      default:
        return <Dashboard backendUrl={backendUrl} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                    P
                  </div>
                  <span className="ml-2 text-xl font-bold text-gray-900">PixelRise WebCo</span>
                  <span className="ml-2 text-sm text-gray-500 bg-blue-100 px-2 py-1 rounded-full">Cold Email Pro</span>
                </div>
              </div>
            </div>

            {/* User Info */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">{user.name}</div>
                <div className="text-xs text-gray-500">{user.email}</div>
              </div>
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {user.name.charAt(0)}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm min-h-screen border-r border-gray-200">
          <div className="p-4">
            <div className="space-y-2">
              {navigationItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    activeView === item.id
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <span className="text-xl mr-3">{item.icon}</span>
                  <div className="text-left">
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-500">{item.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Domain Status */}
          <div className="p-4 border-t border-gray-200">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                <div className="text-sm font-medium text-green-800">pixelrisewebco.com</div>
              </div>
              <div className="text-xs text-green-600 mt-1">Domain Ready</div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
}

export default App;