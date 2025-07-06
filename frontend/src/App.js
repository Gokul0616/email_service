import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    to_email: '',
    from_email: '',
    from_name: '',
    subject: '',
    body: '',
    is_html: false
  });
  
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [mxTestResult, setMxTestResult] = useState(null);
  const [mxTestDomain, setMxTestDomain] = useState('');
  const [receivedEmails, setReceivedEmails] = useState([]);
  const [serverStatus, setServerStatus] = useState(null);
  const [dnsRecords, setDnsRecords] = useState(null);
  const [dnsTestDomain, setDnsTestDomain] = useState('');
  const [authCheckResult, setAuthCheckResult] = useState(null);
  const [authCheckDomain, setAuthCheckDomain] = useState('');
  const [activeTab, setActiveTab] = useState('send');
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Load data on component mount
  useEffect(() => {
    loadReceivedEmails();
    loadServerStatus();
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSendEmail = async (e) => {
    e.preventDefault();
    setSending(true);
    setResult(null);
    
    try {
      const response = await fetch(`${backendUrl}/api/send-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResult({
          success: data.success,
          message: data.message,
          messageId: data.message_id
        });
        
        if (data.success) {
          // Clear form on success
          setFormData({
            to_email: '',
            from_email: '',
            from_name: '',
            subject: '',
            body: '',
            is_html: false
          });
        }
      } else {
        setResult({
          success: false,
          message: data.detail || 'Failed to send email'
        });
      }
    } catch (error) {
      setResult({
        success: false,
        message: `Network error: ${error.message}`
      });
    } finally {
      setSending(false);
    }
  };

  const handleMxTest = async (e) => {
    e.preventDefault();
    if (!mxTestDomain) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/test-mx/${mxTestDomain}`);
      const data = await response.json();
      
      if (response.ok) {
        setMxTestResult({
          success: true,
          domain: data.domain,
          mx_records: data.mx_records
        });
      } else {
        setMxTestResult({
          success: false,
          message: data.detail || 'Failed to lookup MX records'
        });
      }
    } catch (error) {
      setMxTestResult({
        success: false,
        message: `Network error: ${error.message}`
      });
    }
  };

  const loadReceivedEmails = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/received-emails`);
      const data = await response.json();
      
      if (response.ok) {
        setReceivedEmails(data.emails || []);
      }
    } catch (error) {
      console.error('Error loading received emails:', error);
    }
  };

  const loadServerStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/server-status`);
      const data = await response.json();
      
      if (response.ok) {
        setServerStatus(data);
      }
    } catch (error) {
      console.error('Error loading server status:', error);
    }
  };

  const handleDnsRecordsTest = async (e) => {
    e.preventDefault();
    if (!dnsTestDomain) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/dns-records/${dnsTestDomain}`);
      const data = await response.json();
      
      if (response.ok) {
        setDnsRecords(data);
      } else {
        setDnsRecords({
          error: data.detail || 'Failed to get DNS records'
        });
      }
    } catch (error) {
      setDnsRecords({
        error: `Network error: ${error.message}`
      });
    }
  };

  const handleAuthCheck = async (e) => {
    e.preventDefault();
    if (!authCheckDomain) return;
    
    try {
      const response = await fetch(`${backendUrl}/api/auth-check/${authCheckDomain}`);
      const data = await response.json();
      
      if (response.ok) {
        setAuthCheckResult(data);
      } else {
        setAuthCheckResult({
          error: data.detail || 'Failed to check domain authentication'
        });
      }
    } catch (error) {
      setAuthCheckResult({
        error: `Network error: ${error.message}`
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            📧 Professional Email Service Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Complete email delivery service with multi-method delivery, DKIM authentication, 
            and Gmail/Yahoo compatibility. Built like SendGrid but fully customizable.
          </p>
          <div className="mt-4 flex justify-center space-x-4">
            <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
              ✅ Gmail Compatible
            </span>
            <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
              ✅ Professional Delivery
            </span>
            <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
              ✅ Multi-Method Relay
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-6xl mx-auto mb-8">
          <div className="flex flex-wrap justify-center space-x-2 mb-6">
            {[
              { key: 'send', label: '📤 Send Email', icon: '📤' },
              { key: 'auth', label: '🔐 Auth Check', icon: '🔐' },
              { key: 'mx', label: '🔍 MX Lookup', icon: '🔍' },
              { key: 'received', label: '📥 Received', icon: '📥' },
              { key: 'dns', label: '⚙️ DNS Setup', icon: '⚙️' },
              { key: 'status', label: '📊 Status', icon: '📊' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-blue-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-6xl mx-auto">
          {/* Send Email Tab */}
          {activeTab === 'send' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="bg-blue-100 text-blue-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                  📤
                </span>
                Send Email with DKIM Authentication
              </h2>
              
              {/* Authentication Notice */}
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                    💡
                  </div>
                  <div>
                    <h3 className="font-bold text-blue-800 mb-1">Email Authentication Tips</h3>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• <strong>Use your own domain</strong> for the "From" address (not Gmail/Yahoo/Outlook)</li>
                      <li>• Check the <strong>"Auth Check"</strong> tab to verify your domain's authentication status</li>
                      <li>• Use the <strong>"DNS Setup"</strong> tab to get the required DNS records for your domain</li>
                      <li>• Major email providers require SPF, DKIM, and DMARC records to accept emails</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <form onSubmit={handleSendEmail} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      To Email Address
                    </label>
                    <input
                      type="email"
                      name="to_email"
                      value={formData.to_email}
                      onChange={handleInputChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="recipient@gmail.com"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Email Address
                    </label>
                    <input
                      type="email"
                      name="from_email"
                      value={formData.from_email}
                      onChange={handleInputChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="sender@yourdomain.com"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Name
                  </label>
                  <input
                    type="text"
                    name="from_name"
                    value={formData.from_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Your Name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subject
                  </label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Email subject"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message Body
                  </label>
                  <textarea
                    name="body"
                    value={formData.body}
                    onChange={handleInputChange}
                    required
                    rows="6"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your message here..."
                  />
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_html"
                    id="is_html"
                    checked={formData.is_html}
                    onChange={handleInputChange}
                    className="mr-2"
                  />
                  <label htmlFor="is_html" className="text-sm text-gray-700">
                    HTML Message
                  </label>
                </div>
                
                <button
                  type="submit"
                  disabled={sending}
                  className={`w-full py-3 px-4 rounded-md font-medium text-white transition-colors ${
                    sending
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
                  }`}
                >
                  {sending ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Sending with DKIM...
                    </div>
                  ) : (
                    'Send Email with Authentication'
                  )}
                </button>
              </form>
              
              {/* Email Result */}
              {result && (
                <div className={`mt-6 p-4 rounded-md ${
                  result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="flex items-center">
                    <div className={`w-5 h-5 rounded-full mr-3 ${
                      result.success ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div>
                      <p className={`font-medium ${
                        result.success ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {result.success ? 'Success!' : 'Error'}
                      </p>
                      <p className={`text-sm ${
                        result.success ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {result.message}
                      </p>
                      {result.messageId && (
                        <p className="text-xs text-green-500 mt-1">
                          Message ID: {result.messageId}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Authentication Check Tab */}
          {activeTab === 'auth' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="bg-red-100 text-red-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                  🔐
                </span>
                Email Authentication Checker
              </h2>
              
              {/* Authentication Warning */}
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg mb-6">
                <h3 className="font-bold text-yellow-800 mb-2">⚠️ Important: Email Authentication Required</h3>
                <p className="text-sm text-yellow-700 mb-2">
                  Major email providers (Gmail, Yahoo, Outlook) require proper email authentication to prevent spam. 
                  You need to set up SPF, DKIM, and DMARC records for your domain.
                </p>
                <ul className="text-sm text-yellow-700 list-disc list-inside">
                  <li><strong>Use your own domain</strong> - Don't send FROM Gmail/Yahoo addresses</li>
                  <li><strong>Set up DNS records</strong> - Configure SPF, DKIM, and DMARC</li>
                  <li><strong>Domain verification</strong> - Verify domain ownership with email providers</li>
                </ul>
              </div>
              
              <form onSubmit={handleAuthCheck} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Check Domain Authentication Status
                  </label>
                  <input
                    type="text"
                    value={authCheckDomain}
                    onChange={(e) => setAuthCheckDomain(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder="yourdomain.com"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 px-4 bg-red-600 text-white rounded-md font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Check Authentication Status
                </button>
              </form>
              
              {/* Authentication Check Result */}
              {authCheckResult && !authCheckResult.error && (
                <div className="mt-6 space-y-4">
                  <div className={`p-4 rounded-lg ${
                    authCheckResult.ready_for_sending ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    <h3 className={`font-bold mb-2 ${
                      authCheckResult.ready_for_sending ? 'text-green-800' : 'text-red-800'
                    }`}>
                      Authentication Status for {authCheckResult.domain}
                    </h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                          authCheckResult.authentication_status.spf_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                        }`}>
                          {authCheckResult.authentication_status.spf_configured ? '✅' : '❌'}
                        </div>
                        <p className="font-medium">SPF</p>
                      </div>
                      <div className="text-center">
                        <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                          authCheckResult.authentication_status.dkim_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                        }`}>
                          {authCheckResult.authentication_status.dkim_configured ? '✅' : '❌'}
                        </div>
                        <p className="font-medium">DKIM</p>
                      </div>
                      <div className="text-center">
                        <div className={`w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center ${
                          authCheckResult.authentication_status.dmarc_configured ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                        }`}>
                          {authCheckResult.authentication_status.dmarc_configured ? '✅' : '❌'}
                        </div>
                        <p className="font-medium">DMARC</p>
                      </div>
                    </div>
                  </div>
                  
                  {authCheckResult.setup_required.length > 0 && (
                    <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                      <h4 className="font-bold text-blue-800 mb-2">Setup Required:</h4>
                      <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
                        {authCheckResult.setup_required.map((instruction, index) => (
                          <li key={index}>{instruction}</li>
                        ))}
                      </ul>
                      <p className="text-sm text-blue-600 mt-2">
                        Use the "DNS Setup" tab to generate the required DNS records for your domain.
                      </p>
                    </div>
                  )}
                  
                  {authCheckResult.existing_records.spf && (
                    <div className="bg-gray-50 p-3 rounded">
                      <h5 className="font-medium text-gray-800">Current SPF Record:</h5>
                      <p className="text-sm text-gray-600 font-mono">{authCheckResult.existing_records.spf}</p>
                    </div>
                  )}
                </div>
              )}
              
              {authCheckResult && authCheckResult.error && (
                <div className="mt-6 bg-red-50 border border-red-200 p-4 rounded-md">
                  <p className="text-red-800">{authCheckResult.error}</p>
                </div>
              )}
            </div>
          )}

          {/* MX Lookup Tab */}
          {activeTab === 'mx' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="bg-green-100 text-green-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                  🔍
                </span>
                Test MX Records
              </h2>
              
              <form onSubmit={handleMxTest} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domain to Test
                  </label>
                  <input
                    type="text"
                    value={mxTestDomain}
                    onChange={(e) => setMxTestDomain(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                    placeholder="gmail.com"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 px-4 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  Lookup MX Records
                </button>
              </form>
              
              {/* MX Test Result */}
              {mxTestResult && (
                <div className={`mt-6 p-4 rounded-md ${
                  mxTestResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  {mxTestResult.success ? (
                    <div>
                      <p className="font-medium text-green-800 mb-2">
                        MX Records for {mxTestResult.domain}:
                      </p>
                      <div className="space-y-2">
                        {mxTestResult.mx_records.map((record, index) => (
                          <div key={index} className="bg-white p-3 rounded border">
                            <p className="text-sm">
                              <span className="font-medium">Priority:</span> {record.priority}
                            </p>
                            <p className="text-sm">
                              <span className="font-medium">Server:</span> {record.server}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-red-500 mr-3"></div>
                      <div>
                        <p className="font-medium text-red-800">Error</p>
                        <p className="text-sm text-red-600">{mxTestResult.message}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Received Emails Tab */}
          {activeTab === 'received' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <span className="bg-purple-100 text-purple-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                    📥
                  </span>
                  Received Emails ({receivedEmails.length})
                </h2>
                <button
                  onClick={loadReceivedEmails}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                >
                  Refresh
                </button>
              </div>
              
              {receivedEmails.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">No emails received yet</p>
                  <p className="text-sm text-gray-400 mt-2">
                    SMTP server is running on port 2525
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {receivedEmails.map((email, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium">From: {email.from}</p>
                          <p className="text-sm text-gray-600">To: {email.to.join(', ')}</p>
                        </div>
                        <span className="text-xs text-gray-400">
                          {new Date(email.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="font-medium mb-2">{email.headers.Subject || 'No Subject'}</p>
                      <div className="bg-gray-50 p-3 rounded text-sm">
                        {email.body || 'No content'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* DNS Setup Tab */}
          {activeTab === 'dns' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                <span className="bg-yellow-100 text-yellow-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                  ⚙️
                </span>
                DNS Configuration
              </h2>
              
              <form onSubmit={handleDnsRecordsTest} className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domain Name
                  </label>
                  <input
                    type="text"
                    value={dnsTestDomain}
                    onChange={(e) => setDnsTestDomain(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    placeholder="yourdomain.com"
                  />
                </div>
                
                <button
                  type="submit"
                  className="w-full py-3 px-4 bg-yellow-600 text-white rounded-md font-medium hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                >
                  Generate DNS Records
                </button>
              </form>
              
              {dnsRecords && !dnsRecords.error && (
                <div className="space-y-6">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h3 className="font-bold text-blue-800 mb-2">SPF Record</h3>
                    <p className="text-sm text-blue-600 mb-2">Add this TXT record to authorize email sending:</p>
                    <div className="bg-white p-3 rounded border font-mono text-sm break-all">
                      <strong>Name:</strong> {dnsRecords.records.spf.name}<br/>
                      <strong>Type:</strong> {dnsRecords.records.spf.type}<br/>
                      <strong>Value:</strong> {dnsRecords.records.spf.value}
                    </div>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg">
                    <h3 className="font-bold text-green-800 mb-2">DKIM Record</h3>
                    <p className="text-sm text-green-600 mb-2">Add this TXT record for DKIM signing:</p>
                    <div className="bg-white p-3 rounded border font-mono text-sm break-all">
                      <strong>Name:</strong> {dnsRecords.records.dkim.name}<br/>
                      <strong>Type:</strong> {dnsRecords.records.dkim.type}<br/>
                      <strong>Value:</strong> {dnsRecords.records.dkim.value}
                    </div>
                  </div>
                  
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <h3 className="font-bold text-purple-800 mb-2">DMARC Record</h3>
                    <p className="text-sm text-purple-600 mb-2">Add this TXT record for DMARC policy:</p>
                    <div className="bg-white p-3 rounded border font-mono text-sm break-all">
                      <strong>Name:</strong> {dnsRecords.records.dmarc.name}<br/>
                      <strong>Type:</strong> {dnsRecords.records.dmarc.type}<br/>
                      <strong>Value:</strong> {dnsRecords.records.dmarc.value}
                    </div>
                  </div>
                </div>
              )}
              
              {dnsRecords && dnsRecords.error && (
                <div className="bg-red-50 border border-red-200 p-4 rounded-md">
                  <p className="text-red-800">{dnsRecords.error}</p>
                </div>
              )}
            </div>
          )}

          {/* Server Status Tab */}
          {activeTab === 'status' && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <span className="bg-indigo-100 text-indigo-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                    📊
                  </span>
                  Server Status
                </h2>
                <button
                  onClick={loadServerStatus}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                >
                  Refresh
                </button>
              </div>
              
              {serverStatus && (
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-bold text-gray-800 mb-3">SMTP Server</h3>
                    <div className="space-y-2">
                      <p className="text-sm">
                        <span className="font-medium">Status:</span> 
                        <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                          serverStatus.running ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {serverStatus.running ? 'Running' : 'Stopped'}
                        </span>
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Host:</span> {serverStatus.host}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Port:</span> {serverStatus.port}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Total Emails:</span> {serverStatus.total_emails}
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-bold text-gray-800 mb-3">User Mailboxes</h3>
                    <div className="space-y-2">
                      <p className="text-sm">
                        <span className="font-medium">Active Users:</span> {serverStatus.user_count}
                      </p>
                      {serverStatus.users && serverStatus.users.length > 0 && (
                        <div>
                          <p className="text-sm font-medium mb-1">Users:</p>
                          {serverStatus.users.map((user, index) => (
                            <p key={index} className="text-xs text-gray-600 ml-2">
                              {user}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Technical Features */}
        <div className="mt-12 bg-white rounded-lg shadow-lg p-8 max-w-6xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            🚀 Complete Email Service Features
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔌</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">Raw Socket SMTP</h4>
              <p className="text-sm text-gray-600">
                Direct TCP communication with mail servers using manual SMTP protocol
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔐</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">DKIM Authentication</h4>
              <p className="text-sm text-gray-600">
                Digital signatures for email authentication and anti-spam
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📨</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">SMTP Server</h4>
              <p className="text-sm text-gray-600">
                Receive incoming emails from other mail servers
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-yellow-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🌐</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">DNS Integration</h4>
              <p className="text-sm text-gray-600">
                MX record lookup and DNS configuration management
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;