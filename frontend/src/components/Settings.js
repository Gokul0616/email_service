import React, { useState, useEffect } from 'react';

const Settings = ({ backendUrl }) => {
  const [activeTab, setActiveTab] = useState('domain');
  const [domainSetupGuide, setDomainSetupGuide] = useState(null);
  const [authCheckResult, setAuthCheckResult] = useState(null);
  const [dnsRecords, setDnsRecords] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testDomain, setTestDomain] = useState('pixelrisewebco.com');

  useEffect(() => {
    loadDomainSetupGuide();
    checkDomainAuth();
  }, []);

  const loadDomainSetupGuide = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/domain-setup-guide`);
      const data = await response.json();
      setDomainSetupGuide(data);
    } catch (error) {
      console.error('Error loading domain setup guide:', error);
    }
  };

  const checkDomainAuth = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/auth-check/${testDomain}`);
      const data = await response.json();
      setAuthCheckResult(data);
    } catch (error) {
      console.error('Error checking domain auth:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateDnsRecords = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/dns-records/${testDomain}`);
      const data = await response.json();
      setDnsRecords(data);
    } catch (error) {
      console.error('Error generating DNS records:', error);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'domain', name: 'Domain Setup', icon: '🌐' },
    { id: 'authentication', name: 'Authentication', icon: '🔐' },
    { id: 'dns', name: 'DNS Records', icon: '⚙️' },
    { id: 'deliverability', name: 'Deliverability', icon: '📬' },
    { id: 'general', name: 'General', icon: '⚙️' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Configure your cold email system for optimal performance</p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Domain Setup Tab */}
      {activeTab === 'domain' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Domain Configuration</h3>
              <p className="text-sm text-gray-600">Set up pixelrisewebco.com for cold email campaigns</p>
            </div>
            <div className="p-6">
              {domainSetupGuide && (
                <div className="space-y-6">
                  {/* Domain Registration Status */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-2">📋 Domain Registration Required</h4>
                    <p className="text-sm text-yellow-600 mb-3">
                      To use pixelrisewebco.com for cold email campaigns, you need to register this domain first.
                    </p>
                    <div className="space-x-3">
                      <a 
                        href="https://www.namecheap.com/domains/registration/results/?domain=pixelrisewebco.com" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-block bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700"
                      >
                        Register on Namecheap
                      </a>
                      <a 
                        href="https://www.godaddy.com/domains/searchresults.aspx?checkAvail=1&domainToCheck=pixelrisewebco.com" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-block bg-yellow-600 text-white px-4 py-2 rounded text-sm hover:bg-yellow-700"
                      >
                        Register on GoDaddy
                      </a>
                    </div>
                  </div>

                  {/* Setup Steps */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-2">Step 1: Register Domain</h4>
                      <p className="text-sm text-blue-600 mb-2">
                        <strong>Time:</strong> {domainSetupGuide.step_1_domain_registration?.estimated_time}<br/>
                        <strong>Cost:</strong> {domainSetupGuide.step_1_domain_registration?.cost}
                      </p>
                      <ul className="text-sm text-blue-600 space-y-1">
                        {domainSetupGuide.step_1_domain_registration?.instructions?.map((instruction, index) => (
                          <li key={index}>• {instruction}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-2">Step 2: DNS Configuration</h4>
                      <p className="text-sm text-green-600 mb-2">
                        <strong>Time:</strong> {domainSetupGuide.step_2_dns_configuration?.estimated_time}
                      </p>
                      <p className="text-sm text-green-600">
                        Configure SPF, DKIM, and DMARC records for email authentication
                      </p>
                    </div>

                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h4 className="font-medium text-purple-800 mb-2">Step 3: Email Setup</h4>
                      <p className="text-sm text-purple-600 mb-2">
                        <strong>Server:</strong> {domainSetupGuide.step_3_email_configuration?.server_settings?.smtp_server}
                      </p>
                      <p className="text-sm text-purple-600">
                        Configure email addresses and SMTP settings
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Authentication Tab */}
      {activeTab === 'authentication' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Email Authentication</h3>
              <p className="text-sm text-gray-600">Check and configure email authentication for your domain</p>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {/* Domain Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domain to Check
                  </label>
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={testDomain}
                      onChange={(e) => setTestDomain(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="yourdomain.com"
                    />
                    <button
                      onClick={checkDomainAuth}
                      disabled={loading}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                      {loading ? 'Checking...' : 'Check Auth'}
                    </button>
                  </div>
                </div>

                {/* Authentication Results */}
                {authCheckResult && (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-lg ${
                      authCheckResult.ready_for_sending ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                    }`}>
                      <h4 className={`font-medium mb-3 ${
                        authCheckResult.ready_for_sending ? 'text-green-800' : 'text-red-800'
                      }`}>
                        Authentication Status for {authCheckResult.domain}
                      </h4>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center ${
                            authCheckResult.authentication_status?.spf_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                          }`}>
                            {authCheckResult.authentication_status?.spf_configured ? '✅' : '❌'}
                          </div>
                          <p className="font-medium">SPF Record</p>
                          <p className="text-sm text-gray-500">Sender Policy Framework</p>
                        </div>
                        
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center ${
                            authCheckResult.authentication_status?.dkim_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                          }`}>
                            {authCheckResult.authentication_status?.dkim_configured ? '✅' : '❌'}
                          </div>
                          <p className="font-medium">DKIM Record</p>
                          <p className="text-sm text-gray-500">Email Signing</p>
                        </div>
                        
                        <div className="text-center">
                          <div className={`w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center ${
                            authCheckResult.authentication_status?.dmarc_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                          }`}>
                            {authCheckResult.authentication_status?.dmarc_configured ? '✅' : '❌'}
                          </div>
                          <p className="font-medium">DMARC Record</p>
                          <p className="text-sm text-gray-500">Policy Framework</p>
                        </div>
                      </div>
                    </div>

                    {authCheckResult.setup_required && authCheckResult.setup_required.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h4 className="font-medium text-blue-800 mb-2">Setup Required:</h4>
                        <ul className="text-sm text-blue-600 space-y-1">
                          {authCheckResult.setup_required.map((instruction, index) => (
                            <li key={index}>• {instruction}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DNS Records Tab */}
      {activeTab === 'dns' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">DNS Record Configuration</h3>
              <p className="text-sm text-gray-600">Generate and manage DNS records for email authentication</p>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {/* Generate DNS Records */}
                <div>
                  <button
                    onClick={generateDnsRecords}
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                  >
                    {loading ? 'Generating...' : 'Generate DNS Records'}
                  </button>
                </div>

                {/* DNS Records Display */}
                {dnsRecords && (
                  <div className="space-y-6">
                    {/* SPF Record */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-800 mb-3">SPF Record</h4>
                      <p className="text-sm text-blue-600 mb-3">
                        Add this TXT record to authorize email sending servers:
                      </p>
                      <div className="bg-white border rounded p-3 font-mono text-sm break-all">
                        <div><strong>Name:</strong> {dnsRecords.records?.spf?.name}</div>
                        <div><strong>Type:</strong> {dnsRecords.records?.spf?.type}</div>
                        <div><strong>Value:</strong> {dnsRecords.records?.spf?.value}</div>
                      </div>
                    </div>

                    {/* DKIM Record */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <h4 className="font-medium text-green-800 mb-3">DKIM Record</h4>
                      <p className="text-sm text-green-600 mb-3">
                        Add this TXT record for DKIM email signing:
                      </p>
                      <div className="bg-white border rounded p-3 font-mono text-sm break-all">
                        <div><strong>Name:</strong> {dnsRecords.records?.dkim?.name}</div>
                        <div><strong>Type:</strong> {dnsRecords.records?.dkim?.type}</div>
                        <div><strong>Value:</strong> {dnsRecords.records?.dkim?.value}</div>
                      </div>
                    </div>

                    {/* DMARC Record */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <h4 className="font-medium text-purple-800 mb-3">DMARC Record</h4>
                      <p className="text-sm text-purple-600 mb-3">
                        Add this TXT record for DMARC policy enforcement:
                      </p>
                      <div className="bg-white border rounded p-3 font-mono text-sm break-all">
                        <div><strong>Name:</strong> {dnsRecords.records?.dmarc?.name}</div>
                        <div><strong>Type:</strong> {dnsRecords.records?.dmarc?.type}</div>
                        <div><strong>Value:</strong> {dnsRecords.records?.dmarc?.value}</div>
                      </div>
                    </div>

                    {/* Setup Instructions */}
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <h4 className="font-medium text-yellow-800 mb-2">📋 Setup Instructions</h4>
                      <ol className="text-sm text-yellow-600 space-y-1 list-decimal list-inside">
                        <li>Log into your domain registrar's control panel</li>
                        <li>Navigate to DNS management or DNS settings</li>
                        <li>Add each record above as a new TXT record</li>
                        <li>Wait 24-48 hours for DNS propagation</li>
                        <li>Verify setup using the Authentication tab</li>
                      </ol>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Deliverability Tab */}
      {activeTab === 'deliverability' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Deliverability Optimization</h3>
              <p className="text-sm text-gray-600">Best practices for high email deliverability</p>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {/* Deliverability Score */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-lg font-semibold text-green-800">Deliverability Score</h4>
                      <p className="text-sm text-green-600">Based on current configuration</p>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-green-600">85/100</div>
                      <div className="text-sm text-green-500">Good</div>
                    </div>
                  </div>
                </div>

                {/* Best Practices */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-800 mb-3">✅ What You're Doing Right</h4>
                    <ul className="text-sm text-blue-600 space-y-2">
                      <li>• DKIM signing enabled</li>
                      <li>• Professional domain setup</li>
                      <li>• Unsubscribe links included</li>
                      <li>• Contact validation</li>
                    </ul>
                  </div>

                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-800 mb-3">⚠️ Areas for Improvement</h4>
                    <ul className="text-sm text-yellow-600 space-y-2">
                      <li>• Set up SPF record</li>
                      <li>• Configure DMARC policy</li>
                      <li>• Implement email warm-up</li>
                      <li>• Monitor sender reputation</li>
                    </ul>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-gray-50 rounded-lg p-6">
                  <h4 className="font-medium text-gray-900 mb-4">📋 Deliverability Recommendations</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h5 className="font-medium text-gray-800 mb-2">Email Content</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Maintain text-to-image ratio</li>
                        <li>• Avoid spam trigger words</li>
                        <li>• Use proper HTML structure</li>
                        <li>• Include plain text version</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-800 mb-2">Sending Practices</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Start with small volumes</li>
                        <li>• Gradually increase sending</li>
                        <li>• Monitor bounce rates</li>
                        <li>• Clean inactive contacts</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">General Settings</h3>
              <p className="text-sm text-gray-600">System configuration and preferences</p>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {/* System Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-3">System Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Version:</span>
                        <span className="font-medium">1.0.0</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Service:</span>
                        <span className="font-medium">Cold Email Pro</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Status:</span>
                        <span className="text-green-600 font-medium">✅ Active</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-3">Features Enabled</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <span className="text-green-600 mr-2">✅</span>
                        <span>Campaign Management</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-600 mr-2">✅</span>
                        <span>Contact Management</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-600 mr-2">✅</span>
                        <span>Email Templates</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-600 mr-2">✅</span>
                        <span>A/B Testing</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-green-600 mr-2">✅</span>
                        <span>Analytics & Tracking</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-3">🚀 Quick Setup</h4>
                  <p className="text-sm text-blue-600 mb-4">
                    Complete these steps to get your cold email system fully operational:
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-white rounded border">
                      <div>
                        <span className="font-medium text-gray-900">1. Register pixelrisewebco.com</span>
                        <p className="text-sm text-gray-500">Purchase and configure your domain</p>
                      </div>
                      <span className="text-yellow-600">⏳ Pending</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded border">
                      <div>
                        <span className="font-medium text-gray-900">2. Configure DNS Records</span>
                        <p className="text-sm text-gray-500">Set up SPF, DKIM, and DMARC</p>
                      </div>
                      <span className="text-yellow-600">⏳ Pending</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded border">
                      <div>
                        <span className="font-medium text-gray-900">3. Import Your Contacts</span>
                        <p className="text-sm text-gray-500">Upload your contact list</p>
                      </div>
                      <span className="text-yellow-600">⏳ Ready</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white rounded border">
                      <div>
                        <span className="font-medium text-gray-900">4. Create Your First Campaign</span>
                        <p className="text-sm text-gray-500">Design and send your first email</p>
                      </div>
                      <span className="text-yellow-600">⏳ Ready</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;