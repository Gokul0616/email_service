import React, { useState, useEffect } from 'react';
import { 
  Globe, Settings, Refresh, Calendar, CreditCard, Shield, 
  ExternalLink, Copy, Check, X, Edit, Trash2, Plus, Server,
  Eye, EyeOff, Lock, Unlock, AlertCircle, TrendingUp
} from 'lucide-react';

const DomainManager = () => {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [showDNSEditor, setShowDNSEditor] = useState(false);
  const [showWHOIS, setShowWHOIS] = useState(false);
  const [showTransfer, setShowTransfer] = useState(false);
  const [userEmail, setUserEmail] = useState('user@example.com');
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('registration_date');
  const [renewalYears, setRenewalYears] = useState(1);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/my-domains?user_email=${userEmail}`);
      const data = await response.json();
      setDomains(data.domains || []);
    } catch (error) {
      console.error('Error fetching domains:', error);
    } finally {
      setLoading(false);
    }
  };

  const renewDomain = async (domain, years = 1) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain}/renew`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ domain, years })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Process payment for renewal
        const paymentResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/payment/process`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            payment_id: data.payment_id,
            payment_method: 'credit_card'
          })
        });

        const paymentData = await paymentResponse.json();
        
        if (paymentData.success) {
          alert(`Domain ${domain} renewed successfully!`);
          fetchDomains();
        } else {
          alert('Renewal payment failed. Please try again.');
        }
      } else {
        alert(`Renewal failed: ${data.detail}`);
      }
    } catch (error) {
      console.error('Error renewing domain:', error);
      alert('Renewal failed. Please try again.');
    }
  };

  const toggleAutoRenew = async (domain) => {
    try {
      const domainInfo = domains.find(d => d.domain === domain);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain}/update`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain,
          auto_renew: !domainInfo.auto_renew
        })
      });

      if (response.ok) {
        fetchDomains();
      } else {
        alert('Failed to update auto-renew setting');
      }
    } catch (error) {
      console.error('Error updating auto-renew:', error);
    }
  };

  const getAuthCode = async (domain) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/auth-code/${domain}`);
      const data = await response.json();
      
      if (response.ok) {
        navigator.clipboard.writeText(data.auth_code);
        alert(`Authorization code copied to clipboard: ${data.auth_code}`);
      } else {
        alert('Failed to get authorization code');
      }
    } catch (error) {
      console.error('Error getting auth code:', error);
    }
  };

  const getDaysUntilExpiry = (expirationDate) => {
    const expiry = new Date(expirationDate);
    const today = new Date();
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'expired': return 'text-red-600 bg-red-100';
      case 'suspended': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const filteredDomains = domains.filter(domain => {
    if (filter === 'all') return true;
    if (filter === 'active') return domain.status === 'active';
    if (filter === 'expiring') return getDaysUntilExpiry(domain.expiration_date) <= 30;
    if (filter === 'expired') return domain.status === 'expired';
    return true;
  });

  const sortedDomains = filteredDomains.sort((a, b) => {
    if (sortBy === 'registration_date') {
      return new Date(b.registration_date) - new Date(a.registration_date);
    }
    if (sortBy === 'expiration_date') {
      return new Date(a.expiration_date) - new Date(b.expiration_date);
    }
    if (sortBy === 'domain') {
      return a.domain.localeCompare(b.domain);
    }
    return 0;
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Globe className="mr-3 text-blue-600" />
            Domain Manager
          </h1>
          <p className="text-gray-600">Manage your registered domains</p>
        </div>
        <button
          onClick={fetchDomains}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <Refresh size={16} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Sort Controls */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Domains</option>
              <option value="active">Active</option>
              <option value="expiring">Expiring Soon</option>
              <option value="expired">Expired</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
            >
              <option value="registration_date">Registration Date</option>
              <option value="expiration_date">Expiration Date</option>
              <option value="domain">Domain Name</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>Total: {filteredDomains.length} domains</span>
          </div>
        </div>
      </div>

      {/* Domain List */}
      <div className="space-y-4">
        {sortedDomains.map(domain => {
          const daysUntilExpiry = getDaysUntilExpiry(domain.expiration_date);
          const isExpiringSoon = daysUntilExpiry <= 30;
          
          return (
            <div key={domain.domain} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">{domain.domain}</h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(domain.status)}`}>
                      {domain.status}
                    </span>
                    {isExpiringSoon && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-600 rounded-full flex items-center">
                        <AlertCircle size={12} className="mr-1" />
                        Expiring Soon
                      </span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">Registered:</span>
                      <div>{new Date(domain.registration_date).toLocaleDateString()}</div>
                    </div>
                    <div>
                      <span className="font-medium">Expires:</span>
                      <div className={isExpiringSoon ? 'text-red-600 font-semibold' : ''}>
                        {new Date(domain.expiration_date).toLocaleDateString()}
                      </div>
                    </div>
                    <div>
                      <span className="font-medium">Auto-Renew:</span>
                      <div className="flex items-center space-x-1">
                        {domain.auto_renew ? (
                          <Check className="text-green-600" size={16} />
                        ) : (
                          <X className="text-red-600" size={16} />
                        )}
                        <span>{domain.auto_renew ? 'Enabled' : 'Disabled'}</span>
                      </div>
                    </div>
                    <div>
                      <span className="font-medium">Days until expiry:</span>
                      <div className={isExpiringSoon ? 'text-red-600 font-semibold' : ''}>
                        {daysUntilExpiry} days
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-2 mt-4 lg:mt-0">
                  <button
                    onClick={() => renewDomain(domain.domain, renewalYears)}
                    className="bg-green-600 text-white px-3 py-2 rounded-lg hover:bg-green-700 flex items-center space-x-1 text-sm"
                  >
                    <CreditCard size={14} />
                    <span>Renew</span>
                  </button>
                  
                  <button
                    onClick={() => toggleAutoRenew(domain.domain)}
                    className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-1 text-sm"
                  >
                    {domain.auto_renew ? <Unlock size={14} /> : <Lock size={14} />}
                    <span>{domain.auto_renew ? 'Disable' : 'Enable'} Auto-Renew</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      setSelectedDomain(domain);
                      setShowDNSEditor(true);
                    }}
                    className="bg-purple-600 text-white px-3 py-2 rounded-lg hover:bg-purple-700 flex items-center space-x-1 text-sm"
                  >
                    <Server size={14} />
                    <span>DNS</span>
                  </button>
                  
                  <button
                    onClick={() => {
                      setSelectedDomain(domain);
                      setShowWHOIS(true);
                    }}
                    className="bg-gray-600 text-white px-3 py-2 rounded-lg hover:bg-gray-700 flex items-center space-x-1 text-sm"
                  >
                    <Eye size={14} />
                    <span>WHOIS</span>
                  </button>
                  
                  <button
                    onClick={() => getAuthCode(domain.domain)}
                    className="bg-orange-600 text-white px-3 py-2 rounded-lg hover:bg-orange-700 flex items-center space-x-1 text-sm"
                  >
                    <Copy size={14} />
                    <span>Auth Code</span>
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredDomains.length === 0 && (
        <div className="text-center py-12">
          <Globe className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No domains found</h3>
          <p className="text-gray-600 mb-4">
            {filter === 'all' 
              ? "You haven't registered any domains yet." 
              : `No domains match the current filter: ${filter}`
            }
          </p>
          <button
            onClick={() => window.location.href = '/domain-registration'}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Register Your First Domain
          </button>
        </div>
      )}

      {/* DNS Editor Modal */}
      {showDNSEditor && selectedDomain && (
        <DNSEditor
          domain={selectedDomain}
          onClose={() => setShowDNSEditor(false)}
          onUpdate={fetchDomains}
        />
      )}

      {/* WHOIS Modal */}
      {showWHOIS && selectedDomain && (
        <WHOISViewer
          domain={selectedDomain}
          onClose={() => setShowWHOIS(false)}
        />
      )}
    </div>
  );
};

// DNS Editor Component
const DNSEditor = ({ domain, onClose, onUpdate }) => {
  const [dnsRecords, setDnsRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newRecord, setNewRecord] = useState({
    name: '',
    type: 'A',
    value: '',
    ttl: 3600
  });

  useEffect(() => {
    fetchDNSRecords();
  }, []);

  const fetchDNSRecords = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain.domain}/dns`);
      const data = await response.json();
      setDnsRecords(data.records || []);
    } catch (error) {
      console.error('Error fetching DNS records:', error);
    } finally {
      setLoading(false);
    }
  };

  const addDNSRecord = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain.domain}/dns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: domain.domain,
          record: newRecord
        })
      });

      if (response.ok) {
        fetchDNSRecords();
        setNewRecord({ name: '', type: 'A', value: '', ttl: 3600 });
      } else {
        alert('Failed to add DNS record');
      }
    } catch (error) {
      console.error('Error adding DNS record:', error);
    }
  };

  const deleteDNSRecord = async (recordId) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain.domain}/dns/${recordId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchDNSRecords();
      } else {
        alert('Failed to delete DNS record');
      }
    } catch (error) {
      console.error('Error deleting DNS record:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">DNS Records - {domain.domain}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {/* Add New Record */}
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h3 className="font-semibold mb-4">Add New DNS Record</h3>
          <div className="grid grid-cols-4 gap-4">
            <input
              type="text"
              placeholder="Name"
              value={newRecord.name}
              onChange={(e) => setNewRecord({...newRecord, name: e.target.value})}
              className="p-2 border rounded-lg"
            />
            <select
              value={newRecord.type}
              onChange={(e) => setNewRecord({...newRecord, type: e.target.value})}
              className="p-2 border rounded-lg"
            >
              <option value="A">A</option>
              <option value="AAAA">AAAA</option>
              <option value="CNAME">CNAME</option>
              <option value="MX">MX</option>
              <option value="TXT">TXT</option>
              <option value="NS">NS</option>
            </select>
            <input
              type="text"
              placeholder="Value"
              value={newRecord.value}
              onChange={(e) => setNewRecord({...newRecord, value: e.target.value})}
              className="p-2 border rounded-lg"
            />
            <div className="flex space-x-2">
              <input
                type="number"
                placeholder="TTL"
                value={newRecord.ttl}
                onChange={(e) => setNewRecord({...newRecord, ttl: parseInt(e.target.value)})}
                className="p-2 border rounded-lg flex-1"
              />
              <button
                onClick={addDNSRecord}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                <Plus size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* DNS Records Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-3 text-left">Name</th>
                <th className="border border-gray-300 p-3 text-left">Type</th>
                <th className="border border-gray-300 p-3 text-left">Value</th>
                <th className="border border-gray-300 p-3 text-left">TTL</th>
                <th className="border border-gray-300 p-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {dnsRecords.map(record => (
                <tr key={record.record_id}>
                  <td className="border border-gray-300 p-3">{record.name}</td>
                  <td className="border border-gray-300 p-3">{record.type}</td>
                  <td className="border border-gray-300 p-3">{record.value}</td>
                  <td className="border border-gray-300 p-3">{record.ttl}</td>
                  <td className="border border-gray-300 p-3">
                    <button
                      onClick={() => deleteDNSRecord(record.record_id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// WHOIS Viewer Component
const WHOISViewer = ({ domain, onClose }) => {
  const [whoisData, setWhoisData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWHOISData();
  }, []);

  const fetchWHOISData = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/${domain.domain}/whois`);
      const data = await response.json();
      setWhoisData(data);
    } catch (error) {
      console.error('Error fetching WHOIS data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">WHOIS Information - {domain.domain}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : whoisData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="font-semibold mb-2">Domain Info</h3>
                <div className="text-sm space-y-1">
                  <div><strong>Domain:</strong> {whoisData.domain}</div>
                  <div><strong>Registrar:</strong> {whoisData.registrar}</div>
                  <div><strong>Created:</strong> {new Date(whoisData.creation_date).toLocaleDateString()}</div>
                  <div><strong>Expires:</strong> {new Date(whoisData.expiration_date).toLocaleDateString()}</div>
                  <div><strong>Updated:</strong> {new Date(whoisData.updated_date).toLocaleDateString()}</div>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Status</h3>
                <div className="text-sm space-y-1">
                  {whoisData.status?.map((status, index) => (
                    <div key={index} className="bg-gray-100 p-1 rounded">{status}</div>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Registrant Information</h3>
              {whoisData.privacy_protection ? (
                <div className="text-sm text-gray-600 flex items-center">
                  <Shield className="mr-2" size={16} />
                  Privacy protection enabled
                </div>
              ) : (
                <div className="text-sm space-y-1">
                  <div><strong>Name:</strong> {whoisData.registrant?.first_name} {whoisData.registrant?.last_name}</div>
                  <div><strong>Email:</strong> {whoisData.registrant?.email}</div>
                  <div><strong>Phone:</strong> {whoisData.registrant?.phone}</div>
                  <div><strong>Address:</strong> {whoisData.registrant?.address}</div>
                </div>
              )}
            </div>

            <div>
              <h3 className="font-semibold mb-2">Name Servers</h3>
              <div className="text-sm space-y-1">
                {whoisData.name_servers?.map((ns, index) => (
                  <div key={index}>{ns}</div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            WHOIS information not available
          </div>
        )}
      </div>
    </div>
  );
};

export default DomainManager;