import React, { useState, useEffect } from 'react';

const CampaignManager = ({ backendUrl }) => {
  const [view, setView] = useState('list'); // list, create, edit, view
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    html_content: '',
    from_email: 'campaigns@pixelrisewebco.com',
    from_name: 'PixelRise WebCo',
    reply_to: '',
    contact_lists: [],
    tags: [],
    send_immediately: false,
    scheduled_at: '',
    ab_test_percentage: 0,
    ab_test_subject_b: '',
    ab_test_content_b: ''
  });

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/campaigns`);
      const data = await response.json();
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Error loading campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCampaign = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/campaigns`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Campaign created successfully!');
        setView('list');
        loadCampaigns();
        resetForm();
      } else {
        alert(`Error: ${result.message}`);
      }
    } catch (error) {
      alert(`Error creating campaign: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendCampaign = async (campaignId) => {
    if (!confirm('Are you sure you want to send this campaign?')) return;
    
    try {
      setLoading(true);
      
      // First prepare the campaign
      const prepareResponse = await fetch(`${backendUrl}/api/campaigns/${campaignId}/prepare`, {
        method: 'POST'
      });
      const prepareResult = await prepareResponse.json();
      
      if (!prepareResult.success) {
        alert(`Error preparing campaign: ${prepareResult.message}`);
        return;
      }
      
      // Then send the campaign
      const sendResponse = await fetch(`${backendUrl}/api/campaigns/${campaignId}/send`, {
        method: 'POST'
      });
      const sendResult = await sendResponse.json();
      
      if (sendResult.success) {
        alert(`Campaign sent successfully! ${sendResult.message}`);
        loadCampaigns();
      } else {
        alert(`Error sending campaign: ${sendResult.message}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      subject: '',
      html_content: '',
      from_email: 'campaigns@pixelrisewebco.com',
      from_name: 'PixelRise WebCo',
      reply_to: '',
      contact_lists: [],
      tags: [],
      send_immediately: false,
      scheduled_at: '',
      ab_test_percentage: 0,
      ab_test_subject_b: '',
      ab_test_content_b: ''
    });
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-100 text-gray-800',
      scheduled: 'bg-blue-100 text-blue-800',
      sending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      paused: 'bg-red-100 text-red-800'
    };
    
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  if (view === 'create' || view === 'edit') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {view === 'create' ? 'Create Campaign' : 'Edit Campaign'}
            </h1>
            <p className="text-gray-600">Design and configure your email campaign</p>
          </div>
          <button
            onClick={() => setView('list')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Back to campaigns
          </button>
        </div>

        {/* Campaign Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6">
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Campaign Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter campaign name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Subject
                  </label>
                  <input
                    type="text"
                    value={formData.subject}
                    onChange={(e) => setFormData({...formData, subject: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter email subject"
                  />
                </div>
              </div>

              {/* Sender Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Email
                  </label>
                  <input
                    type="email"
                    value={formData.from_email}
                    onChange={(e) => setFormData({...formData, from_email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Name
                  </label>
                  <input
                    type="text"
                    value={formData.from_name}
                    onChange={(e) => setFormData({...formData, from_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Email Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Content
                </label>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <h4 className="font-medium text-blue-800 mb-2">📝 Personalization Variables</h4>
                  <p className="text-sm text-blue-600 mb-2">
                    Use these variables in your content to personalize emails:
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <code className="bg-white px-2 py-1 rounded">{'{{first_name}}'}</code>
                    <code className="bg-white px-2 py-1 rounded">{'{{last_name}}'}</code>
                    <code className="bg-white px-2 py-1 rounded">{'{{company}}'}</code>
                    <code className="bg-white px-2 py-1 rounded">{'{{email}}'}</code>
                  </div>
                </div>
                <textarea
                  value={formData.html_content}
                  onChange={(e) => setFormData({...formData, html_content: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="12"
                  placeholder="Hi {{first_name}},

I hope this email finds you well. I'm reaching out because I noticed that {{company}} might benefit from our services.

[Your message here]

Best regards,
{{from_name}}

P.S. If you'd prefer not to receive these emails, you can unsubscribe here: [unsubscribe_link]"
                />
              </div>

              {/* A/B Testing */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">A/B Testing (Optional)</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Test Percentage (0-50%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="50"
                      value={formData.ab_test_percentage}
                      onChange={(e) => setFormData({...formData, ab_test_percentage: parseInt(e.target.value) || 0})}
                      className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Percentage of recipients to include in variant B test
                    </p>
                  </div>
                  
                  {formData.ab_test_percentage > 0 && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Alternative Subject Line (Variant B)
                        </label>
                        <input
                          type="text"
                          value={formData.ab_test_subject_b}
                          onChange={(e) => setFormData({...formData, ab_test_subject_b: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder="Alternative subject line for testing"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Alternative Content (Variant B)
                        </label>
                        <textarea
                          value={formData.ab_test_content_b}
                          onChange={(e) => setFormData({...formData, ab_test_content_b: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          rows="6"
                          placeholder="Alternative content for testing"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Targeting */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">Targeting</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tags (comma-separated)
                    </label>
                    <input
                      type="text"
                      value={formData.tags.join(', ')}
                      onChange={(e) => setFormData({...formData, tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="prospects, leads, customers"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Target contacts with specific tags
                    </p>
                  </div>
                </div>
              </div>

              {/* Scheduling */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">Scheduling</h3>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="send_immediately"
                      checked={formData.send_immediately}
                      onChange={(e) => setFormData({...formData, send_immediately: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="send_immediately" className="text-sm text-gray-700">
                      Send immediately after creation
                    </label>
                  </div>
                  
                  {!formData.send_immediately && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Schedule for later
                      </label>
                      <input
                        type="datetime-local"
                        value={formData.scheduled_at}
                        onChange={(e) => setFormData({...formData, scheduled_at: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setView('list')}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={createCampaign}
                  disabled={loading || !formData.name || !formData.subject || !formData.html_content}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Creating...' : 'Create Campaign'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Email Campaigns</h1>
          <p className="text-gray-600">Manage and track your email campaigns</p>
        </div>
        <button
          onClick={() => setView('create')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Create Campaign
        </button>
      </div>

      {/* Campaign List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : campaigns.length === 0 ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📧</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns yet</h3>
            <p className="text-gray-500 mb-4">Create your first email campaign to get started</p>
            <button
              onClick={() => setView('create')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Campaign
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {campaigns.map((campaign) => (
              <div key={campaign.id} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">{campaign.name}</h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(campaign.status)}`}>
                        {campaign.status}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">{campaign.subject}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span>📤 {campaign.sent_count || 0} sent</span>
                      <span>👁️ {campaign.opened_count || 0} opens</span>
                      <span>👆 {campaign.clicked_count || 0} clicks</span>
                      <span>📊 {campaign.total_recipients || 0} recipients</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {campaign.status === 'draft' && (
                      <button
                        onClick={() => sendCampaign(campaign.id)}
                        className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
                      >
                        Send Now
                      </button>
                    )}
                    <button className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200 transition-colors">
                      View Stats
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignManager;