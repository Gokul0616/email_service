import React, { useState, useEffect } from 'react';

const Dashboard = ({ backendUrl }) => {
  const [stats, setStats] = useState(null);
  const [recentCampaigns, setRecentCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard stats
      const statsResponse = await fetch(`${backendUrl}/api/analytics/dashboard`);
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Load recent campaigns
      const campaignsResponse = await fetch(`${backendUrl}/api/campaigns?limit=5`);
      const campaignsData = await campaignsResponse.json();
      setRecentCampaigns(campaignsData.campaigns || []);
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Welcome to Cold Email Pro</h1>
            <p className="text-blue-100 text-lg">
              Professional cold email campaigns with advanced analytics and deliverability optimization
            </p>
            <div className="mt-4 flex space-x-4">
              <div className="bg-white/20 rounded-lg px-4 py-2">
                <div className="text-xs text-blue-100">Domain Status</div>
                <div className="font-semibold">✅ pixelrisewebco.com</div>
              </div>
              <div className="bg-white/20 rounded-lg px-4 py-2">
                <div className="text-xs text-blue-100">Authentication</div>
                <div className="font-semibold">✅ DKIM Ready</div>
              </div>
            </div>
          </div>
          <div className="hidden lg:block">
            <img 
              src="https://images.unsplash.com/photo-1551721434-f5a13c7a6d14?w=400&h=300&fit=crop" 
              alt="Professional workspace"
              className="w-64 h-40 object-cover rounded-lg opacity-80"
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 font-bold">📧</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Campaigns</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_campaigns || 0}</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="text-green-600 text-sm font-medium">
              {stats?.active_campaigns || 0} active
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-green-600 font-bold">👥</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Contacts</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_contacts || 0}</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="text-green-600 text-sm font-medium">
              {stats?.active_contacts || 0} active
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 font-bold">📤</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Emails Sent</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_emails_sent || 0}</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="text-blue-600 text-sm font-medium">
              {stats?.overall_open_rate?.toFixed(1) || 0}% open rate
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-yellow-600 font-bold">📈</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Click Rate</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.overall_click_rate?.toFixed(1) || 0}%</p>
            </div>
          </div>
          <div className="mt-4">
            <span className="text-green-600 text-sm font-medium">
              {stats?.total_clicks || 0} total clicks
            </span>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Campaigns */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Campaigns</h3>
          </div>
          <div className="p-6">
            {recentCampaigns.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-gray-400 text-2xl">📧</span>
                </div>
                <p className="text-gray-500">No campaigns yet</p>
                <p className="text-sm text-gray-400">Create your first campaign to get started</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentCampaigns.map((campaign) => (
                  <div key={campaign.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{campaign.name}</p>
                      <p className="text-sm text-gray-500">{campaign.subject}</p>
                      <div className="flex items-center mt-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          campaign.status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : campaign.status === 'sending'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {campaign.status}
                        </span>
                        <span className="ml-2 text-xs text-gray-500">
                          {campaign.total_recipients} recipients
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {campaign.sent_count || 0} sent
                      </p>
                      <p className="text-xs text-gray-500">
                        {campaign.opened_count || 0} opens
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <button 
                onClick={() => window.location.hash = '#campaigns'}
                className="w-full flex items-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
                  📧
                </div>
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900">Create Campaign</p>
                  <p className="text-sm text-gray-500">Start a new email campaign</p>
                </div>
              </button>

              <button 
                onClick={() => window.location.hash = '#contacts'}
                className="w-full flex items-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors"
              >
                <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center text-white font-bold">
                  👥
                </div>
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900">Import Contacts</p>
                  <p className="text-sm text-gray-500">Upload your contact list</p>
                </div>
              </button>

              <button 
                onClick={() => window.location.hash = '#templates'}
                className="w-full flex items-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
              >
                <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
                  📝
                </div>
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900">Design Template</p>
                  <p className="text-sm text-gray-500">Create email templates</p>
                </div>
              </button>

              <button 
                onClick={() => window.location.hash = '#settings'}
                className="w-full flex items-center p-4 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors"
              >
                <div className="w-10 h-10 bg-yellow-600 rounded-lg flex items-center justify-center text-white font-bold">
                  ⚙️
                </div>
                <div className="ml-4 text-left">
                  <p className="font-medium text-gray-900">Setup Domain</p>
                  <p className="text-sm text-gray-500">Configure authentication</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Performance Overview</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats?.overall_open_rate?.toFixed(1) || 0}%</div>
              <div className="text-sm text-gray-500">Average Open Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats?.overall_click_rate?.toFixed(1) || 0}%</div>
              <div className="text-sm text-gray-500">Average Click Rate</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats?.total_emails_sent || 0}</div>
              <div className="text-sm text-gray-500">Total Emails Sent</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats?.total_unsubscribes || 0}</div>
              <div className="text-sm text-gray-500">Unsubscribes</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;