import React, { useState, useEffect } from 'react';
import { Search, ShoppingCart, CreditCard, Check, X, Star, TrendingUp, Globe, Clock, Shield, Zap } from 'lucide-react';

const DomainRegistration = ({ backendUrl }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cart, setCart] = useState([]);
  const [showRegistration, setShowRegistration] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [popularTlds, setPopularTlds] = useState([]);
  const [registrantInfo, setRegistrantInfo] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    organization: '',
    privacy_protection: true
  });

  useEffect(() => {
    fetchPopularTlds();
  }, []);

  const fetchPopularTlds = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/domains/pricing/tlds`);
      const data = await response.json();
      setPopularTlds(data.tlds.filter(tld => tld.popular));
    } catch (error) {
      console.error('Error fetching popular TLDs:', error);
    }
  };

  const searchDomains = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/search?query=${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error('Error searching domains:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (domain) => {
    if (!cart.find(item => item.domain === domain.domain)) {
      setCart([...cart, { ...domain, years: 1 }]);
    }
  };

  const removeFromCart = (domain) => {
    setCart(cart.filter(item => item.domain !== domain));
  };

  const getTotalCost = () => {
    return cart.reduce((total, item) => total + (item.price * item.years), 0);
  };

  const handleRegistration = async (domain) => {
    setSelectedDomain(domain);
    setShowRegistration(true);
  };

  const processRegistration = async () => {
    if (!selectedDomain) return;

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/domains/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: selectedDomain.domain,
          years: selectedDomain.years || 1,
          registrant_info: registrantInfo
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Process payment
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
          alert(`Domain ${selectedDomain.domain} registered successfully!`);
          setShowRegistration(false);
          setSelectedDomain(null);
          removeFromCart(selectedDomain.domain);
        } else {
          alert('Payment failed. Please try again.');
        }
      } else {
        alert(`Registration failed: ${data.detail}`);
      }
    } catch (error) {
      console.error('Error registering domain:', error);
      alert('Registration failed. Please try again.');
    }
  };

  const handleInputChange = (field, value) => {
    setRegistrantInfo(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const suggestDomains = (baseName) => {
    const suggestions = [
      `${baseName}app`,
      `${baseName}hub`,
      `${baseName}pro`,
      `${baseName}store`,
      `${baseName}online`,
      `get${baseName}`,
      `my${baseName}`,
      `${baseName}now`
    ];
    return suggestions.slice(0, 4);
  };

  return (
    <div className="max-w-7xl mx-auto p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          <Globe className="inline-block mr-3 text-blue-600" />
          Domain Registration
        </h1>
        <p className="text-xl text-gray-600">Find the perfect domain for your business</p>
      </div>

      {/* Search Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex items-center space-x-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter domain name (e.g., myawesome)"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && searchDomains()}
            />
          </div>
          <button
            onClick={searchDomains}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            ) : (
              <Search size={20} />
            )}
            <span>Search</span>
          </button>
        </div>

        {/* Popular TLDs */}
        {popularTlds.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3 flex items-center">
              <Star className="mr-2 text-yellow-500" size={20} />
              Popular Extensions
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {popularTlds.map(tld => (
                <div key={tld.tld} className="bg-gray-50 p-3 rounded-lg text-center">
                  <div className="font-semibold text-gray-900">{tld.tld}</div>
                  <div className="text-sm text-gray-600">${tld.price}/year</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <TrendingUp className="mr-2 text-green-500" />
            Search Results
          </h2>
          
          <div className="space-y-3">
            {searchResults.map(result => (
              <div key={result.domain} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-lg font-semibold text-gray-900">
                      {result.domain}
                    </div>
                    <div className="flex items-center space-x-2">
                      {result.available ? (
                        <Check className="text-green-500" size={16} />
                      ) : (
                        <X className="text-red-500" size={16} />
                      )}
                      <span className={`text-sm ${result.available ? 'text-green-600' : 'text-red-600'}`}>
                        {result.available ? 'Available' : 'Unavailable'}
                      </span>
                      {result.popular && (
                        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                          Popular
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-lg font-bold text-gray-900">
                        ${result.price}/year
                      </div>
                      <div className="text-sm text-gray-500">
                        Renews at ${result.renewal_price}/year
                      </div>
                    </div>
                    
                    {result.available && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => addToCart(result)}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                        >
                          <ShoppingCart size={16} />
                          <span>Add to Cart</span>
                        </button>
                        <button
                          onClick={() => handleRegistration(result)}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                        >
                          Register Now
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Domain Suggestions */}
          {searchQuery && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold mb-3">Alternative Suggestions:</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {suggestDomains(searchQuery).map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => setSearchQuery(suggestion)}
                    className="text-blue-600 hover:text-blue-800 text-sm p-2 rounded hover:bg-blue-100"
                  >
                    {suggestion}.com
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Shopping Cart */}
      {cart.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <ShoppingCart className="mr-2 text-blue-600" />
            Shopping Cart ({cart.length})
          </h2>
          
          <div className="space-y-3">
            {cart.map(item => (
              <div key={item.domain} className="flex items-center justify-between border-b pb-3">
                <div>
                  <div className="font-semibold">{item.domain}</div>
                  <div className="text-sm text-gray-600">{item.years} year(s)</div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-lg font-bold">${(item.price * item.years).toFixed(2)}</div>
                  <button
                    onClick={() => removeFromCart(item.domain)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X size={20} />
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 flex justify-between items-center">
            <div className="text-2xl font-bold">
              Total: ${getTotalCost().toFixed(2)}
            </div>
            <button
              onClick={() => setShowRegistration(true)}
              className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 flex items-center space-x-2"
            >
              <CreditCard size={20} />
              <span>Proceed to Checkout</span>
            </button>
          </div>
        </div>
      )}

      {/* Registration Modal */}
      {showRegistration && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Domain Registration</h2>
              <button
                onClick={() => setShowRegistration(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={24} />
              </button>
            </div>

            {selectedDomain && (
              <div className="bg-blue-50 p-4 rounded-lg mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-lg">{selectedDomain.domain}</div>
                    <div className="text-sm text-gray-600">1 year registration</div>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    ${selectedDomain.price}
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={(e) => { e.preventDefault(); processRegistration(); }}>
              <div className="grid grid-cols-2 gap-4 mb-6">
                <input
                  type="text"
                  placeholder="First Name"
                  value={registrantInfo.first_name}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  value={registrantInfo.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <input
                  type="email"
                  placeholder="Email"
                  value={registrantInfo.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="tel"
                  placeholder="Phone"
                  value={registrantInfo.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <input
                type="text"
                placeholder="Address"
                value={registrantInfo.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                required
              />

              <div className="grid grid-cols-3 gap-4 mb-6">
                <input
                  type="text"
                  placeholder="City"
                  value={registrantInfo.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  placeholder="State"
                  value={registrantInfo.state}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
                <input
                  type="text"
                  placeholder="Postal Code"
                  value={registrantInfo.postal_code}
                  onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <input
                type="text"
                placeholder="Country"
                value={registrantInfo.country}
                onChange={(e) => handleInputChange('country', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
                required
              />

              <input
                type="text"
                placeholder="Organization (Optional)"
                value={registrantInfo.organization}
                onChange={(e) => handleInputChange('organization', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
              />

              <label className="flex items-center space-x-2 mb-6">
                <input
                  type="checkbox"
                  checked={registrantInfo.privacy_protection}
                  onChange={(e) => handleInputChange('privacy_protection', e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-700 flex items-center">
                  <Shield className="mr-1" size={16} />
                  Enable privacy protection (Recommended)
                </span>
              </label>

              <div className="flex space-x-4">
                <button
                  type="button"
                  onClick={() => setShowRegistration(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 flex items-center justify-center space-x-2"
                >
                  <CreditCard size={20} />
                  <span>Register Domain</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Features Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-6 text-center">Why Choose Our Domain Registration?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <Zap className="mx-auto mb-3 text-blue-600" size={48} />
            <h3 className="font-semibold mb-2">Instant Registration</h3>
            <p className="text-gray-600">Get your domain registered and active within minutes</p>
          </div>
          <div className="text-center">
            <Shield className="mx-auto mb-3 text-green-600" size={48} />
            <h3 className="font-semibold mb-2">Privacy Protection</h3>
            <p className="text-gray-600">Keep your personal information private and secure</p>
          </div>
          <div className="text-center">
            <Clock className="mx-auto mb-3 text-purple-600" size={48} />
            <h3 className="font-semibold mb-2">24/7 Support</h3>
            <p className="text-gray-600">Get help whenever you need it with our support team</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainRegistration;