import React, { useState } from 'react';
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
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

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
          success: true,
          message: data.message,
          messageId: data.message_id
        });
        
        // Clear form on success
        setFormData({
          to_email: '',
          from_email: '',
          from_name: '',
          subject: '',
          body: '',
          is_html: false
        });
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            📧 Custom Email Server
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Send emails using our custom-built SMTP client with raw socket implementation.
            No external email services - direct communication with Gmail, Yahoo, and other providers.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Email Sending Form */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <span className="bg-blue-100 text-blue-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                1
              </span>
              Send Email
            </h2>
            
            <form onSubmit={handleSendEmail} className="space-y-4">
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
                  rows="5"
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
                    Sending Email...
                  </div>
                ) : (
                  'Send Email'
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

          {/* MX Record Testing */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
              <span className="bg-green-100 text-green-600 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                2
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
        </div>

        {/* Technical Details */}
        <div className="mt-12 bg-white rounded-lg shadow-lg p-8 max-w-4xl mx-auto">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">
            🔧 Technical Implementation
          </h3>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔌</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">Raw Socket SMTP</h4>
              <p className="text-sm text-gray-600">
                Direct TCP socket communication with mail servers using manual SMTP protocol implementation
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🌐</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">DNS MX Lookup</h4>
              <p className="text-sm text-gray-600">
                Custom DNS resolver that queries MX records using raw DNS protocol packets
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔐</span>
              </div>
              <h4 className="font-bold text-gray-900 mb-2">STARTTLS Support</h4>
              <p className="text-sm text-gray-600">
                Automatic TLS encryption when supported by destination mail servers
              </p>
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-bold text-gray-900 mb-2">Protocol Flow:</h4>
            <ol className="text-sm text-gray-600 space-y-1">
              <li>1. DNS MX record lookup for recipient domain</li>
              <li>2. TCP connection to highest priority MX server</li>
              <li>3. SMTP handshake (EHLO/HELO)</li>
              <li>4. STARTTLS negotiation if supported</li>
              <li>5. MAIL FROM and RCPT TO commands</li>
              <li>6. DATA command and message transmission</li>
              <li>7. QUIT and connection cleanup</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;