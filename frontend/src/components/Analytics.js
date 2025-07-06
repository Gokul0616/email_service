import React, { useState, useEffect } from 'react';

const Analytics = ({ backendUrl }) => {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [campaignAnalytics, setCampaignAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30'); // days

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard stats
      const dashboardResponse = await fetch(`${backendUrl}/api/analytics/dashboard`);
      const dashboardData = await dashboardResponse.json();
      setDashboardStats(dashboardData);

      // Load campaign analytics
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - parseInt(timeRange));
      
      const campaignResponse = await fetch(
        `${backendUrl}/api/analytics/campaigns?start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`
      );
      const campaignData = await campaignResponse.json();
      setCampaignAnalytics(campaignData);
      
    } catch (error) {
      console.error('Error loading analytics:', error);
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics & Performance</h1>
          <p className="text-gray-600">Track your email campaign performance and engagement metrics</p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-gray-700">Time Range:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 text-2xl">📧</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Sent</p>
              <p className="text-2xl font-bold text-gray-900">{campaignAnalytics?.total_sent || 0}</p>
              <p className="text-sm text-gray-500">from {campaignAnalytics?.total_campaigns || 0} campaigns</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <span className="text-green-600 text-2xl">👁️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Open Rate</p>
              <p className="text-2xl font-bold text-gray-900">{campaignAnalytics?.overall_open_rate?.toFixed(1) || 0}%</p>
              <p className="text-sm text-gray-500">{campaignAnalytics?.total_opens || 0} total opens</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 text-2xl">👆</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Click Rate</p>
              <p className="text-2xl font-bold text-gray-900">{campaignAnalytics?.overall_click_rate?.toFixed(1) || 0}%</p>
              <p className="text-sm text-gray-500">{campaignAnalytics?.total_clicks || 0} total clicks</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
              <span className="text-yellow-600 text-2xl">📊</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Engagement Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {((campaignAnalytics?.overall_open_rate || 0) + (campaignAnalytics?.overall_click_rate || 0) * 2).toFixed(0)}
              </p>
              <p className="text-sm text-gray-500">Composite score</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Performance Trends</h3>
          <p className="text-sm text-gray-600">Email performance over time</p>
        </div>
        <div className="p-6">
          <div className="h-64 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 text-2xl">📈</span>
              </div>
              <p className="text-gray-600 font-medium">Performance Chart</p>
              <p className="text-sm text-gray-500">Visual analytics coming soon</p>
            </div>
          </div>
        </div>
      </div>

      {/* Campaign Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performing Campaigns */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Top Performing Campaigns</h3>
            <p className="text-sm text-gray-600">Highest engagement rates</p>
          </div>
          <div className="p-6">
            {campaignAnalytics?.campaigns && campaignAnalytics.campaigns.length > 0 ? (
              <div className="space-y-4">
                {campaignAnalytics.campaigns
                  .sort((a, b) => (b.opened_count || 0) - (a.opened_count || 0))
                  .slice(0, 5)
                  .map((campaign, index) => {
                    const openRate = campaign.sent_count > 0 ? ((campaign.opened_count || 0) / campaign.sent_count * 100) : 0;
                    const clickRate = campaign.sent_count > 0 ? ((campaign.clicked_count || 0) / campaign.sent_count * 100) : 0;
                    
                    return (
                      <div key={campaign.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{campaign.name}</p>
                          <p className="text-sm text-gray-500">{campaign.sent_count || 0} sent</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-green-600">{openRate.toFixed(1)}% opens</p>
                          <p className="text-sm text-blue-600">{clickRate.toFixed(1)}% clicks</p>
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-gray-400">📧</span>
                </div>
                <p className="text-gray-500">No campaign data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Deliverability Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Deliverability Status</h3>
            <p className="text-sm text-gray-600">Email authentication and reputation</p>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-green-600 text-sm">✅</span>
                  </div>
                  <div>
                    <p className="font-medium text-green-800">Domain Authentication</p>
                    <p className="text-sm text-green-600">pixelrisewebco.com</p>
                  </div>
                </div>
                <span className="text-green-600 font-medium">Active</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-green-600 text-sm">🔐</span>
                  </div>
                  <div>
                    <p className="font-medium text-green-800">DKIM Signing</p>
                    <p className="text-sm text-green-600">Email authentication</p>
                  </div>
                </div>
                <span className="text-green-600 font-medium">Enabled</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-blue-600 text-sm">📊</span>
                  </div>
                  <div>
                    <p className="font-medium text-blue-800">Sender Reputation</p>
                    <p className="text-sm text-blue-600">Domain reputation score</p>
                  </div>
                </div>
                <span className="text-blue-600 font-medium">Good</span>
              </div>

              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-yellow-600 text-sm">⚠️</span>
                  </div>
                  <div>
                    <p className="font-medium text-yellow-800">Bounce Rate</p>
                    <p className="text-sm text-yellow-600">Keep below 2%</p>
                  </div>
                </div>
                <span className="text-yellow-600 font-medium">0.5%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Metrics</h3>
          <p className="text-sm text-gray-600">Comprehensive performance breakdown</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{dashboardStats?.total_contacts || 0}</div>
              <div className="text-sm text-gray-500">Total Contacts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{dashboardStats?.active_contacts || 0}</div>
              <div className="text-sm text-gray-500">Active Contacts</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{campaignAnalytics?.total_sent || 0}</div>
              <div className="text-sm text-gray-500">Emails Sent</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{campaignAnalytics?.total_opens || 0}</div>
              <div className="text-sm text-gray-500">Total Opens</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{campaignAnalytics?.total_clicks || 0}</div>
              <div className="text-sm text-gray-500">Total Clicks</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{dashboardStats?.total_unsubscribes || 0}</div>
              <div className="text-sm text-gray-500">Unsubscribes</div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Tips */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📈 Performance Tips</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">🎯 Improve Open Rates</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Use personalized subject lines</li>
              <li>• Test different send times</li>
              <li>• Keep subject lines under 50 characters</li>
              <li>• Avoid spam trigger words</li>
            </ul>
          </div>
          <div className="bg-white rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">👆 Boost Click Rates</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Use clear call-to-action buttons</li>
              <li>• Personalize email content</li>
              <li>• Segment your audience</li>
              <li>• A/B test different content</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;