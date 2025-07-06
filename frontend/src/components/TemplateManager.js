import React, { useState, useEffect } from 'react';

const TemplateManager = ({ backendUrl }) => {
  const [view, setView] = useState('list'); // list, create, edit, preview
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    html_content: '',
    text_content: '',
    category: 'general'
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/templates`);
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTemplate = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Template created successfully!');
        setView('list');
        loadTemplates();
        resetForm();
      } else {
        alert(`Error: ${result.message || 'Failed to create template'}`);
      }
    } catch (error) {
      alert(`Error creating template: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const previewTemplate = async (templateId) => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/templates/${templateId}/preview`, {
        method: 'POST'
      });
      
      const result = await response.json();
      setPreview(result);
      setView('preview');
    } catch (error) {
      alert(`Error previewing template: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      subject: '',
      html_content: '',
      text_content: '',
      category: 'general'
    });
  };

  const templateCategories = [
    { value: 'general', label: 'General' },
    { value: 'sales', label: 'Sales Outreach' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'followup', label: 'Follow-up' },
    { value: 'newsletter', label: 'Newsletter' }
  ];

  const sampleTemplates = [
    {
      name: 'Cold Outreach - Introduction',
      subject: 'Quick question about {{company}}',
      content: `Hi {{first_name}},

I hope this email finds you well. I came across {{company}} and was impressed by [specific detail about their company].

I'm reaching out because we help companies like yours [brief value proposition]. I'd love to share how we've helped similar companies [specific benefit].

Would you be open to a brief 15-minute call this week to discuss how this might benefit {{company}}?

Best regards,
{{from_name}}

P.S. If you'd prefer not to receive emails like this, you can unsubscribe here: [unsubscribe_link]`
    },
    {
      name: 'Follow-up - Second Touch',
      subject: 'Following up on my previous email',
      content: `Hi {{first_name}},

I wanted to follow up on my email from last week regarding [brief description of offer].

I understand you're probably busy, but I believe this could be valuable for {{company}} because [specific reason].

If you're interested, I'd be happy to send over a brief case study showing how we helped [similar company] achieve [specific result].

Would that be helpful?

Best regards,
{{from_name}}`
    }
  ];

  if (view === 'preview' && preview) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Template Preview</h1>
            <p className="text-gray-600">See how your template looks with sample data</p>
          </div>
          <button
            onClick={() => setView('list')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Back to templates
          </button>
        </div>

        {/* Preview */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6">
            <div className="space-y-6">
              {/* Subject Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Line
                </label>
                <div className="bg-gray-50 p-3 rounded-lg border">
                  <p className="font-medium">{preview.subject}</p>
                </div>
              </div>

              {/* Content Preview */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Content
                </label>
                <div className="bg-gray-50 p-6 rounded-lg border max-h-96 overflow-y-auto">
                  <div dangerouslySetInnerHTML={{ __html: preview.html_content.replace(/\n/g, '<br>') }} />
                </div>
              </div>

              {/* Variables Used */}
              {preview.variables && preview.variables.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Variables Used
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {preview.variables.map((variable, index) => (
                      <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {`{{${variable}}}`}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Data Note */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-800 mb-1">📋 Sample Data Used</h4>
                <p className="text-sm text-yellow-600">
                  This preview uses sample data: John Doe from Example Corp (john.doe@example.com)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'create' || view === 'edit') {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {view === 'create' ? 'Create Template' : 'Edit Template'}
            </h1>
            <p className="text-gray-600">Design reusable email templates for your campaigns</p>
          </div>
          <button
            onClick={() => setView('list')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Back to templates
          </button>
        </div>

        {/* Template Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6">
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Template Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter template name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {templateCategories.map(cat => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Subject Line */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Line
                </label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => setFormData({...formData, subject: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter email subject"
                />
              </div>

              {/* Personalization Variables */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-2">📝 Personalization Variables</h4>
                <p className="text-sm text-blue-600 mb-3">
                  Use these variables in your subject and content to personalize emails:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                  <code className="bg-white px-2 py-1 rounded">{'{{first_name}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{last_name}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{full_name}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{email}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{company}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{phone}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{current_date}}'}</code>
                  <code className="bg-white px-2 py-1 rounded">{'{{from_name}}'}</code>
                </div>
              </div>

              {/* Email Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Content
                </label>
                <textarea
                  value={formData.html_content}
                  onChange={(e) => setFormData({...formData, html_content: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="15"
                  placeholder="Enter your email content here..."
                />
              </div>

              {/* Sample Templates */}
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">📋 Sample Templates</h3>
                <div className="space-y-3">
                  {sampleTemplates.map((template, index) => (
                    <div key={index} className="border border-gray-200 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-800">{template.name}</h4>
                        <button
                          onClick={() => setFormData({
                            ...formData,
                            name: template.name,
                            subject: template.subject,
                            html_content: template.content
                          })}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          Use Template
                        </button>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        <strong>Subject:</strong> {template.subject}
                      </p>
                      <p className="text-xs text-gray-500">
                        {template.content.substring(0, 150)}...
                      </p>
                    </div>
                  ))}
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
                  onClick={createTemplate}
                  disabled={loading || !formData.name || !formData.subject || !formData.html_content}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Creating...' : 'Create Template'}
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
          <h1 className="text-2xl font-bold text-gray-900">Email Templates</h1>
          <p className="text-gray-600">Create and manage reusable email templates</p>
        </div>
        <button
          onClick={() => setView('create')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Create Template
        </button>
      </div>

      {/* Template Categories */}
      <div className="flex space-x-2 overflow-x-auto">
        {templateCategories.map(category => (
          <button
            key={category.value}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors whitespace-nowrap"
          >
            {category.label}
          </button>
        ))}
      </div>

      {/* Template Grid */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : templates.length === 0 ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-gray-400 text-2xl">📝</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No templates yet</h3>
            <p className="text-gray-500 mb-4">Create your first email template to get started</p>
            <button
              onClick={() => setView('create')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Template
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
            {templates.map((template) => (
              <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 mb-1">{template.name}</h3>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {template.category}
                    </span>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => previewTemplate(template.id)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Preview"
                    >
                      👁️
                    </button>
                    <button
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="Edit"
                    >
                      ✏️
                    </button>
                  </div>
                </div>
                
                <div className="mb-3">
                  <p className="text-sm font-medium text-gray-700 mb-1">Subject:</p>
                  <p className="text-sm text-gray-600">{template.subject}</p>
                </div>
                
                <div className="mb-4">
                  <p className="text-xs text-gray-500 line-clamp-3">
                    {template.html_content.substring(0, 120)}...
                  </p>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">
                    {new Date(template.created_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => previewTemplate(template.id)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Preview →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TemplateManager;